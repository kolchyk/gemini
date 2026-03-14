import base64
import concurrent.futures
import io
import logging
from dataclasses import dataclass

from backend.config import prompts, settings
from backend.services.error_utils import format_error_with_retry
from backend.services.image_service import ImageService

logger = logging.getLogger(__name__)

ALLOWED_ASPECT_RATIOS = (
    "1:1",
    "16:9",
    "9:16",
    "4:3",
    "3:4",
    "2:3",
    "3:2",
    "4:5",
    "5:4",
    "21:9",
    "1:4",
    "4:1",
    "1:8",
    "8:1",
)
ALLOWED_MODEL_MODES = ("Flash", "Pro", "Both")
ALLOWED_RESOLUTIONS = ("1K", "2K")
PROMPT_MAP = {
    "custom": prompts.PROMPT_CUSTOM,
    "women": prompts.PROMPT_WOMEN,
    "men": prompts.PROMPT_MEN,
    "darnytsia": prompts.PROMPT_DARNYTSIA,
}


class GenerationExecutionError(RuntimeError):
    """Wrap generation failures so routes can expose user-facing details."""


@dataclass(frozen=True)
class ReferenceImage:
    """Keep uploaded image data alive after the request finishes."""

    filename: str
    content: bytes


@dataclass(frozen=True)
class GenerationRequest:
    """Describe one image generation job independent from HTTP details."""

    prompt: str
    model_mode: str
    aspect_ratio: str
    resolution: str
    temperature: float
    prompt_type: str
    reference_images: tuple[ReferenceImage, ...]


def build_final_prompt(prompt: str, prompt_type: str) -> str:
    """Fill in server-side defaults when a prompt template is selected."""
    stripped_prompt = prompt.strip()

    if prompt_type == "darnytsia":
        if not stripped_prompt:
            return ""
        if "Darnytsia Presentation Expert" in stripped_prompt:
            return stripped_prompt
        return prompts.PROMPT_DARNYTSIA.replace("{{user_input}}", stripped_prompt)

    if stripped_prompt:
        return stripped_prompt

    if prompt_type in ("women", "men"):
        return PROMPT_MAP[prompt_type]

    return ""


def validate_generation_request(
    *,
    prompt: str,
    model_mode: str,
    aspect_ratio: str,
    resolution: str,
    temperature: float,
    prompt_type: str,
    reference_images: tuple[ReferenceImage, ...],
) -> GenerationRequest:
    """Normalize request data so the same payload can be reused by jobs and routes."""
    final_prompt = build_final_prompt(prompt, prompt_type)
    if not final_prompt:
        raise ValueError("Prompt is required.")

    if aspect_ratio not in ALLOWED_ASPECT_RATIOS:
        raise ValueError(f"Invalid aspect ratio: {aspect_ratio}")

    if model_mode not in ALLOWED_MODEL_MODES:
        raise ValueError(f"Invalid model mode: {model_mode}")

    if resolution not in ALLOWED_RESOLUTIONS:
        raise ValueError(f"Invalid resolution: {resolution}")

    return GenerationRequest(
        prompt=final_prompt,
        model_mode=model_mode,
        aspect_ratio=aspect_ratio,
        resolution=resolution,
        temperature=temperature,
        prompt_type=prompt_type,
        reference_images=reference_images,
    )


def execute_generation(request: GenerationRequest) -> dict[str, object]:
    """Run the full multi-model generation flow and return frontend-ready payload."""
    file_objects = _build_file_objects(request.reference_images)

    flash_model = settings.GEMINI_IMAGE_MODELS[0]
    pro_model = settings.GEMINI_IMAGE_MODELS[1]

    if request.model_mode == "Flash":
        target_models = [flash_model]
    elif request.model_mode == "Pro":
        target_models = [pro_model]
    else:
        target_models = [flash_model, pro_model]

    image_service = ImageService()
    thinking_level = settings.IMAGE_DEFAULT_THINKING_LEVEL

    def generate_with_model(model_name: str) -> tuple[str, dict[str, object]]:
        model_thinking = thinking_level if "flash" in model_name.lower() else None
        for file_obj in file_objects:
            file_obj.seek(0)
        return model_name, image_service.generate_image(
            prompt=request.prompt,
            aspect_ratio=request.aspect_ratio,
            person_images=file_objects if file_objects else None,
            resolution=request.resolution,
            temperature=request.temperature,
            model=model_name,
            thinking_level=model_thinking,
        )

    try:
        results: dict[str, dict[str, object]] = {}
        errors: dict[str, str] = {}
        fallback_used = False

        with concurrent.futures.ThreadPoolExecutor(max_workers=len(target_models)) as executor:
            future_to_model = {executor.submit(generate_with_model, model): model for model in target_models}
            for future in concurrent.futures.as_completed(future_to_model):
                model = future_to_model[future]
                try:
                    model_name, result = future.result()
                    results[model_name] = result
                except Exception as error:
                    logger.warning("Model %s failed: %s", model, error)
                    errors[model] = format_error_with_retry(error, "генерацію зображення")

        if request.model_mode != "Both" and not results and errors:
            fallback_model = pro_model if target_models[0] == flash_model else flash_model
            logger.info("Fallback: trying %s after %s failed", fallback_model, target_models[0])
            try:
                fallback_name, fallback_result = generate_with_model(fallback_model)
                results[fallback_name] = fallback_result
                fallback_used = True
            except Exception as error:
                logger.error("Fallback model %s also failed: %s", fallback_model, error)
                errors[fallback_model] = format_error_with_retry(error, "генерацію зображення")

        if not results:
            all_errors = "; ".join(errors.values())
            raise GenerationExecutionError(all_errors)

        response_results = {}
        for model_name, result in results.items():
            response_results[model_name] = {
                "image_base64": base64.b64encode(result["image_bytes"]).decode()
                if result.get("image_bytes")
                else None,
                "text_output": result.get("text_output", ""),
                "error": None,
            }

        for model_name, error_message in errors.items():
            if model_name not in response_results:
                response_results[model_name] = {
                    "image_base64": None,
                    "text_output": "",
                    "error": error_message,
                }

        return {"results": response_results, "fallback_used": fallback_used}
    except GenerationExecutionError:
        raise
    except Exception as error:
        logger.error("Generation failed: %s", error, exc_info=True)
        error_message = format_error_with_retry(error, "генерацію зображення")
        raise GenerationExecutionError(error_message) from error


def _build_file_objects(reference_images: tuple[ReferenceImage, ...]) -> list[io.BytesIO]:
    """Convert persisted upload bytes back into file-like objects for Gemini."""
    file_objects: list[io.BytesIO] = []
    for image in reference_images:
        file_obj = io.BytesIO(image.content)
        file_obj.name = image.filename or "image.jpg"
        file_objects.append(file_obj)
    return file_objects

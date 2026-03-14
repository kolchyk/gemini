import io
import base64
import logging
import concurrent.futures
from fastapi import APIRouter, UploadFile, File, Form, HTTPException
from backend.services.image_service import ImageService
from backend.services.error_utils import format_error_with_retry
from backend.config import settings, prompts

logger = logging.getLogger(__name__)

router = APIRouter()

PROMPT_MAP = {
    "custom": prompts.PROMPT_CUSTOM,
    "women": prompts.PROMPT_WOMEN,
    "men": prompts.PROMPT_MEN,
    "darnytsia": prompts.PROMPT_DARNYTSIA,
}


def _build_final_prompt(prompt: str, prompt_type: str) -> str:
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


@router.get("/prompts")
async def get_prompts():
    return {
        "custom": prompts.PROMPT_CUSTOM,
        "women": prompts.PROMPT_WOMEN,
        "men": prompts.PROMPT_MEN,
        "darnytsia": prompts.PROMPT_DARNYTSIA,
    }


@router.post("/generate")
async def generate_image(
    prompt: str = Form(""),
    model_mode: str = Form("Pro"),
    aspect_ratio: str = Form("1:1"),
    temperature: float = Form(1.0),
    prompt_type: str = Form("custom"),
    reference_images: list[UploadFile] = File(default=[]),
):
    final_prompt = _build_final_prompt(prompt, prompt_type)
    if not final_prompt:
        raise HTTPException(status_code=400, detail="Prompt is required.")

    if aspect_ratio not in ("1:1", "16:9", "9:16", "4:3", "3:4", "2:3", "3:2", "4:5", "5:4", "21:9", "1:4", "4:1", "1:8", "8:1"):
        raise HTTPException(status_code=400, detail=f"Invalid aspect ratio: {aspect_ratio}")

    if model_mode not in ("Flash", "Pro", "Both"):
        raise HTTPException(status_code=400, detail=f"Invalid model mode: {model_mode}")

    # Prepare uploaded files as BytesIO with .name attribute
    file_objects = []
    for upload_file in reference_images:
        content = await upload_file.read()
        if content:
            file_obj = io.BytesIO(content)
            file_obj.name = upload_file.filename or "image.jpg"
            file_objects.append(file_obj)

    # Determine target models
    flash_model = settings.GEMINI_IMAGE_MODELS[0]
    pro_model = settings.GEMINI_IMAGE_MODELS[1]

    if model_mode == "Flash":
        target_models = [flash_model]
    elif model_mode == "Pro":
        target_models = [pro_model]
    else:
        target_models = [flash_model, pro_model]

    image_service = ImageService()

    resolution = settings.IMAGE_DEFAULT_RESOLUTION
    thinking_level = settings.IMAGE_DEFAULT_THINKING_LEVEL

    def generate_with_model(model_name):
        model_thinking = thinking_level if "flash" in model_name.lower() else None
        # Reset file positions for each model
        for f in file_objects:
            f.seek(0)
        return model_name, image_service.generate_image(
            prompt=final_prompt,
            aspect_ratio=aspect_ratio,
            person_images=file_objects if file_objects else None,
            resolution=resolution,
            temperature=temperature,
            model=model_name,
            thinking_level=model_thinking,
        )

    try:
        results = {}
        errors = {}
        fallback_used = False

        with concurrent.futures.ThreadPoolExecutor(max_workers=len(target_models)) as executor:
            future_to_model = {executor.submit(generate_with_model, m): m for m in target_models}
            for future in concurrent.futures.as_completed(future_to_model):
                model = future_to_model[future]
                try:
                    model_name, result = future.result()
                    results[model_name] = result
                except Exception as e:
                    logger.warning(f"Model {model} failed: {e}")
                    errors[model] = format_error_with_retry(e, "генерацію зображення")

        # Single-model mode: if the selected model failed, try the fallback
        if model_mode != "Both" and not results and errors:
            fallback_model = pro_model if target_models[0] == flash_model else flash_model
            logger.info(f"Fallback: trying {fallback_model} after {target_models[0]} failed")
            try:
                fallback_name, fallback_result = generate_with_model(fallback_model)
                results[fallback_name] = fallback_result
                fallback_used = True
            except Exception as e:
                logger.error(f"Fallback model {fallback_model} also failed: {e}")
                errors[fallback_model] = format_error_with_retry(e, "генерацію зображення")

        # If all models failed, return error
        if not results:
            all_errors = "; ".join(errors.values())
            raise HTTPException(status_code=500, detail=all_errors)

        # Convert image bytes to base64 for JSON response
        response_results = {}
        for model_name, result in results.items():
            response_results[model_name] = {
                "image_base64": base64.b64encode(result["image_bytes"]).decode() if result.get("image_bytes") else None,
                "text_output": result.get("text_output", ""),
                "error": None,
            }
        # Include failed models in response
        for model_name, error_msg in errors.items():
            if model_name not in response_results:
                response_results[model_name] = {
                    "image_base64": None,
                    "text_output": "",
                    "error": error_msg,
                }

        return {"results": response_results, "fallback_used": fallback_used}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Generation failed: {e}", exc_info=True)
        error_msg = format_error_with_retry(e, "генерацію зображення")
        raise HTTPException(status_code=500, detail=error_msg)

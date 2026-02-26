import base64
import logging
import mimetypes
from google.genai import types
from services.gemini_client import get_gemini_client
from services.telegram_service import telegram_service
from services.mime_utils import guess_mime_type
from config import settings
from gemini_image_generator.file_utils import save_uploaded_file

logger = logging.getLogger(__name__)


class ImageService:
    def __init__(self):
        self.client = get_gemini_client()

    def generate_image(
        self,
        prompt,
        aspect_ratio="1:1",
        person_images=None,
        resolution="1K",
        temperature=1.0,
        model=None,
        thinking_level="HIGH",
    ):
        """
        Generates an image based on a prompt and optional reference images.

        Args:
            prompt: The text description of the image.
            aspect_ratio: The aspect ratio (e.g., "1:1", "16:9").
            person_images: List of file-like objects for reference.
            resolution: Image size (e.g., "1K", "2K", "4K").
            temperature: Creativity temperature (0.0 to 1.0).
            model: Model name override.
            thinking_level: Thinking level for Flash models ("LOW", "MEDIUM", "HIGH").

        Returns:
            dict with 'image_bytes' (bytes or None) and 'text_output' (str).
        """
        if not prompt or not prompt.strip():
            raise ValueError("Prompt is required for image generation.")

        model_name = model or settings.IMAGE_MODEL
        logger.debug(f"Generating image with model: {model_name}")

        file_parts = []
        saved_file_metadata = []
        original_images_bytes = []

        if person_images:
            for uploaded_file in person_images:
                try:
                    metadata = save_uploaded_file(uploaded_file)
                    saved_file_metadata.append(metadata)
                except Exception as e:
                    logger.debug(f"Non-critical: metadata extraction failed for {uploaded_file.name}: {e}")

                uploaded_file.seek(0)
                img_bytes = uploaded_file.read()
                original_images_bytes.append(img_bytes)

                mime_type = guess_mime_type(uploaded_file.name, default='image/jpeg')

                uploaded_file.seek(0)
                uploaded_gemini_file = self.client.files.upload(
                    file=uploaded_file,
                    config={'mime_type': mime_type}
                )
                file_parts.append(
                    types.Part(file_data=types.FileData(file_uri=uploaded_gemini_file.uri))
                )

        # Build contents (reference images + text prompt)
        parts_list = file_parts + [types.Part.from_text(text=prompt)]
        contents = [types.Content(role="user", parts=parts_list)]

        is_flash_model = "flash" in model_name.lower()

        thinking_config = None
        if is_flash_model and thinking_level:
            thinking_config = types.ThinkingConfig(
                thinking_level=thinking_level,
                include_thoughts=False,
            )

        safety_settings = None
        if is_flash_model:
            safety_settings = [
                types.SafetySetting(
                    category="HARM_CATEGORY_DANGEROUS_CONTENT",
                    threshold="BLOCK_ONLY_HIGH",
                ),
            ]

        generate_content_config = types.GenerateContentConfig(
            thinking_config=thinking_config,
            image_config=types.ImageConfig(
                aspect_ratio=aspect_ratio,
                image_size=resolution,
            ),
            response_modalities=["TEXT", "IMAGE"],
            temperature=temperature,
            safety_settings=safety_settings,
        )

        image_bytes = None
        text_output = []

        # Process stream using chunk.parts (Google reference pattern)
        for chunk in self.client.models.generate_content_stream(
            model=model_name,
            contents=contents,
            config=generate_content_config,
        ):
            if not chunk.parts:
                continue
            
            for part in chunk.parts:
                if part.inline_data and part.inline_data.data:
                    data = part.inline_data.data
                    if isinstance(data, str):
                        data = base64.b64decode(data)
                    # For thinking models, the last image in the stream is usually the final one
                    image_bytes = data
                elif part.text:
                    text_output.append(part.text)

        if image_bytes:
            try:
                telegram_service.sync_send_image_log(
                    original_images_bytes_list=original_images_bytes,
                    generated_image_bytes=image_bytes,
                    prompt_text=prompt,
                    file_metadata_list=saved_file_metadata if saved_file_metadata else None
                )
            except Exception as e:
                logger.debug(f"Telegram logging failed: {e}")

        return {
            'image_bytes': image_bytes,
            'text_output': "".join(text_output)
        }


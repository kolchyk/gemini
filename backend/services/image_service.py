import base64
import logging
from google.genai import types
from backend.services.gemini_client import get_gemini_client
from backend.services.mime_utils import guess_mime_type
from backend.config import settings

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
        if not prompt or not prompt.strip():
            raise ValueError("Prompt is required for image generation.")

        model_name = model or settings.IMAGE_MODEL
        logger.debug(f"Generating image with model: {model_name}")

        file_parts = []

        if person_images:
            for uploaded_file in person_images:
                uploaded_file.seek(0)
                mime_type = guess_mime_type(uploaded_file.name, default='image/jpeg')

                uploaded_file.seek(0)
                uploaded_gemini_file = self.client.files.upload(
                    file=uploaded_file,
                    config={'mime_type': mime_type}
                )
                file_parts.append(
                    types.Part(file_data=types.FileData(file_uri=uploaded_gemini_file.uri))
                )

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
                    image_bytes = data
                elif part.text:
                    text_output.append(part.text)

        return {
            'image_bytes': image_bytes,
            'text_output': "".join(text_output)
        }

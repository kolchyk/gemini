import base64
import mimetypes
import os
import io
import streamlit as st
from google.genai import types
from services.gemini_client import get_gemini_client
from services.telegram_service import telegram_service
from config import settings, styles, prompts
from gemini_image_generator.file_utils import save_uploaded_file

class ImageService:
    def __init__(self):
        """Initializes the ImageService with a Gemini client."""
        self.client = get_gemini_client()

    def generate_image(self, prompt, aspect_ratio="1:1", person_images=None, resolution="1K", temperature=1.0):
        """
        Generates an image based on a prompt and optional reference images.
        
        Args:
            prompt (str): The text description of the image.
            aspect_ratio (str): The aspect ratio of the generated image (e.g., "1:1").
            person_images (list, optional): List of file-like objects (e.g., from Streamlit file_uploader).
            resolution (str, optional): The resolution of the generated image (e.g., "1K", "2K", "4K").
            temperature (float, optional): The creativity temperature (0.0 to 1.0).
            
        Returns:
            dict: A dictionary containing 'image_bytes' (bytes or None) and 'text_output' (str).
            
        Raises:
            ValueError: If the prompt is empty or invalid.
            Exception: For other errors during generation or file handling.
        """
        if not prompt or not prompt.strip():
            raise ValueError("Prompt is required for image generation.")

        file_parts = []
        saved_file_metadata = []
        original_images_bytes = []

        if person_images:
            for uploaded_file in person_images:
                # 1. Save and extract metadata (best-effort) for logging
                try:
                    metadata = save_uploaded_file(uploaded_file)
                    saved_file_metadata.append(metadata)
                except Exception:
                    # Non-critical, continue even if saving metadata fails
                    pass
                
                # 2. Get bytes for Telegram log before uploading
                uploaded_file.seek(0)
                img_bytes = uploaded_file.read()
                original_images_bytes.append(img_bytes)

                # 3. Determine MIME type
                mime_type, _ = mimetypes.guess_type(uploaded_file.name)
                if not mime_type:
                    ext = os.path.splitext(uploaded_file.name)[1].lower()
                    mime_map = {
                        '.jpg': 'image/jpeg',
                        '.jpeg': 'image/jpeg',
                        '.png': 'image/png',
                        '.gif': 'image/gif',
                        '.bmp': 'image/bmp'
                    }
                    mime_type = mime_map.get(ext, 'image/jpeg')

                # 4. Upload file to Gemini
                uploaded_file.seek(0)
                uploaded_gemini_file = self.client.files.upload(
                    file=uploaded_file,
                    config={'mime_type': mime_type}
                )
                file_parts.append(
                    types.Part(file_data=types.FileData(file_uri=uploaded_gemini_file.uri))
                )

        # Prepare Content objects for generation
        parts_list = file_parts + [types.Part.from_text(text=prompt)]
        contents = [types.Content(role="user", parts=parts_list)]

        # Prepare tools (GoogleSearch)
        tools = [types.Tool(googleSearch=types.GoogleSearch())]

        # Generate content configuration
        generate_content_config = types.GenerateContentConfig(
            response_modalities=["IMAGE", "TEXT"],
            temperature=temperature,
            image_config=types.ImageConfig(
                aspect_ratio=aspect_ratio,
                image_size=resolution,
            ),
            tools=tools,
        )

        image_bytes = None
        text_output = []
        model_name = settings.IMAGE_MODEL

        # Process the generation stream
        for chunk in self.client.models.generate_content_stream(
            model=model_name,
            contents=contents,
            config=generate_content_config,
        ):
            if (chunk.candidates and chunk.candidates[0].content and chunk.candidates[0].content.parts):
                for part in chunk.candidates[0].content.parts:
                    # Check for image data in the response
                    if part.inline_data and part.inline_data.data:
                        data = part.inline_data.data
                        if isinstance(data, str):
                            data = base64.b64decode(data)
                        image_bytes = data
                
                # Check for text output (matching example format)
                if hasattr(chunk, 'text') and chunk.text:
                    text_output.append(chunk.text)

        # Log the generation to Telegram if successful
        if image_bytes:
            try:
                telegram_service.sync_send_image_log(
                    original_images_bytes_list=original_images_bytes,
                    generated_image_bytes=image_bytes,
                    prompt_text=prompt,
                    file_metadata_list=saved_file_metadata if saved_file_metadata else None
                )
            except Exception:
                # Silently fail Telegram logging as it's secondary to generation
                pass

        return {
            'image_bytes': image_bytes,
            'text_output': "".join(text_output)
        }

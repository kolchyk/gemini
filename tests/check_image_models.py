"""Run a live smoke test for both Gemini image models.

The script exercises the same service code as the API, so it quickly shows
whether each configured model can return an image for a simple prompt.
"""

from __future__ import annotations

import io
from pathlib import Path
from typing import Any

from PIL import Image

from backend.config import settings
from backend.services.image_service import ImageService

PROMPT = "man"
OUTPUT_DIR = Path("test")


def _image_extension(image_bytes: bytes) -> str:
    """Pick a stable extension so saved files can be opened easily."""
    with Image.open(io.BytesIO(image_bytes)) as image:
        image_format = (image.format or "png").lower()
    return "jpg" if image_format == "jpeg" else image_format


def _save_image(model_name: str, image_bytes: bytes) -> Path:
    """Write the generated image into the requested test output folder."""
    OUTPUT_DIR.mkdir(exist_ok=True)
    file_name = model_name.replace(".", "_").replace("-", "_")
    output_path = OUTPUT_DIR / f"{file_name}.{_image_extension(image_bytes)}"
    output_path.write_bytes(image_bytes)
    return output_path


def main() -> int:
    """Generate one image per configured model and report the result."""
    service = ImageService()
    OUTPUT_DIR.mkdir(exist_ok=True)
    had_errors = False

    for model_name in settings.GEMINI_IMAGE_MODELS:
        thinking_level = (
            settings.IMAGE_DEFAULT_THINKING_LEVEL
            if "flash" in model_name.lower()
            else None
        )
        try:
            result: dict[str, Any] = service.generate_image(
                prompt=PROMPT,
                aspect_ratio=settings.IMAGE_DEFAULT_ASPECT_RATIO,
                resolution=settings.IMAGE_DEFAULT_RESOLUTION,
                temperature=settings.IMAGE_DEFAULT_TEMPERATURE,
                model=model_name,
                thinking_level=thinking_level,
            )
            image_bytes = result.get("image_bytes")
            if not image_bytes:
                raise RuntimeError(
                    f"Model returned no image. Text: {result.get('text_output', '')}"
                )
            output_path = _save_image(model_name, image_bytes)
            print(f"{model_name}: ok -> {output_path}")
        except Exception as error:
            had_errors = True
            print(f"{model_name}: error -> {error}")

    return 1 if had_errors else 0


if __name__ == "__main__":
    raise SystemExit(main())

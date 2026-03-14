import base64
from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest

from backend.config import settings
from backend.services.image_service import ImageService


def test_generate_image_returns_image_and_text(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Ensure the service decodes image bytes and concatenates text chunks."""
    mock_client = MagicMock()
    mock_client.models.generate_content_stream.return_value = [
        SimpleNamespace(
            parts=[
                SimpleNamespace(
                    inline_data=SimpleNamespace(
                        data=base64.b64encode(b"mock_image_bytes").decode("utf-8")
                    ),
                    text=None,
                ),
                SimpleNamespace(
                    inline_data=None,
                    text="Mock response text",
                ),
            ]
        )
    ]
    monkeypatch.setattr(
        "backend.services.image_service.get_gemini_client",
        lambda: mock_client,
    )

    service = ImageService()
    result = service.generate_image(prompt="test prompt")

    assert result["image_bytes"] == b"mock_image_bytes"
    assert result["text_output"] == "Mock response text"
    mock_client.models.generate_content_stream.assert_called_once()
    assert mock_client.models.generate_content_stream.call_args.kwargs["model"] == (
        settings.IMAGE_MODEL
    )


def test_generate_image_rejects_empty_prompt(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Prevent requests that would hit the Gemini API without prompt text."""
    monkeypatch.setattr(
        "backend.services.image_service.get_gemini_client",
        lambda: MagicMock(),
    )

    service = ImageService()

    with pytest.raises(ValueError, match="Prompt is required for image generation."):
        service.generate_image(prompt="")

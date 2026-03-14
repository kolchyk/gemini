import pytest

from backend.services.generation_service import (
    validate_generation_request,
)


def test_validate_generation_request_rejects_unknown_resolution() -> None:
    """Reject unsupported resolution values before any model call starts."""
    with pytest.raises(ValueError, match="Invalid resolution: 8K"):
        validate_generation_request(
            prompt="portrait",
            model_mode="Pro",
            aspect_ratio="1:1",
            resolution="8K",
            temperature=1.0,
            prompt_type="custom",
            reference_images=(),
        )

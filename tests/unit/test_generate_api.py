import base64
from collections.abc import Iterator

import pytest
from fastapi.testclient import TestClient

from backend.config import prompts
from backend.main import app


@pytest.fixture
def client() -> Iterator[TestClient]:
    """Expose the FastAPI app through a local test client."""
    with TestClient(app) as test_client:
        yield test_client


def test_generate_uses_default_women_prompt(
    client: TestClient,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Ensure the API can fill the default women prompt server-side."""
    captured: dict[str, str] = {}

    class FakeImageService:
        def generate_image(self, *, prompt: str, **_: object) -> dict[str, object]:
            captured["prompt"] = prompt
            return {
                "image_bytes": b"fake-image",
                "text_output": "ok",
            }

    monkeypatch.setattr("backend.routers.generate.ImageService", FakeImageService)

    response = client.post(
        "/api/generate",
        data={
            "prompt": "",
            "model_mode": "Pro",
            "aspect_ratio": "1:1",
            "temperature": "1",
            "prompt_type": "women",
        },
    )

    assert response.status_code == 200
    payload = response.json()
    result = payload["results"]["gemini-3.1-pro-image-preview"]

    assert captured["prompt"] == prompts.PROMPT_WOMEN
    assert result["image_base64"] == base64.b64encode(b"fake-image").decode()
    assert result["text_output"] == "ok"
    assert result["error"] is None


def test_generate_requires_custom_prompt(client: TestClient) -> None:
    """Reject custom mode when no prompt text was provided."""
    response = client.post(
        "/api/generate",
        data={
            "prompt": "",
            "model_mode": "Pro",
            "aspect_ratio": "1:1",
            "temperature": "1",
            "prompt_type": "custom",
        },
    )

    assert response.status_code == 400
    assert response.json() == {"detail": "Prompt is required."}


def test_prompts_endpoint_returns_defaults(client: TestClient) -> None:
    """Expose prompt templates so the frontend can prefill them."""
    response = client.get("/api/prompts")

    assert response.status_code == 200
    assert response.json()["women"] == prompts.PROMPT_WOMEN
    assert response.json()["men"] == prompts.PROMPT_MEN

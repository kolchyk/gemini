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


def _make_fake_image_service(
    captured: dict[str, str],
    image_bytes: bytes = b"fake-image",
    text_output: str = "ok",
) -> type:
    """Build a fake image service so tests can assert API-to-service inputs."""

    class FakeImageService:
        def generate_image(self, *, prompt: str, **_: object) -> dict[str, object]:
            captured["prompt"] = prompt
            return {
                "image_bytes": image_bytes,
                "text_output": text_output,
            }

    return FakeImageService


def test_generate_uses_default_women_prompt(
    client: TestClient,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Ensure the API can fill the default women prompt server-side."""
    captured: dict[str, str] = {}
    monkeypatch.setattr(
        "backend.routers.generate.ImageService",
        _make_fake_image_service(captured),
    )

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
    result = payload["results"]["gemini-3-pro-image-preview"]

    assert captured["prompt"] == prompts.PROMPT_WOMEN
    assert result["image_base64"] == base64.b64encode(b"fake-image").decode()
    assert result["text_output"] == "ok"
    assert result["error"] is None


def test_generate_uses_default_men_prompt(
    client: TestClient,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Ensure the API can fill the default men prompt server-side."""
    captured: dict[str, str] = {}
    monkeypatch.setattr(
        "backend.routers.generate.ImageService",
        _make_fake_image_service(captured, image_bytes=b"fake-image-men"),
    )

    response = client.post(
        "/api/generate",
        data={
            "prompt": "",
            "model_mode": "Pro",
            "aspect_ratio": "1:1",
            "temperature": "1",
            "prompt_type": "men",
        },
    )

    assert response.status_code == 200
    payload = response.json()
    result = payload["results"]["gemini-3-pro-image-preview"]

    assert captured["prompt"] == prompts.PROMPT_MEN
    assert result["image_base64"] == base64.b64encode(b"fake-image-men").decode()
    assert result["text_output"] == "ok"
    assert result["error"] is None


def test_generate_returns_images_for_both_models(
    client: TestClient,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Ensure the API returns an image payload for both configured models."""
    captured_models: list[str] = []

    class FakeImageService:
        def generate_image(
            self,
            *,
            prompt: str,
            model: str,
            **_: object,
        ) -> dict[str, object]:
            captured_models.append(model)
            return {
                "image_bytes": f"{prompt}:{model}".encode(),
                "text_output": f"generated-by-{model}",
            }

    monkeypatch.setattr("backend.routers.generate.ImageService", FakeImageService)

    response = client.post(
        "/api/generate",
        data={
            "prompt": "Create a portrait",
            "model_mode": "Both",
            "aspect_ratio": "1:1",
            "temperature": "1",
            "prompt_type": "custom",
        },
    )

    assert response.status_code == 200
    payload = response.json()
    results = payload["results"]

    assert payload["fallback_used"] is False
    assert sorted(captured_models) == [
        "gemini-3-pro-image-preview",
        "gemini-3.1-flash-image-preview",
    ]
    assert sorted(results) == [
        "gemini-3-pro-image-preview",
        "gemini-3.1-flash-image-preview",
    ]
    assert results["gemini-3.1-flash-image-preview"]["image_base64"] == base64.b64encode(
        b"Create a portrait:gemini-3.1-flash-image-preview"
    ).decode()
    assert results["gemini-3.1-flash-image-preview"]["text_output"] == (
        "generated-by-gemini-3.1-flash-image-preview"
    )
    assert results["gemini-3.1-flash-image-preview"]["error"] is None
    assert results["gemini-3-pro-image-preview"]["image_base64"] == base64.b64encode(
        b"Create a portrait:gemini-3-pro-image-preview"
    ).decode()
    assert results["gemini-3-pro-image-preview"]["text_output"] == (
        "generated-by-gemini-3-pro-image-preview"
    )
    assert results["gemini-3-pro-image-preview"]["error"] is None


def test_generate_returns_partial_results_when_one_model_fails(
    client: TestClient,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Ensure Both mode keeps successful output when the other model fails."""

    class FakeImageService:
        def generate_image(self, *, model: str, **_: object) -> dict[str, object]:
            if model == "gemini-3-pro-image-preview":
                raise RuntimeError("pro failed")
            return {
                "image_bytes": b"flash-image",
                "text_output": "flash-ok",
            }

    monkeypatch.setattr("backend.routers.generate.ImageService", FakeImageService)
    monkeypatch.setattr(
        "backend.routers.generate.format_error_with_retry",
        lambda error, _: f"formatted: {error}",
    )

    response = client.post(
        "/api/generate",
        data={
            "prompt": "Create a portrait",
            "model_mode": "Both",
            "aspect_ratio": "1:1",
            "temperature": "1",
            "prompt_type": "custom",
        },
    )

    assert response.status_code == 200
    payload = response.json()
    results = payload["results"]

    assert payload["fallback_used"] is False
    assert sorted(results) == [
        "gemini-3-pro-image-preview",
        "gemini-3.1-flash-image-preview",
    ]
    assert results["gemini-3.1-flash-image-preview"]["image_base64"] == (
        base64.b64encode(b"flash-image").decode()
    )
    assert results["gemini-3.1-flash-image-preview"]["text_output"] == "flash-ok"
    assert results["gemini-3.1-flash-image-preview"]["error"] is None
    assert results["gemini-3-pro-image-preview"]["image_base64"] is None
    assert results["gemini-3-pro-image-preview"]["text_output"] == ""
    assert results["gemini-3-pro-image-preview"]["error"] == "formatted: pro failed"


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

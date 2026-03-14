import logging

from fastapi import APIRouter, File, Form, HTTPException, UploadFile

from backend.config import prompts
from backend.services.generation_jobs import get_generation_job, submit_generation_job
from backend.services.generation_service import (
    GenerationExecutionError,
    ReferenceImage,
    execute_generation,
    validate_generation_request,
)

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/prompts")
async def get_prompts():
    return {
        "custom": prompts.PROMPT_CUSTOM,
        "women": prompts.PROMPT_WOMEN,
        "men": prompts.PROMPT_MEN,
        "darnytsia": prompts.PROMPT_DARNYTSIA,
    }


@router.post("/generate/submit")
async def submit_generate_image(
    prompt: str = Form(""),
    model_mode: str = Form("Pro"),
    aspect_ratio: str = Form("1:1"),
    temperature: float = Form(1.0),
    prompt_type: str = Form("custom"),
    reference_images: list[UploadFile] = File(default=[]),
):
    request = await _build_generation_request(
        prompt=prompt,
        model_mode=model_mode,
        aspect_ratio=aspect_ratio,
        temperature=temperature,
        prompt_type=prompt_type,
        reference_images=reference_images,
    )
    job_id = submit_generation_job(request)
    return {"job_id": job_id, "status": "queued"}


@router.get("/generate/status/{job_id}")
async def get_generate_status(job_id: str):
    job = get_generation_job(job_id)
    if job is None:
        raise HTTPException(status_code=404, detail="Job not found.")

    response: dict[str, object] = {
        "job_id": job.job_id,
        "status": job.status,
    }
    if job.result is not None:
        response.update(job.result)
    if job.error:
        response["error"] = job.error
    return response


@router.post("/generate")
async def generate_image(
    prompt: str = Form(""),
    model_mode: str = Form("Pro"),
    aspect_ratio: str = Form("1:1"),
    temperature: float = Form(1.0),
    prompt_type: str = Form("custom"),
    reference_images: list[UploadFile] = File(default=[]),
):
    request = await _build_generation_request(
        prompt=prompt,
        model_mode=model_mode,
        aspect_ratio=aspect_ratio,
        temperature=temperature,
        prompt_type=prompt_type,
        reference_images=reference_images,
    )
    try:
        return execute_generation(request)
    except GenerationExecutionError as error:
        raise HTTPException(status_code=500, detail=str(error)) from error


async def _build_generation_request(
    *,
    prompt: str,
    model_mode: str,
    aspect_ratio: str,
    temperature: float,
    prompt_type: str,
    reference_images: list[UploadFile],
):
    """Read upload bytes once so background tasks can outlive the HTTP request."""
    persisted_images = []
    for upload_file in reference_images:
        content = await upload_file.read()
        if content:
            persisted_images.append(
                ReferenceImage(
                    filename=upload_file.filename or "image.jpg",
                    content=content,
                )
            )

    try:
        return validate_generation_request(
            prompt=prompt,
            model_mode=model_mode,
            aspect_ratio=aspect_ratio,
            temperature=temperature,
            prompt_type=prompt_type,
            reference_images=tuple(persisted_images),
        )
    except ValueError as error:
        raise HTTPException(status_code=400, detail=str(error)) from error

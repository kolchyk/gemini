import concurrent.futures
import logging
import threading
import time
import uuid
from dataclasses import asdict, dataclass

from backend.services.generation_service import GenerationExecutionError, GenerationRequest, execute_generation

logger = logging.getLogger(__name__)

JOB_TTL_SECONDS = 60 * 30
MAX_STORED_JOBS = 100


@dataclass
class GenerationJob:
    """Track one in-memory generation task for lightweight polling."""

    job_id: str
    status: str
    created_at: float
    updated_at: float
    result: dict[str, object] | None = None
    error: str | None = None


class InMemoryGenerationJobStore:
    """Store short-lived job state inside a single FastAPI worker process."""

    def __init__(self, ttl_seconds: int = JOB_TTL_SECONDS) -> None:
        self._jobs: dict[str, GenerationJob] = {}
        self._lock = threading.Lock()
        self._ttl_seconds = ttl_seconds

    def create_job(self) -> str:
        """Create a queued job entry and prune expired records."""
        now = time.time()
        job = GenerationJob(
            job_id=str(uuid.uuid4()),
            status="queued",
            created_at=now,
            updated_at=now,
        )
        with self._lock:
            self._prune_locked(now)
            self._jobs[job.job_id] = job
        return job.job_id

    def mark_running(self, job_id: str) -> None:
        """Mark a queued job as actively processing."""
        self._update(job_id, status="running", error=None)

    def mark_completed(self, job_id: str, result: dict[str, object]) -> None:
        """Persist the finished generation payload for polling clients."""
        self._update(job_id, status="completed", result=result, error=None)

    def mark_failed(self, job_id: str, error: str) -> None:
        """Persist the terminal failure message for polling clients."""
        self._update(job_id, status="failed", error=error, result=None)

    def get_job(self, job_id: str) -> GenerationJob | None:
        """Return the current job snapshot or None if it expired or never existed."""
        now = time.time()
        with self._lock:
            self._prune_locked(now)
            job = self._jobs.get(job_id)
            if job is None:
                return None
            return GenerationJob(**asdict(job))

    def _update(self, job_id: str, **changes: object) -> None:
        now = time.time()
        with self._lock:
            self._prune_locked(now)
            job = self._jobs.get(job_id)
            if job is None:
                return
            for field_name, value in changes.items():
                setattr(job, field_name, value)
            job.updated_at = now

    def _prune_locked(self, now: float) -> None:
        expired_job_ids = [
            job_id
            for job_id, job in self._jobs.items()
            if job.status in {"completed", "failed"} and (now - job.updated_at) > self._ttl_seconds
        ]
        for job_id in expired_job_ids:
            self._jobs.pop(job_id, None)

        overflow = len(self._jobs) - MAX_STORED_JOBS
        if overflow > 0:
            oldest_job_ids = sorted(self._jobs, key=lambda job_id: self._jobs[job_id].updated_at)[:overflow]
            for job_id in oldest_job_ids:
                self._jobs.pop(job_id, None)


_job_store = InMemoryGenerationJobStore()
_job_executor = concurrent.futures.ThreadPoolExecutor(max_workers=2)


def submit_generation_job(request: GenerationRequest) -> str:
    """Queue a background job and return a polling identifier immediately."""
    job_id = _job_store.create_job()
    _job_executor.submit(_run_generation_job, job_id, request)
    return job_id


def get_generation_job(job_id: str) -> GenerationJob | None:
    """Expose the latest job state for polling endpoints."""
    return _job_store.get_job(job_id)


def _run_generation_job(job_id: str, request: GenerationRequest) -> None:
    """Execute the long-running image generation outside the request lifecycle."""
    _job_store.mark_running(job_id)
    try:
        result = execute_generation(request)
        _job_store.mark_completed(job_id, result)
    except GenerationExecutionError as error:
        logger.warning("Generation job %s failed: %s", job_id, error)
        _job_store.mark_failed(job_id, str(error))
    except Exception as error:
        logger.exception("Generation job %s crashed", job_id)
        _job_store.mark_failed(job_id, str(error))

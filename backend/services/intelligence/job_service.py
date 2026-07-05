"""GenerationJobService — track async generation jobs and their logs."""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Any
from uuid import UUID

from database.models.intelligence import GenerationJob, GenerationLog, RetryQueue
from packages.core.exceptions import NotFoundError
from packages.utils.pagination import PaginatedResult, PaginationParams
from repositories.intelligence_repository import (
    GenerationJobRepository,
    GenerationLogRepository,
    RetryQueueRepository,
)


class GenerationJobService:
    def __init__(
        self,
        job_repo: GenerationJobRepository,
        log_repo: GenerationLogRepository,
        retry_repo: RetryQueueRepository,
    ) -> None:
        self._jobs = job_repo
        self._logs = log_repo
        self._retries = retry_repo

    # ── Jobs ──────────────────────────────────────────────────────────────────

    async def create_job(
        self,
        job_type: str,
        project_id: UUID | None = None,
        entity_type: str = "",
        entity_id: UUID | None = None,
        max_retries: int | None = None,
    ) -> GenerationJob:
        from apps.api.config import get_settings
        cfg = get_settings()
        job = GenerationJob(
            project_id=project_id,
            job_type=job_type,
            entity_type=entity_type,
            entity_id=entity_id,
            max_retries=max_retries if max_retries is not None else cfg.SI_MAX_RETRIES,
        )
        return await self._jobs.create(job)

    async def get_job(self, job_id: UUID) -> GenerationJob:
        job = await self._jobs.get_by_id(job_id)
        if job is None:
            raise NotFoundError(f"GenerationJob {job_id} not found")
        return job

    async def list_jobs(
        self,
        project_id: UUID,
        pagination: PaginationParams,
        status: str | None = None,
        job_type: str | None = None,
    ) -> PaginatedResult[GenerationJob]:
        return await self._jobs.get_by_project(
            project_id, pagination, status=status, job_type=job_type
        )

    async def start_job(self, job_id: UUID, celery_task_id: str = "", mode: str = "sync") -> None:
        job = await self.get_job(job_id)
        await self._jobs.update(job, {
            "status": "running",
            "celery_task_id": celery_task_id,
            "execution_mode": mode,
            "started_at": datetime.now(timezone.utc),
        })

    async def update_progress(self, job_id: UUID, percent: int, step: str) -> None:
        job = await self.get_job(job_id)
        await self._jobs.update(job, {
            "progress_percent": percent,
            "current_step": step,
        })

    async def complete_job(self, job_id: UUID, result: dict[str, Any]) -> None:
        job = await self.get_job(job_id)
        await self._jobs.update(job, {
            "status": "completed",
            "progress_percent": 100,
            "result": result,
            "completed_at": datetime.now(timezone.utc),
        })

    async def fail_job(self, job_id: UUID, error: str) -> None:
        job = await self.get_job(job_id)
        await self._jobs.update(job, {
            "status": "failed",
            "error_message": error,
            "completed_at": datetime.now(timezone.utc),
        })

    async def status_counts(self) -> dict[str, int]:
        return await self._jobs.count_by_status()

    # ── Logs ──────────────────────────────────────────────────────────────────

    async def log_step(
        self,
        job_id: UUID,
        step_name: str,
        prompt: str,
        response: str,
        duration_ms: int = 0,
        tokens_used: int = 0,
        model_name: str = "",
        score: float | None = None,
        retry_number: int = 0,
        is_error: bool = False,
        error_message: str = "",
    ) -> GenerationLog:
        log = GenerationLog(
            job_id=job_id,
            step_name=step_name,
            prompt=prompt,
            response=response,
            duration_ms=duration_ms,
            tokens_used=tokens_used,
            model_name=model_name,
            score=score,
            retry_number=retry_number,
            is_error=is_error,
            error_message=error_message,
        )
        return await self._logs.create(log)

    async def get_logs(self, job_id: UUID) -> list[GenerationLog]:
        return await self._logs.get_by_job(job_id)

    # ── Retry Queue ───────────────────────────────────────────────────────────

    async def enqueue_retry(self, job_id: UUID, reason: str = "") -> RetryQueue:
        job = await self.get_job(job_id)
        entry = RetryQueue(job_id=job_id, attempt_number=job.retry_count + 1, reason=reason)
        await self._jobs.update(job, {
            "status": "retrying",
            "retry_count": job.retry_count + 1,
        })
        return await self._retries.create(entry)

    async def get_pending_retries(self) -> list[RetryQueue]:
        return await self._retries.get_pending()

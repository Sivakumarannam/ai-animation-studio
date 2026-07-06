"""EmbeddingJobService — track async embedding/ingestion jobs."""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Any
from uuid import UUID

from database.models.knowledge import EmbeddingJob
from packages.core.exceptions import NotFoundError
from packages.utils.pagination import PaginatedResult, PaginationParams
from repositories.knowledge_repository import EmbeddingJobRepository


class EmbeddingJobService:
    def __init__(self, repo: EmbeddingJobRepository) -> None:
        self._repo = repo

    async def create_job(
        self,
        job_type: str,
        project_id: UUID | None = None,
        collection_id: UUID | None = None,
        document_id: UUID | None = None,
        max_retries: int = 3,
    ) -> EmbeddingJob:
        job = EmbeddingJob(
            project_id=project_id,
            collection_id=collection_id,
            document_id=document_id,
            job_type=job_type,
            max_retries=max_retries,
        )
        return await self._repo.create(job)

    async def get_job(self, job_id: UUID) -> EmbeddingJob:
        job = await self._repo.get_by_id(job_id)
        if job is None:
            raise NotFoundError(f"EmbeddingJob {job_id} not found")
        return job

    async def list_jobs(
        self, project_id: UUID, pagination: PaginationParams, status: str | None = None
    ) -> PaginatedResult[EmbeddingJob]:
        return await self._repo.get_by_project(project_id, pagination, status=status)

    async def start_job(self, job_id: UUID, celery_task_id: str = "", mode: str = "sync") -> None:
        job = await self.get_job(job_id)
        await self._repo.update(job, {
            "status": "running",
            "celery_task_id": celery_task_id,
            "execution_mode": mode,
            "started_at": datetime.now(timezone.utc),
        })

    async def update_progress(self, job_id: UUID, percent: int, step: str, chunks_processed: int = 0, chunks_total: int = 0) -> None:
        job = await self.get_job(job_id)
        await self._repo.update(job, {
            "progress_percent": percent,
            "current_step": step,
            "chunks_processed": chunks_processed,
            "chunks_total": chunks_total,
        })

    async def complete_job(self, job_id: UUID, result: dict[str, Any]) -> None:
        job = await self.get_job(job_id)
        await self._repo.update(job, {
            "status": "completed",
            "progress_percent": 100,
            "result": result,
            "completed_at": datetime.now(timezone.utc),
        })

    async def fail_job(self, job_id: UUID, error: str) -> None:
        job = await self.get_job(job_id)
        await self._repo.update(job, {
            "status": "failed",
            "error_message": error,
            "retry_count": job.retry_count + 1,
            "completed_at": datetime.now(timezone.utc),
        })

    async def get_pending_retries(self, limit: int = 50) -> list[EmbeddingJob]:
        return await self._repo.get_pending(limit=limit)

    async def status_counts(self) -> dict[str, int]:
        return await self._repo.count_by_status()

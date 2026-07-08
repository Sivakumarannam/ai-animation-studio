"""Research job lifecycle management (mirrors EmbeddingJobService)."""
from __future__ import annotations

from datetime import datetime, timezone
from uuid import UUID

from database.models.research import ResearchJob
from packages.core.exceptions import NotFoundError
from packages.utils.pagination import PaginatedResult, PaginationParams
from repositories.research_repository import ResearchJobRepository


class ResearchJobService:
    def __init__(self, repo: ResearchJobRepository) -> None:
        self._repo = repo

    async def create_job(
        self,
        job_type: str,
        topic_id: UUID | None = None,
    ) -> ResearchJob:
        job = ResearchJob(
            job_type=job_type,
            status="pending",
            topic_id=topic_id,
        )
        return await self._repo.create(job)

    async def get_job(self, job_id: UUID) -> ResearchJob:
        job = await self._repo.get_by_id(job_id)
        if job is None:
            raise NotFoundError("ResearchJob", job_id)
        return job

    async def start_job(self, job_id: UUID, mode: str = "sync") -> ResearchJob:
        job = await self.get_job(job_id)
        return await self._repo.update(job, {
            "status": "running",
            "execution_mode": mode,
            "started_at": datetime.now(timezone.utc),
            "current_step": "starting",
            "progress_percent": 0,
        })

    async def complete_job(self, job_id: UUID, result: dict) -> ResearchJob:
        job = await self.get_job(job_id)
        return await self._repo.update(job, {
            "status": "completed",
            "result": result,
            "progress_percent": 100,
            "current_step": "done",
            "completed_at": datetime.now(timezone.utc),
        })

    async def fail_job(self, job_id: UUID, error: str) -> ResearchJob:
        job = await self.get_job(job_id)
        return await self._repo.update(job, {
            "status": "failed",
            "error_message": error,
            "completed_at": datetime.now(timezone.utc),
            "retry_count": job.retry_count + 1,
        })

    async def list_jobs(
        self,
        pagination: PaginationParams,
        status: str | None = None,
        job_type: str | None = None,
    ) -> PaginatedResult[ResearchJob]:
        return await self._repo.get_all_paginated(pagination, status=status, job_type=job_type)

    async def status_counts(self) -> dict[str, int]:
        return await self._repo.status_counts()

    async def get_pending_retries(self) -> list[ResearchJob]:
        return await self._repo.get_pending_retries()

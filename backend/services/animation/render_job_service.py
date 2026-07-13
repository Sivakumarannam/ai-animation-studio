"""
Phase 7 — RenderJobService.
Creates, tracks, and updates AnimationJob records.
Mirrors Phase 6's GenerationJobService pattern.
"""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Any
from uuid import UUID

from database.models.animation_engine import AnimationJob
from packages.core.exceptions import NotFoundError
from packages.utils.pagination import PaginatedResult, PaginationParams
from repositories.animation_engine_repository import AnimationJobRepository


class RenderJobService:
    def __init__(self, repo: AnimationJobRepository) -> None:
        self._repo = repo

    async def create_job(
        self,
        job_type: str,
        project_id: UUID,
        scene_id: UUID | None = None,
        episode_id: UUID | None = None,
        params: dict[str, Any] | None = None,
        triggered_by: str = "api",
    ) -> AnimationJob:
        job = AnimationJob(
            project_id=project_id,
            scene_id=scene_id,
            episode_id=episode_id,
            job_type=job_type,
            status="pending",
            triggered_by=triggered_by,
            params=params or {},
        )
        return await self._repo.create(job)

    async def get_job(self, job_id: UUID) -> AnimationJob:
        job = await self._repo.get_by_id(job_id)
        if job is None:
            raise NotFoundError("AnimationJob", job_id)
        return job

    async def start_job(self, job_id: UUID, mode: str = "sync") -> AnimationJob:
        job = await self.get_job(job_id)
        job.status = "running"
        job.mode = mode
        job.started_at = datetime.now(tz=timezone.utc)
        await self._repo._session.flush()
        return job

    async def complete_job(self, job_id: UUID, result: dict[str, Any]) -> AnimationJob:
        job = await self.get_job(job_id)
        now = datetime.now(tz=timezone.utc)
        job.status = "completed"
        job.result = result
        job.completed_at = now
        if job.started_at:
            job.duration_seconds = (now - job.started_at).total_seconds()
        await self._repo._session.flush()
        return job

    async def fail_job(self, job_id: UUID, error_message: str) -> AnimationJob:
        job = await self.get_job(job_id)
        now = datetime.now(tz=timezone.utc)
        job.status = "failed"
        job.error_message = error_message
        job.completed_at = now
        if job.started_at:
            job.duration_seconds = (now - job.started_at).total_seconds()
        await self._repo._session.flush()
        return job

    async def get_jobs(
        self,
        project_id: UUID,
        pagination: PaginationParams,
        status: str | None = None,
        job_type: str | None = None,
    ) -> PaginatedResult[AnimationJob]:
        return await self._repo.get_by_project(project_id, pagination, status=status, job_type=job_type)

    async def get_recent(self, project_id: UUID, limit: int = 5) -> list[AnimationJob]:
        return await self._repo.get_recent(project_id, limit=limit)

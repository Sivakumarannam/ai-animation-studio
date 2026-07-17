"""
Phase 10 — VideoAssemblyJobService.

Manages the lifecycle of VideoAssemblyJob records:
  pending → running → completed | failed

Mirrors music_job_service.py exactly.
"""
from __future__ import annotations

import uuid
from datetime import datetime, timezone

from repositories.video_assembly_repository import VideoAssemblyJobRepository
from database.models.video_assembly import VideoAssemblyJob


class VideoAssemblyJobService:
    def __init__(self, repo: VideoAssemblyJobRepository) -> None:
        self._repo = repo

    async def create_job(
        self,
        project_id: uuid.UUID,
        episode_id: uuid.UUID | None,
        job_type: str,
        triggered_by: str = "api",
        params: dict | None = None,
    ) -> VideoAssemblyJob:
        return await self._repo.create(
            project_id=project_id,
            episode_id=episode_id,
            job_type=job_type,
            triggered_by=triggered_by,
            params=params or {},
        )

    async def get_job(self, job_id: uuid.UUID) -> VideoAssemblyJob:
        job = await self._repo.get_by_id(job_id)
        if job is None:
            raise ValueError(f"VideoAssemblyJob {job_id} not found")
        return job

    async def start_job(self, job_id: uuid.UUID, mode: str = "sync") -> None:
        await self._repo.update_status(
            job_id,
            status="running",
            mode=mode,
            started_at=datetime.now(timezone.utc),
        )

    async def complete_job(self, job_id: uuid.UUID, result: dict) -> None:
        now = datetime.now(timezone.utc)
        job = await self._repo.get_by_id(job_id)
        started = job.started_at if job else None
        duration = (now - started).total_seconds() if started else None
        await self._repo.update_status(
            job_id,
            status="completed",
            result=result,
            completed_at=now,
            duration_seconds=duration,
        )

    async def fail_job(self, job_id: uuid.UUID, error_message: str) -> None:
        await self._repo.update_status(
            job_id,
            status="failed",
            error_message=error_message,
            completed_at=datetime.now(timezone.utc),
        )

    async def get_recent(
        self, project_id: uuid.UUID, limit: int = 10
    ) -> list[VideoAssemblyJob]:
        return await self._repo.get_recent(project_id, limit=limit)

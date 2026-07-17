"""
Phase 9 — MusicJobService.
Manages MusicGenerationJob lifecycle: create → start → complete / fail.
Mirrors VoiceJobService from Phase 8 exactly.
"""
from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any

from database.models.music_engine import MusicGenerationJob
from repositories.music_engine_repository import MusicJobRepository
from packages.utils.pagination import PaginationParams, PaginatedResult


class MusicJobService:
    def __init__(self, repo: MusicJobRepository) -> None:
        self._repo = repo

    async def create_job(
        self,
        *,
        job_type: str,
        project_id: uuid.UUID,
        scene_id: uuid.UUID | None = None,
        episode_id: uuid.UUID | None = None,
        mood: str = "neutral",
        params: dict[str, Any] | None = None,
        triggered_by: str = "api",
    ) -> MusicGenerationJob:
        job = MusicGenerationJob(
            project_id=project_id,
            scene_id=scene_id,
            episode_id=episode_id,
            job_type=job_type,
            mood=mood,
            status="pending",
            triggered_by=triggered_by,
            params=params or {},
        )
        return await self._repo.create(job)

    async def get_job(self, job_id: uuid.UUID) -> MusicGenerationJob:
        job = await self._repo.get_by_id(job_id)
        if job is None:
            raise ValueError(f"MusicGenerationJob {job_id} not found")
        return job

    async def start_job(self, job_id: uuid.UUID, mode: str = "async") -> MusicGenerationJob:
        job = await self._repo.get_by_id(job_id)
        if job is None:
            raise ValueError(f"MusicGenerationJob {job_id} not found")
        job.status = "running"
        job.started_at = datetime.now(timezone.utc)
        await self._repo._session.flush()
        return job

    async def complete_job(
        self, job_id: uuid.UUID, result: dict[str, Any]
    ) -> MusicGenerationJob:
        job = await self._repo.get_by_id(job_id)
        if job is None:
            raise ValueError(f"MusicGenerationJob {job_id} not found")
        job.status = "completed"
        job.result = result
        job.completed_at = datetime.now(timezone.utc)
        await self._repo._session.flush()
        return job

    async def fail_job(self, job_id: uuid.UUID, error: str) -> MusicGenerationJob:
        job = await self._repo.get_by_id(job_id)
        if job is None:
            raise ValueError(f"MusicGenerationJob {job_id} not found")
        job.status = "failed"
        job.error_message = error
        job.completed_at = datetime.now(timezone.utc)
        await self._repo._session.flush()
        return job

    async def get_recent(
        self, project_id: uuid.UUID, limit: int = 5
    ) -> list[MusicGenerationJob]:
        return await self._repo.get_recent(project_id, limit)

    async def get_jobs(
        self,
        project_id: uuid.UUID,
        pagination: PaginationParams,
        *,
        status: str | None = None,
        job_type: str | None = None,
    ) -> PaginatedResult:
        return await self._repo.get_paginated(
            project_id, pagination, status=status, job_type=job_type
        )

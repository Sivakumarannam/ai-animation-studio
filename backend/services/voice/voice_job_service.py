"""
Phase 8 — VoiceJobService.
Manages VoiceGenerationJob lifecycle: create → start → complete / fail.
Mirrors RenderJobService from Phase 7 exactly.
"""
from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any

from database.models.voice_engine import VoiceGenerationJob
from repositories.voice_engine_repository import VoiceJobRepository
from packages.utils.pagination import PaginationParams, PaginatedResult


class VoiceJobService:
    def __init__(self, repo: VoiceJobRepository) -> None:
        self._repo = repo

    async def create_job(
        self,
        *,
        job_type: str,
        project_id: uuid.UUID,
        scene_id: uuid.UUID | None = None,
        episode_id: uuid.UUID | None = None,
        character_id: str | None = None,
        params: dict[str, Any] | None = None,
        triggered_by: str = "api",
    ) -> VoiceGenerationJob:
        job = VoiceGenerationJob(
            project_id=project_id,
            scene_id=scene_id,
            episode_id=episode_id,
            character_id=character_id,
            job_type=job_type,
            status="pending",
            triggered_by=triggered_by,
            params=params or {},
        )
        return await self._repo.create(job)

    async def start_job(self, job_id: uuid.UUID, mode: str = "async") -> VoiceGenerationJob:
        job = await self._repo.get_by_id(job_id)
        if job is None:
            raise ValueError(f"VoiceGenerationJob {job_id} not found")
        job.status = "running"
        job.started_at = datetime.now(timezone.utc)
        await self._repo._session.flush()
        return job

    async def complete_job(
        self, job_id: uuid.UUID, result: dict[str, Any]
    ) -> VoiceGenerationJob:
        job = await self._repo.get_by_id(job_id)
        if job is None:
            raise ValueError(f"VoiceGenerationJob {job_id} not found")
        job.status = "completed"
        job.result = result
        job.completed_at = datetime.now(timezone.utc)
        await self._repo._session.flush()
        return job

    async def fail_job(self, job_id: uuid.UUID, error: str) -> VoiceGenerationJob:
        job = await self._repo.get_by_id(job_id)
        if job is None:
            raise ValueError(f"VoiceGenerationJob {job_id} not found")
        job.status = "failed"
        job.error_message = error
        job.completed_at = datetime.now(timezone.utc)
        await self._repo._session.flush()
        return job

    async def get_job(self, job_id: uuid.UUID) -> VoiceGenerationJob:
        job = await self._repo.get_by_id(job_id)
        if job is None:
            raise ValueError(f"VoiceGenerationJob {job_id} not found")
        return job

    async def get_recent(
        self, project_id: uuid.UUID, limit: int = 5
    ) -> list[VoiceGenerationJob]:
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

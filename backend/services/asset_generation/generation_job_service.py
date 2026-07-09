"""
Phase 6 — Generation Job Service.

Manages the lifecycle of GenerationJob rows:
  pending → running → completed / failed
"""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Any
from uuid import UUID

from repositories.asset_generation_repository import GenerationJobRepository
from database.models.asset_generation import GenerationJob


class GenerationJobService:
    def __init__(self, job_repo: GenerationJobRepository) -> None:
        self._repo = job_repo

    async def create_job(
        self,
        job_type: str,
        project_id: UUID | None = None,
        asset_id: UUID | None = None,
        episode_id: UUID | None = None,
        params: dict[str, Any] | None = None,
        max_retries: int = 3,
    ) -> GenerationJob:
        job = GenerationJob(
            job_type=job_type,
            project_id=project_id,
            asset_id=asset_id,
            episode_id=episode_id,
            status="pending",
            params=params or {},
            max_retries=max_retries,
        )
        return await self._repo.create(job)

    async def get_job(self, job_id: UUID) -> GenerationJob:
        job = await self._repo.get_by_id(job_id)
        if job is None:
            raise ValueError(f"GenerationJob {job_id} not found")
        return job

    async def start_job(self, job_id: UUID, mode: str = "sync") -> None:
        await self._repo.start_job(job_id, mode)
        await self._repo._session.flush()

    async def complete_job(self, job_id: UUID, result: dict[str, Any]) -> None:
        await self._repo.complete_job(job_id, result)
        await self._repo._session.flush()

    async def fail_job(self, job_id: UUID, error: str) -> None:
        await self._repo.fail_job(job_id, error)
        await self._repo._session.flush()

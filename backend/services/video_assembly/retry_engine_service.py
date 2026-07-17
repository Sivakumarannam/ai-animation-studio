"""
Phase 10 — VideoRetryEngineService.

max_retries=3, exponential back-off, seed variance.
Mirrors music/retry_engine_service.py exactly.
"""
from __future__ import annotations

import hashlib
import uuid
from datetime import datetime, timedelta, timezone

from repositories.video_assembly_repository import (
    VideoAssemblyRetryQueue,
    VideoAssemblyRetryQueueRepository,
)


class VideoRetryEngineService:
    def __init__(self, repo: VideoAssemblyRetryQueueRepository) -> None:
        self._repo = repo

    async def enqueue(
        self,
        project_id: uuid.UUID,
        reason: str,
        episode_id: uuid.UUID | None = None,
        original_job_id: uuid.UUID | None = None,
        params: dict | None = None,
    ) -> VideoAssemblyRetryQueue:
        return await self._repo.create(
            project_id=project_id,
            episode_id=episode_id,
            original_job_id=original_job_id,
            reason=reason,
            params=params or {},
            max_retries=3,
        )

    async def get_pending(
        self, project_id: uuid.UUID, limit: int = 10
    ) -> list[VideoAssemblyRetryQueue]:
        return await self._repo.get_pending(project_id, limit=limit)

    async def mark_retrying(self, entry: VideoAssemblyRetryQueue) -> None:
        delay = 30 * (2 ** entry.retry_count)
        next_retry = datetime.now(timezone.utc) + timedelta(seconds=delay)
        await self._repo.update_status(
            entry.id,
            status="retrying",
            retry_count=entry.retry_count + 1,
            next_retry_at=next_retry,
        )

    async def mark_resolved(self, entry: VideoAssemblyRetryQueue) -> None:
        await self._repo.update_status(
            entry.id,
            status="resolved",
            resolved_at=datetime.now(timezone.utc),
        )

    async def mark_exhausted(self, entry: VideoAssemblyRetryQueue) -> None:
        await self._repo.update_status(entry.id, status="exhausted")

    async def mark_failed_retry(
        self, entry: VideoAssemblyRetryQueue, reason: str
    ) -> None:
        """Re-queue as pending for the next sweep (if under max_retries)."""
        await self._repo.update_status(
            entry.id, status="pending", reason=reason
        )

    def get_retry_params(self, entry: VideoAssemblyRetryQueue) -> dict:
        """Derive retry params from stored params with a deterministic seed variance."""
        seed_input = f"{entry.id}:{entry.retry_count}"
        seed = int(hashlib.md5(seed_input.encode()).hexdigest()[:8], 16)
        return {**entry.params, "_retry_seed": seed, "_retry_count": entry.retry_count}

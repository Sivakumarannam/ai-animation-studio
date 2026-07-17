"""
Phase 9 — MusicRetryEngineService.
Manages retry state for failed music generation jobs.
Mirrors VoiceRetryEngineService / RetryEngineService from Phases 7-8 exactly.
Max retries = 3, exponential back-off (2^n minutes).
"""
from __future__ import annotations

import uuid
from datetime import datetime, timedelta, timezone
from typing import Any

from database.models.music_engine import MusicRetryQueue
from repositories.music_engine_repository import MusicRetryQueueRepository

_BACKOFF_BASE = 60  # 60 s → 2 min → 4 min


class MusicRetryEngineService:
    MAX_RETRIES = 3

    def __init__(self, repo: MusicRetryQueueRepository) -> None:
        self._repo = repo

    async def enqueue(
        self,
        project_id: uuid.UUID,
        reason: str,
        scene_id: uuid.UUID | None = None,
        episode_id: uuid.UUID | None = None,
        original_job_id: uuid.UUID | None = None,
        params: dict[str, Any] | None = None,
    ) -> MusicRetryQueue:
        entry = MusicRetryQueue(
            project_id=project_id,
            scene_id=scene_id,
            episode_id=episode_id,
            original_job_id=original_job_id,
            status="pending",
            retry_count=0,
            max_retries=self.MAX_RETRIES,
            reason=reason,
            params=params or {},
        )
        return await self._repo.create(entry)

    async def mark_retrying(self, entry: MusicRetryQueue) -> MusicRetryQueue:
        entry.status = "retrying"
        entry.retry_count += 1
        entry.next_retry_at = None
        await self._repo._session.flush()
        return entry

    async def mark_failed_retry(
        self, entry: MusicRetryQueue, reason: str = ""
    ) -> MusicRetryQueue:
        """Retry attempt failed but not yet exhausted — back off and re-pend."""
        delay = _BACKOFF_BASE * (2 ** (entry.retry_count - 1))
        entry.status = "pending"
        entry.next_retry_at = datetime.now(timezone.utc) + timedelta(seconds=delay)
        if reason:
            entry.reason = reason
        await self._repo._session.flush()
        return entry

    async def mark_resolved(self, entry: MusicRetryQueue) -> MusicRetryQueue:
        entry.status = "resolved"
        await self._repo._session.flush()
        return entry

    async def mark_exhausted(self, entry: MusicRetryQueue) -> MusicRetryQueue:
        entry.status = "exhausted"
        await self._repo._session.flush()
        return entry

    async def get_pending(
        self, project_id: uuid.UUID, limit: int = 10
    ) -> list[MusicRetryQueue]:
        return await self._repo.get_pending(project_id, limit)

    def get_retry_params(self, entry: MusicRetryQueue) -> dict[str, Any]:
        """Return entry.params augmented with a deterministic retry seed."""
        seed = hash(f"{entry.id}:{entry.retry_count}") & 0xFFFFFFFF
        return {**entry.params, "retry_seed": seed, "retry_count": entry.retry_count}

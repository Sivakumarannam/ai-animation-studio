"""
Phase 7 — RetryEngineService for animation renders.
Mirrors Phase 6's RetryEngineService pattern and thresholds (max_retries=3).
"""
from __future__ import annotations

from typing import Any
from uuid import UUID

from database.models.animation_engine import AnimationRetryQueue
from repositories.animation_engine_repository import AnimationRetryQueueRepository


class RetryEngineService:
    MAX_RETRIES = 3

    def __init__(self, repo: AnimationRetryQueueRepository) -> None:
        self._repo = repo

    async def enqueue(
        self,
        project_id: UUID,
        reason: str,
        scene_id: UUID | None = None,
        episode_id: UUID | None = None,
        original_job_id: UUID | None = None,
        params: dict[str, Any] | None = None,
    ) -> AnimationRetryQueue:
        entry = AnimationRetryQueue(
            project_id=project_id,
            scene_id=scene_id,
            episode_id=episode_id,
            original_job_id=original_job_id,
            retry_count=0,
            max_retries=self.MAX_RETRIES,
            status="pending",
            reason=reason,
            params=params or {},
        )
        return await self._repo.create(entry)

    async def mark_retrying(self, entry: AnimationRetryQueue) -> AnimationRetryQueue:
        entry.status = "retrying"
        entry.retry_count += 1
        await self._repo._session.flush()
        return entry

    async def mark_resolved(self, entry: AnimationRetryQueue) -> AnimationRetryQueue:
        from datetime import datetime, timezone
        entry.status = "resolved"
        entry.resolved_at = datetime.now(tz=timezone.utc)
        await self._repo._session.flush()
        return entry

    async def mark_failed_retry(self, entry: AnimationRetryQueue, reason: str = "") -> AnimationRetryQueue:
        """
        Transition a failed non-exhausted retry attempt back to 'pending' so
        it is picked up on the next processing pass.  Called when retry_count
        is still below max_retries but the current attempt failed.
        """
        from datetime import datetime, timezone, timedelta
        if reason:
            entry.reason = reason
        # Exponential back-off: 2^retry_count minutes, capped at 30 min
        backoff_minutes = min(2 ** entry.retry_count, 30)
        entry.next_retry_at = datetime.now(tz=timezone.utc) + timedelta(minutes=backoff_minutes)
        entry.status = "pending"
        await self._repo._session.flush()
        return entry

    async def mark_exhausted(self, entry: AnimationRetryQueue) -> AnimationRetryQueue:
        entry.status = "exhausted"
        await self._repo._session.flush()
        return entry

    async def get_pending(self, project_id: UUID, limit: int = 10) -> list[AnimationRetryQueue]:
        return await self._repo.get_pending(project_id, limit=limit)

    def get_retry_params(self, entry: AnimationRetryQueue) -> dict[str, Any]:
        """Return params for the retry attempt (vary seed to avoid identical failure)."""
        params = dict(entry.params)
        params["retry_seed"] = entry.retry_count * 1000 + hash(str(entry.id)) % 1000
        return params

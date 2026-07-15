"""
Phase 8 — Voice RetryEngineService.
Identical state machine as Phase 7's animation RetryEngineService:
  enqueue → mark_retrying → mark_resolved / mark_exhausted / mark_failed_retry
"""
from __future__ import annotations

import uuid
from datetime import datetime, timedelta, timezone
from typing import Any

from database.models.voice_engine import VoiceRetryQueue
from repositories.voice_engine_repository import VoiceRetryQueueRepository

# Exponential back-off delays (seconds): attempt 1→30s, 2→60s, 3→120s, …
_BACKOFF_BASE = 30


class VoiceRetryEngineService:
    def __init__(self, repo: VoiceRetryQueueRepository) -> None:
        self._repo = repo

    async def enqueue(
        self,
        *,
        project_id: uuid.UUID,
        reason: str = "",
        scene_id: uuid.UUID | None = None,
        episode_id: uuid.UUID | None = None,
        original_job_id: uuid.UUID | None = None,
        params: dict[str, Any] | None = None,
        max_retries: int = 3,
    ) -> VoiceRetryQueue:
        entry = VoiceRetryQueue(
            project_id=project_id,
            scene_id=scene_id,
            episode_id=episode_id,
            original_job_id=original_job_id,
            status="pending",
            retry_count=0,
            max_retries=max_retries,
            reason=reason,
            params=params or {},
        )
        return await self._repo.create(entry)

    async def mark_retrying(self, entry: VoiceRetryQueue) -> VoiceRetryQueue:
        entry.status = "retrying"
        entry.retry_count += 1
        entry.next_retry_at = None
        await self._repo._session.flush()
        return entry

    async def mark_failed_retry(
        self, entry: VoiceRetryQueue, reason: str = ""
    ) -> VoiceRetryQueue:
        """
        Called when a retry attempt fails but retry_count < max_retries.
        Transitions entry back to 'pending' with an exponential back-off delay
        so get_pending() will pick it up on the next scheduled sweep.
        """
        delay = _BACKOFF_BASE * (2 ** (entry.retry_count - 1))
        entry.status = "pending"
        entry.next_retry_at = datetime.now(timezone.utc) + timedelta(seconds=delay)
        if reason:
            entry.reason = reason
        await self._repo._session.flush()
        return entry

    async def mark_resolved(self, entry: VoiceRetryQueue) -> VoiceRetryQueue:
        entry.status = "resolved"
        await self._repo._session.flush()
        return entry

    async def mark_exhausted(self, entry: VoiceRetryQueue) -> VoiceRetryQueue:
        entry.status = "exhausted"
        await self._repo._session.flush()
        return entry

    async def get_pending(
        self, project_id: uuid.UUID, limit: int = 10
    ) -> list[VoiceRetryQueue]:
        return await self._repo.get_pending(project_id, limit)

    def get_retry_params(self, entry: VoiceRetryQueue) -> dict[str, Any]:
        """
        Return entry.params augmented with a deterministic retry seed so the
        provider produces a slightly different attempt each time.
        """
        seed = hash(f"{entry.id}:{entry.retry_count}") & 0xFFFFFFFF
        return {**entry.params, "retry_seed": seed, "retry_count": entry.retry_count}

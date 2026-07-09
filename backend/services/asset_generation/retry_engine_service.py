"""
Phase 6 — Retry Engine Service.

Processes the retry queue:
  - Selects pending retry entries
  - Regenerates prompts with adjustments
  - Re-triggers generation and evaluation
  - Marks exhausted entries as failed
"""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Any
from uuid import UUID

from database.models.asset_generation import RetryQueue
from repositories.asset_generation_repository import (
    AssetRepository,
    RetryQueueRepository,
)


# Prompt adjustments to apply on retry based on failure reason
_RETRY_ADJUSTMENTS: dict[str, dict[str, Any]] = {
    "low_quality": {"steps": 30, "cfg_scale": 8.0},
    "wrong_character": {"cfg_scale": 9.0, "steps": 25},
    "wrong_background": {"cfg_scale": 7.5, "steps": 28},
    "artifacts": {"steps": 35, "cfg_scale": 6.5},
    "wrong_pose": {"cfg_scale": 8.5, "steps": 25},
    "wrong_style": {"cfg_scale": 9.0, "steps": 30},
    "wrong_camera": {"cfg_scale": 7.0, "steps": 25},
    "score_below_threshold": {"steps": 30, "cfg_scale": 7.5},
}


class RetryEngineService:
    """Processes the retry queue and re-triggers generation."""

    def __init__(
        self,
        retry_repo: RetryQueueRepository,
        asset_repo: AssetRepository,
    ) -> None:
        self._retry_repo = retry_repo
        self._asset_repo = asset_repo

    async def get_retry_params(self, entry: RetryQueue) -> dict[str, Any]:
        """Return adjusted generation params for a retry attempt."""
        adjustments = _RETRY_ADJUSTMENTS.get(entry.failure_reason, {})
        base = dict(entry.retry_params)
        base.update(adjustments)
        # vary the seed on each retry to avoid identical output
        base["seed"] = entry.retry_count * 1000 + hash(str(entry.asset_id)) % 10000
        return base

    async def mark_retrying(self, entry: RetryQueue) -> None:
        entry.status = "retrying"
        entry.last_retry_at = datetime.now(timezone.utc)
        entry.retry_count += 1
        await self._retry_repo._session.flush()

    async def mark_resolved(self, entry: RetryQueue) -> None:
        entry.status = "resolved"
        entry.resolved_at = datetime.now(timezone.utc)
        await self._retry_repo._session.flush()

    async def mark_exhausted(self, entry: RetryQueue) -> None:
        entry.status = "exhausted"
        await self._retry_repo._session.flush()
        asset = await self._asset_repo.get_by_id(entry.asset_id)
        if asset:
            asset.status = "failed"
            await self._asset_repo._session.flush()

    async def process_pending(self, project_id: UUID, limit: int = 10) -> dict[str, Any]:
        """Return pending retry entries for processing by the caller."""
        entries = await self._retry_repo.get_pending(project_id, limit=limit)
        return {
            "project_id": str(project_id),
            "pending_count": len(entries),
            "entries": [
                {
                    "id": str(e.id),
                    "asset_id": str(e.asset_id),
                    "failure_reason": e.failure_reason,
                    "retry_count": e.retry_count,
                    "max_retries": e.max_retries,
                }
                for e in entries
            ],
        }

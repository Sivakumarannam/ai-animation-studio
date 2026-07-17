"""
Phase 9 — Music Engine repositories.
MusicJobRepository, MusicOutputRepository, SFXAssetRepository, MusicRetryQueueRepository.
Mirrors animation_engine_repository.py / voice_engine_repository.py exactly.
"""
from __future__ import annotations

import uuid
from datetime import datetime, timezone

from sqlalchemy import func, select

from database.models.music_engine import (
    MusicGenerationJob,
    MusicOutput,
    MusicRetryQueue,
    SoundEffectAsset,
)
from packages.utils.pagination import PaginatedResult, PaginationParams
from repositories.base import BaseRepository


# ---------------------------------------------------------------------------
# MusicJobRepository
# ---------------------------------------------------------------------------

class MusicJobRepository(BaseRepository[MusicGenerationJob]):
    model = MusicGenerationJob

    async def get_paginated(
        self,
        project_id: uuid.UUID,
        pagination: PaginationParams,
        *,
        status: str | None = None,
        job_type: str | None = None,
    ) -> PaginatedResult[MusicGenerationJob]:
        q = select(MusicGenerationJob).where(MusicGenerationJob.project_id == project_id)
        if status:
            q = q.where(MusicGenerationJob.status == status)
        if job_type:
            q = q.where(MusicGenerationJob.job_type == job_type)

        count_q = select(func.count()).select_from(q.subquery())
        total = (await self._session.execute(count_q)).scalar_one()

        offset = (pagination.page - 1) * pagination.page_size
        rows = (
            await self._session.execute(
                q.order_by(MusicGenerationJob.created_at.desc())
                .offset(offset)
                .limit(pagination.page_size)
            )
        ).scalars().all()

        return PaginatedResult(
            items=list(rows),
            total=total,
            page=pagination.page,
            page_size=pagination.page_size,
        )

    async def get_recent(self, project_id: uuid.UUID, limit: int = 5) -> list[MusicGenerationJob]:
        rows = (
            await self._session.execute(
                select(MusicGenerationJob)
                .where(MusicGenerationJob.project_id == project_id)
                .order_by(MusicGenerationJob.created_at.desc())
                .limit(limit)
            )
        ).scalars().all()
        return list(rows)

    async def count_by_status(self, project_id: uuid.UUID) -> dict[str, int]:
        result = await self._session.execute(
            select(MusicGenerationJob.status, func.count(MusicGenerationJob.id))
            .where(MusicGenerationJob.project_id == project_id)
            .group_by(MusicGenerationJob.status)
        )
        return {row[0]: row[1] for row in result.all()}


# ---------------------------------------------------------------------------
# MusicOutputRepository
# ---------------------------------------------------------------------------

class MusicOutputRepository(BaseRepository[MusicOutput]):
    model = MusicOutput

    async def get_paginated(
        self,
        project_id: uuid.UUID,
        pagination: PaginationParams,
        *,
        mood: str | None = None,
        output_type: str | None = None,
        status: str | None = None,
    ) -> PaginatedResult[MusicOutput]:
        q = select(MusicOutput).where(MusicOutput.project_id == project_id)
        if mood:
            q = q.where(MusicOutput.mood == mood)
        if output_type:
            q = q.where(MusicOutput.output_type == output_type)
        if status:
            q = q.where(MusicOutput.status == status)

        count_q = select(func.count()).select_from(q.subquery())
        total = (await self._session.execute(count_q)).scalar_one()

        offset = (pagination.page - 1) * pagination.page_size
        rows = (
            await self._session.execute(
                q.order_by(MusicOutput.created_at.desc())
                .offset(offset)
                .limit(pagination.page_size)
            )
        ).scalars().all()

        return PaginatedResult(
            items=list(rows),
            total=total,
            page=pagination.page,
            page_size=pagination.page_size,
        )

    async def count_by_project(self, project_id: uuid.UUID) -> int:
        result = await self._session.execute(
            select(func.count(MusicOutput.id)).where(MusicOutput.project_id == project_id)
        )
        return result.scalar_one()


# ---------------------------------------------------------------------------
# SFXAssetRepository
# ---------------------------------------------------------------------------

class SFXAssetRepository(BaseRepository[SoundEffectAsset]):
    model = SoundEffectAsset

    async def get_paginated(
        self,
        pagination: PaginationParams,
        *,
        category: str | None = None,
        search: str | None = None,
    ) -> PaginatedResult[SoundEffectAsset]:
        q = select(SoundEffectAsset).where(SoundEffectAsset.is_active == True)  # noqa: E712
        if category:
            q = q.where(SoundEffectAsset.category == category)
        if search:
            q = q.where(SoundEffectAsset.name.ilike(f"%{search}%"))

        count_q = select(func.count()).select_from(q.subquery())
        total = (await self._session.execute(count_q)).scalar_one()

        offset = (pagination.page - 1) * pagination.page_size
        rows = (
            await self._session.execute(
                q.order_by(SoundEffectAsset.category, SoundEffectAsset.name)
                .offset(offset)
                .limit(pagination.page_size)
            )
        ).scalars().all()

        return PaginatedResult(
            items=list(rows),
            total=total,
            page=pagination.page,
            page_size=pagination.page_size,
        )

    async def get_by_key(self, sfx_key: str) -> SoundEffectAsset | None:
        result = await self._session.execute(
            select(SoundEffectAsset).where(SoundEffectAsset.sfx_key == sfx_key)
        )
        return result.scalars().first()

    async def count_active(self) -> int:
        result = await self._session.execute(
            select(func.count(SoundEffectAsset.id)).where(SoundEffectAsset.is_active == True)  # noqa: E712
        )
        return result.scalar_one()


# ---------------------------------------------------------------------------
# MusicRetryQueueRepository
# ---------------------------------------------------------------------------

class MusicRetryQueueRepository(BaseRepository[MusicRetryQueue]):
    model = MusicRetryQueue

    async def get_pending(self, project_id: uuid.UUID, limit: int = 10) -> list[MusicRetryQueue]:
        now = datetime.now(timezone.utc)
        rows = (
            await self._session.execute(
                select(MusicRetryQueue)
                .where(MusicRetryQueue.project_id == project_id)
                .where(MusicRetryQueue.status == "pending")
                .where(
                    (MusicRetryQueue.next_retry_at == None)  # noqa: E711
                    | (MusicRetryQueue.next_retry_at <= now)
                )
                .order_by(MusicRetryQueue.created_at.asc())
                .limit(limit)
            )
        ).scalars().all()
        return list(rows)

    async def get_paginated(
        self,
        project_id: uuid.UUID,
        pagination: PaginationParams,
        *,
        status: str | None = None,
    ) -> PaginatedResult[MusicRetryQueue]:
        q = select(MusicRetryQueue).where(MusicRetryQueue.project_id == project_id)
        if status:
            q = q.where(MusicRetryQueue.status == status)

        count_q = select(func.count()).select_from(q.subquery())
        total = (await self._session.execute(count_q)).scalar_one()

        offset = (pagination.page - 1) * pagination.page_size
        rows = (
            await self._session.execute(
                q.order_by(MusicRetryQueue.created_at.desc())
                .offset(offset)
                .limit(pagination.page_size)
            )
        ).scalars().all()

        return PaginatedResult(
            items=list(rows),
            total=total,
            page=pagination.page,
            page_size=pagination.page_size,
        )

    async def count_by_project(self, project_id: uuid.UUID) -> int:
        result = await self._session.execute(
            select(func.count(MusicRetryQueue.id)).where(MusicRetryQueue.project_id == project_id)
        )
        return result.scalar_one()

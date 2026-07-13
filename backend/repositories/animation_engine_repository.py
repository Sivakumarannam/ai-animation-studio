"""
Phase 7 — Animation Engine repositories.
AnimationJobRepository, AnimationRenderOutputRepository, AnimationRetryQueueRepository.
"""
from __future__ import annotations

from datetime import datetime, timezone
from uuid import UUID

from sqlalchemy import func, select

from database.models.animation_engine import (
    AnimationJob,
    AnimationRenderOutput,
    AnimationRetryQueue,
)
from packages.utils.pagination import PaginatedResult, PaginationParams
from repositories.base import BaseRepository


# ---------------------------------------------------------------------------
# AnimationJob Repository
# ---------------------------------------------------------------------------

class AnimationJobRepository(BaseRepository[AnimationJob]):
    model = AnimationJob

    async def get_by_project(
        self,
        project_id: UUID,
        pagination: PaginationParams,
        status: str | None = None,
        job_type: str | None = None,
    ) -> PaginatedResult[AnimationJob]:
        stmt = select(AnimationJob).where(AnimationJob.project_id == project_id)
        if status:
            stmt = stmt.where(AnimationJob.status == status)
        if job_type:
            stmt = stmt.where(AnimationJob.job_type == job_type)

        count_stmt = select(func.count()).select_from(stmt.subquery())
        total = (await self._session.execute(count_stmt)).scalar_one()

        stmt = stmt.order_by(AnimationJob.created_at.desc())
        stmt = stmt.offset(pagination.offset).limit(pagination.limit)
        items = list((await self._session.execute(stmt)).scalars().all())
        return PaginatedResult(items=items, total=total, page=pagination.page, page_size=pagination.page_size)

    async def get_recent(self, project_id: UUID, limit: int = 5) -> list[AnimationJob]:
        result = await self._session.execute(
            select(AnimationJob)
            .where(AnimationJob.project_id == project_id)
            .order_by(AnimationJob.created_at.desc())
            .limit(limit)
        )
        return list(result.scalars().all())

    async def count_by_status(self, project_id: UUID) -> dict[str, int]:
        result = await self._session.execute(
            select(AnimationJob.status, func.count(AnimationJob.id))
            .where(AnimationJob.project_id == project_id)
            .group_by(AnimationJob.status)
        )
        return {row[0]: row[1] for row in result.all()}


# ---------------------------------------------------------------------------
# AnimationRenderOutput Repository
# ---------------------------------------------------------------------------

class AnimationRenderOutputRepository(BaseRepository[AnimationRenderOutput]):
    model = AnimationRenderOutput

    async def get_by_project(
        self,
        project_id: UUID,
        pagination: PaginationParams,
        output_type: str | None = None,
        status: str | None = None,
    ) -> PaginatedResult[AnimationRenderOutput]:
        stmt = select(AnimationRenderOutput).where(AnimationRenderOutput.project_id == project_id)
        if output_type:
            stmt = stmt.where(AnimationRenderOutput.output_type == output_type)
        if status:
            stmt = stmt.where(AnimationRenderOutput.status == status)

        count_stmt = select(func.count()).select_from(stmt.subquery())
        total = (await self._session.execute(count_stmt)).scalar_one()

        stmt = stmt.order_by(AnimationRenderOutput.created_at.desc())
        stmt = stmt.offset(pagination.offset).limit(pagination.limit)
        items = list((await self._session.execute(stmt)).scalars().all())
        return PaginatedResult(items=items, total=total, page=pagination.page, page_size=pagination.page_size)

    async def get_by_job(self, job_id: UUID) -> list[AnimationRenderOutput]:
        result = await self._session.execute(
            select(AnimationRenderOutput)
            .where(AnimationRenderOutput.job_id == job_id)
            .order_by(AnimationRenderOutput.created_at.desc())
        )
        return list(result.scalars().all())

    async def get_by_scene(self, scene_id: UUID) -> list[AnimationRenderOutput]:
        result = await self._session.execute(
            select(AnimationRenderOutput)
            .where(AnimationRenderOutput.scene_id == scene_id)
            .where(AnimationRenderOutput.status == "completed")
            .order_by(AnimationRenderOutput.created_at.desc())
        )
        return list(result.scalars().all())

    async def count_by_project(self, project_id: UUID) -> int:
        result = await self._session.execute(
            select(func.count(AnimationRenderOutput.id))
            .where(AnimationRenderOutput.project_id == project_id)
        )
        return result.scalar_one()


# ---------------------------------------------------------------------------
# AnimationRetryQueue Repository
# ---------------------------------------------------------------------------

class AnimationRetryQueueRepository(BaseRepository[AnimationRetryQueue]):
    model = AnimationRetryQueue

    async def get_paginated(
        self,
        project_id: UUID,
        pagination: PaginationParams,
        status: str | None = None,
    ) -> PaginatedResult[AnimationRetryQueue]:
        stmt = select(AnimationRetryQueue).where(AnimationRetryQueue.project_id == project_id)
        if status:
            stmt = stmt.where(AnimationRetryQueue.status == status)

        count_stmt = select(func.count()).select_from(stmt.subquery())
        total = (await self._session.execute(count_stmt)).scalar_one()

        stmt = stmt.order_by(AnimationRetryQueue.created_at.desc())
        stmt = stmt.offset(pagination.offset).limit(pagination.limit)
        items = list((await self._session.execute(stmt)).scalars().all())
        return PaginatedResult(items=items, total=total, page=pagination.page, page_size=pagination.page_size)

    async def get_pending(self, project_id: UUID, limit: int = 10) -> list[AnimationRetryQueue]:
        result = await self._session.execute(
            select(AnimationRetryQueue)
            .where(AnimationRetryQueue.project_id == project_id)
            .where(AnimationRetryQueue.status == "pending")
            .order_by(AnimationRetryQueue.created_at.asc())
            .limit(limit)
        )
        return list(result.scalars().all())

    async def count_by_project(self, project_id: UUID) -> int:
        result = await self._session.execute(
            select(func.count(AnimationRetryQueue.id))
            .where(AnimationRetryQueue.project_id == project_id)
            .where(AnimationRetryQueue.status.in_(["pending", "retrying"]))
        )
        return result.scalar_one()

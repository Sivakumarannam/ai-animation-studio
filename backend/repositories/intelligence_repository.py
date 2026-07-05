"""
Phase 3 — Story Intelligence repositories.
Each class extends BaseRepository and adds domain-specific queries.
"""
from __future__ import annotations

from typing import Any
from uuid import UUID

from sqlalchemy import desc, select

from database.models.intelligence import (
    Episode,
    GenerationJob,
    GenerationLog,
    RetryQueue,
    Season,
    StoryEvaluation,
    StoryIdea,
    StoryMemory,
    StoryScene,
    StoryVersion,
    World,
)
from packages.utils.pagination import PaginatedResult, PaginationParams
from repositories.base import BaseRepository


# ---------------------------------------------------------------------------
# World
# ---------------------------------------------------------------------------

class WorldRepository(BaseRepository[World]):
    model = World

    async def get_by_project(
        self, project_id: UUID, pagination: PaginationParams
    ) -> PaginatedResult[World]:
        return await self.get_all(pagination, filters={"project_id": project_id})

    async def get_active_by_project(
        self, project_id: UUID, pagination: PaginationParams
    ) -> PaginatedResult[World]:
        from sqlalchemy import func, select
        stmt = (
            select(World)
            .where(World.project_id == project_id, World.status == "active")
        )
        count_stmt = select(func.count()).select_from(stmt.subquery())
        total = (await self._session.execute(count_stmt)).scalar_one()
        stmt = stmt.offset(pagination.offset).limit(pagination.limit)
        items = list((await self._session.execute(stmt)).scalars().all())
        return PaginatedResult(items=items, total=total, page=pagination.page, page_size=pagination.page_size)


# ---------------------------------------------------------------------------
# Season
# ---------------------------------------------------------------------------

class SeasonRepository(BaseRepository[Season]):
    model = Season

    async def get_by_world(
        self, world_id: UUID, pagination: PaginationParams
    ) -> PaginatedResult[Season]:
        return await self.get_all(pagination, filters={"world_id": world_id})

    async def get_next_season_number(self, world_id: UUID) -> int:
        from sqlalchemy import func
        stmt = select(func.max(Season.season_number)).where(Season.world_id == world_id)
        result = await self._session.execute(stmt)
        max_num = result.scalar_one_or_none()
        return (max_num or 0) + 1


# ---------------------------------------------------------------------------
# Episode
# ---------------------------------------------------------------------------

class EpisodeRepository(BaseRepository[Episode]):
    model = Episode

    async def get_by_season(
        self, season_id: UUID, pagination: PaginationParams
    ) -> PaginatedResult[Episode]:
        return await self.get_all(pagination, filters={"season_id": season_id})

    async def get_by_world(
        self, world_id: UUID, pagination: PaginationParams
    ) -> PaginatedResult[Episode]:
        return await self.get_all(pagination, filters={"world_id": world_id})

    async def get_by_project(
        self, project_id: UUID, pagination: PaginationParams,
        status: str | None = None
    ) -> PaginatedResult[Episode]:
        from sqlalchemy import func
        stmt = select(Episode).where(Episode.project_id == project_id)
        if status:
            stmt = stmt.where(Episode.status == status)
        count_stmt = select(func.count()).select_from(stmt.subquery())
        total = (await self._session.execute(count_stmt)).scalar_one()
        stmt = stmt.order_by(Episode.season_id, Episode.episode_number).offset(pagination.offset).limit(pagination.limit)
        items = list((await self._session.execute(stmt)).scalars().all())
        return PaginatedResult(items=items, total=total, page=pagination.page, page_size=pagination.page_size)

    async def get_next_episode_number(self, season_id: UUID) -> int:
        from sqlalchemy import func
        stmt = select(func.max(Episode.episode_number)).where(Episode.season_id == season_id)
        result = await self._session.execute(stmt)
        max_num = result.scalar_one_or_none()
        return (max_num or 0) + 1


# ---------------------------------------------------------------------------
# StoryScene
# ---------------------------------------------------------------------------

class StorySceneRepository(BaseRepository[StoryScene]):
    model = StoryScene

    async def get_by_episode(
        self, episode_id: UUID, pagination: PaginationParams
    ) -> PaginatedResult[StoryScene]:
        return await self.get_all(pagination, filters={"episode_id": episode_id})

    async def get_all_by_episode(self, episode_id: UUID) -> list[StoryScene]:
        stmt = (
            select(StoryScene)
            .where(StoryScene.episode_id == episode_id)
            .order_by(StoryScene.scene_number)
        )
        result = await self._session.execute(stmt)
        return list(result.scalars().all())


# ---------------------------------------------------------------------------
# StoryIdea
# ---------------------------------------------------------------------------

class StoryIdeaRepository(BaseRepository[StoryIdea]):
    model = StoryIdea

    async def get_by_project(
        self, project_id: UUID, pagination: PaginationParams,
        status: str | None = None
    ) -> PaginatedResult[StoryIdea]:
        from sqlalchemy import func
        stmt = select(StoryIdea).where(StoryIdea.project_id == project_id)
        if status:
            stmt = stmt.where(StoryIdea.status == status)
        count_stmt = select(func.count()).select_from(stmt.subquery())
        total = (await self._session.execute(count_stmt)).scalar_one()
        stmt = stmt.order_by(desc(StoryIdea.created_at)).offset(pagination.offset).limit(pagination.limit)
        items = list((await self._session.execute(stmt)).scalars().all())
        return PaginatedResult(items=items, total=total, page=pagination.page, page_size=pagination.page_size)


# ---------------------------------------------------------------------------
# StoryMemory
# ---------------------------------------------------------------------------

class StoryMemoryRepository(BaseRepository[StoryMemory]):
    model = StoryMemory

    async def get_by_world(
        self, world_id: UUID, pagination: PaginationParams,
        memory_type: str | None = None,
    ) -> PaginatedResult[StoryMemory]:
        from sqlalchemy import func
        stmt = select(StoryMemory).where(
            StoryMemory.world_id == world_id, StoryMemory.is_active == True  # noqa: E712
        )
        if memory_type:
            stmt = stmt.where(StoryMemory.memory_type == memory_type)
        count_stmt = select(func.count()).select_from(stmt.subquery())
        total = (await self._session.execute(count_stmt)).scalar_one()
        stmt = stmt.offset(pagination.offset).limit(pagination.limit)
        items = list((await self._session.execute(stmt)).scalars().all())
        return PaginatedResult(items=items, total=total, page=pagination.page, page_size=pagination.page_size)

    async def get_by_key(self, world_id: UUID, key: str) -> StoryMemory | None:
        stmt = select(StoryMemory).where(
            StoryMemory.world_id == world_id, StoryMemory.key == key, StoryMemory.is_active == True  # noqa: E712
        )
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def upsert(self, world_id: UUID, memory_type: str, key: str, value: dict[str, Any]) -> StoryMemory:
        existing = await self.get_by_key(world_id, key)
        if existing:
            return await self.update(existing, {"value": value, "memory_type": memory_type})
        new_mem = StoryMemory(world_id=world_id, memory_type=memory_type, key=key, value=value)
        return await self.create(new_mem)


# ---------------------------------------------------------------------------
# StoryEvaluation
# ---------------------------------------------------------------------------

class StoryEvaluationRepository(BaseRepository[StoryEvaluation]):
    model = StoryEvaluation

    async def get_latest_for_episode(self, episode_id: UUID) -> StoryEvaluation | None:
        stmt = (
            select(StoryEvaluation)
            .where(StoryEvaluation.episode_id == episode_id)
            .order_by(desc(StoryEvaluation.evaluated_at))
            .limit(1)
        )
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_by_episode(self, episode_id: UUID) -> list[StoryEvaluation]:
        stmt = (
            select(StoryEvaluation)
            .where(StoryEvaluation.episode_id == episode_id)
            .order_by(desc(StoryEvaluation.evaluated_at))
        )
        result = await self._session.execute(stmt)
        return list(result.scalars().all())


# ---------------------------------------------------------------------------
# GenerationJob
# ---------------------------------------------------------------------------

class GenerationJobRepository(BaseRepository[GenerationJob]):
    model = GenerationJob

    async def get_by_project(
        self, project_id: UUID, pagination: PaginationParams,
        status: str | None = None, job_type: str | None = None,
    ) -> PaginatedResult[GenerationJob]:
        from sqlalchemy import func
        stmt = select(GenerationJob).where(GenerationJob.project_id == project_id)
        if status:
            stmt = stmt.where(GenerationJob.status == status)
        if job_type:
            stmt = stmt.where(GenerationJob.job_type == job_type)
        count_stmt = select(func.count()).select_from(stmt.subquery())
        total = (await self._session.execute(count_stmt)).scalar_one()
        stmt = stmt.order_by(desc(GenerationJob.created_at)).offset(pagination.offset).limit(pagination.limit)
        items = list((await self._session.execute(stmt)).scalars().all())
        return PaginatedResult(items=items, total=total, page=pagination.page, page_size=pagination.page_size)

    async def get_pending(self, limit: int = 50) -> list[GenerationJob]:
        stmt = (
            select(GenerationJob)
            .where(GenerationJob.status.in_(["pending", "retrying"]))
            .order_by(GenerationJob.created_at)
            .limit(limit)
        )
        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    async def count_by_status(self) -> dict[str, int]:
        from sqlalchemy import func
        stmt = select(GenerationJob.status, func.count(GenerationJob.id)).group_by(GenerationJob.status)
        result = await self._session.execute(stmt)
        return {row[0]: row[1] for row in result.all()}


# ---------------------------------------------------------------------------
# GenerationLog
# ---------------------------------------------------------------------------

class GenerationLogRepository(BaseRepository[GenerationLog]):
    model = GenerationLog

    async def get_by_job(self, job_id: UUID) -> list[GenerationLog]:
        stmt = (
            select(GenerationLog)
            .where(GenerationLog.job_id == job_id)
            .order_by(GenerationLog.created_at)
        )
        result = await self._session.execute(stmt)
        return list(result.scalars().all())


# ---------------------------------------------------------------------------
# RetryQueue
# ---------------------------------------------------------------------------

class RetryQueueRepository(BaseRepository[RetryQueue]):
    model = RetryQueue

    async def get_pending(self, limit: int = 20) -> list[RetryQueue]:
        stmt = (
            select(RetryQueue)
            .where(RetryQueue.status == "pending")
            .order_by(RetryQueue.scheduled_at)
            .limit(limit)
        )
        result = await self._session.execute(stmt)
        return list(result.scalars().all())


# ---------------------------------------------------------------------------
# StoryVersion
# ---------------------------------------------------------------------------

class StoryVersionRepository(BaseRepository[StoryVersion]):
    model = StoryVersion

    async def get_for_entity(
        self, entity_type: str, entity_id: UUID
    ) -> list[StoryVersion]:
        stmt = (
            select(StoryVersion)
            .where(StoryVersion.entity_type == entity_type, StoryVersion.entity_id == entity_id)
            .order_by(desc(StoryVersion.version_number))
        )
        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    async def get_next_version_number(self, entity_type: str, entity_id: UUID) -> int:
        from sqlalchemy import func
        stmt = select(func.max(StoryVersion.version_number)).where(
            StoryVersion.entity_type == entity_type,
            StoryVersion.entity_id == entity_id,
        )
        result = await self._session.execute(stmt)
        max_v = result.scalar_one_or_none()
        return (max_v or 0) + 1

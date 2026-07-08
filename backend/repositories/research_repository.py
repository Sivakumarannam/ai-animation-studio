"""
Phase 5 — Research & Trend Intelligence Engine repositories.
"""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Any
from uuid import UUID

from sqlalchemy import func, select, update, and_
from sqlalchemy.ext.asyncio import AsyncSession

from database.models.research import (
    ResearchAnalytics,
    ResearchArticle,
    ResearchCluster,
    ResearchEntity,
    ResearchFact,
    ResearchHistory,
    ResearchJob,
    ResearchMemory,
    ResearchQueue,
    ResearchScore,
    ResearchSource,
    ResearchTopic,
    ResearchTrend,
    ResearchVersion,
)
from packages.utils.pagination import PaginatedResult, PaginationParams
from repositories.base import BaseRepository


# ---------------------------------------------------------------------------
# ResearchSourceRepository
# ---------------------------------------------------------------------------

class ResearchSourceRepository(BaseRepository[ResearchSource]):
    model = ResearchSource

    async def get_active_sources(self, source_type: str | None = None) -> list[ResearchSource]:
        stmt = select(self.model).where(self.model.is_active.is_(True))
        if source_type:
            stmt = stmt.where(self.model.source_type == source_type)
        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    async def get_due_sources(self) -> list[ResearchSource]:
        """Return active sources whose next fetch is due."""
        now = datetime.now(timezone.utc)
        stmt = select(self.model).where(
            self.model.is_active.is_(True)
        )
        result = await self._session.execute(stmt)
        return list(result.scalars().all())


# ---------------------------------------------------------------------------
# ResearchTrendRepository
# ---------------------------------------------------------------------------

class ResearchTrendRepository(BaseRepository[ResearchTrend]):
    model = ResearchTrend

    async def get_active_trends(
        self,
        pagination: PaginationParams,
        category: str | None = None,
        emerging_only: bool = False,
    ) -> PaginatedResult[ResearchTrend]:
        stmt = select(self.model).where(self.model.status == "active")
        if category:
            stmt = stmt.where(self.model.category == category)
        if emerging_only:
            stmt = stmt.where(self.model.is_emerging.is_(True))
        stmt = stmt.order_by(self.model.trend_score.desc())

        count_stmt = select(func.count()).select_from(stmt.subquery())
        total = (await self._session.execute(count_stmt)).scalar_one()
        stmt = stmt.offset(pagination.offset).limit(pagination.limit)
        items = list((await self._session.execute(stmt)).scalars().all())
        return PaginatedResult(items=items, total=total, page=pagination.page, page_size=pagination.page_size)

    async def get_by_keyword(self, normalized_keyword: str) -> ResearchTrend | None:
        stmt = select(self.model).where(
            self.model.normalized_keyword == normalized_keyword,
            self.model.status == "active",
        )
        result = await self._session.execute(stmt)
        return result.scalars().first()

    async def get_top_trends(self, limit: int = 10) -> list[ResearchTrend]:
        stmt = (
            select(self.model)
            .where(self.model.status == "active")
            .order_by(self.model.trend_score.desc())
            .limit(limit)
        )
        result = await self._session.execute(stmt)
        return list(result.scalars().all())


# ---------------------------------------------------------------------------
# ResearchTopicRepository
# ---------------------------------------------------------------------------

class ResearchTopicRepository(BaseRepository[ResearchTopic]):
    model = ResearchTopic

    async def get_by_slug(self, slug: str) -> ResearchTopic | None:
        stmt = select(self.model).where(self.model.slug == slug)
        result = await self._session.execute(stmt)
        return result.scalars().first()

    async def get_by_status(
        self,
        status: str,
        pagination: PaginationParams,
    ) -> PaginatedResult[ResearchTopic]:
        stmt = select(self.model).where(self.model.status == status).order_by(
            self.model.opportunity_score.desc()
        )
        count_stmt = select(func.count()).select_from(stmt.subquery())
        total = (await self._session.execute(count_stmt)).scalar_one()
        stmt = stmt.offset(pagination.offset).limit(pagination.limit)
        items = list((await self._session.execute(stmt)).scalars().all())
        return PaginatedResult(items=items, total=total, page=pagination.page, page_size=pagination.page_size)

    async def get_pending_research(self, limit: int = 10) -> list[ResearchTopic]:
        stmt = (
            select(self.model)
            .where(
                self.model.research_status == "pending",
                self.model.status != "rejected",
            )
            .order_by(self.model.trend_score.desc())
            .limit(limit)
        )
        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    async def get_top_opportunities(self, limit: int = 20) -> list[ResearchTopic]:
        stmt = (
            select(self.model)
            .where(self.model.status == "researched")
            .order_by(self.model.opportunity_score.desc())
            .limit(limit)
        )
        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    async def get_all_paginated(
        self,
        pagination: PaginationParams,
        status: str | None = None,
        research_status: str | None = None,
    ) -> PaginatedResult[ResearchTopic]:
        stmt = select(self.model)
        if status:
            stmt = stmt.where(self.model.status == status)
        if research_status:
            stmt = stmt.where(self.model.research_status == research_status)
        stmt = stmt.order_by(self.model.opportunity_score.desc())

        count_stmt = select(func.count()).select_from(stmt.subquery())
        total = (await self._session.execute(count_stmt)).scalar_one()
        stmt = stmt.offset(pagination.offset).limit(pagination.limit)
        items = list((await self._session.execute(stmt)).scalars().all())
        return PaginatedResult(items=items, total=total, page=pagination.page, page_size=pagination.page_size)

    async def count_by_status(self) -> dict[str, int]:
        stmt = select(self.model.status, func.count()).group_by(self.model.status)
        result = await self._session.execute(stmt)
        return {row[0]: row[1] for row in result.all()}


# ---------------------------------------------------------------------------
# ResearchClusterRepository
# ---------------------------------------------------------------------------

class ResearchClusterRepository(BaseRepository[ResearchCluster]):
    model = ResearchCluster

    async def get_active_clusters(
        self, pagination: PaginationParams
    ) -> PaginatedResult[ResearchCluster]:
        stmt = (
            select(self.model)
            .where(self.model.status == "active")
            .order_by(self.model.avg_opportunity_score.desc())
        )
        count_stmt = select(func.count()).select_from(stmt.subquery())
        total = (await self._session.execute(count_stmt)).scalar_one()
        stmt = stmt.offset(pagination.offset).limit(pagination.limit)
        items = list((await self._session.execute(stmt)).scalars().all())
        return PaginatedResult(items=items, total=total, page=pagination.page, page_size=pagination.page_size)


# ---------------------------------------------------------------------------
# ResearchArticleRepository
# ---------------------------------------------------------------------------

class ResearchArticleRepository(BaseRepository[ResearchArticle]):
    model = ResearchArticle

    async def get_by_topic(
        self,
        topic_id: UUID,
        pagination: PaginationParams,
        status: str | None = None,
    ) -> PaginatedResult[ResearchArticle]:
        stmt = select(self.model).where(self.model.topic_id == topic_id)
        if status:
            stmt = stmt.where(self.model.status == status)
        stmt = stmt.order_by(self.model.relevance_score.desc())

        count_stmt = select(func.count()).select_from(stmt.subquery())
        total = (await self._session.execute(count_stmt)).scalar_one()
        stmt = stmt.offset(pagination.offset).limit(pagination.limit)
        items = list((await self._session.execute(stmt)).scalars().all())
        return PaginatedResult(items=items, total=total, page=pagination.page, page_size=pagination.page_size)

    async def get_by_content_hash(self, content_hash: str) -> ResearchArticle | None:
        stmt = select(self.model).where(self.model.content_hash == content_hash)
        result = await self._session.execute(stmt)
        return result.scalars().first()


# ---------------------------------------------------------------------------
# ResearchFactRepository
# ---------------------------------------------------------------------------

class ResearchFactRepository(BaseRepository[ResearchFact]):
    model = ResearchFact

    async def get_by_topic(
        self,
        topic_id: UUID,
        pagination: PaginationParams,
        verified_only: bool = False,
    ) -> PaginatedResult[ResearchFact]:
        stmt = select(self.model).where(self.model.topic_id == topic_id)
        if verified_only:
            stmt = stmt.where(self.model.is_verified.is_(True))
        stmt = stmt.order_by(self.model.confidence.desc())

        count_stmt = select(func.count()).select_from(stmt.subquery())
        total = (await self._session.execute(count_stmt)).scalar_one()
        stmt = stmt.offset(pagination.offset).limit(pagination.limit)
        items = list((await self._session.execute(stmt)).scalars().all())
        return PaginatedResult(items=items, total=total, page=pagination.page, page_size=pagination.page_size)

    async def get_unverified(self, limit: int = 50) -> list[ResearchFact]:
        stmt = (
            select(self.model)
            .where(
                self.model.is_verified.is_(False),
                self.model.is_rejected.is_(False),
            )
            .order_by(self.model.confidence.desc())
            .limit(limit)
        )
        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    async def count_verified(self) -> int:
        stmt = select(func.count()).where(self.model.is_verified.is_(True))
        result = await self._session.execute(stmt)
        return result.scalar_one()


# ---------------------------------------------------------------------------
# ResearchEntityRepository
# ---------------------------------------------------------------------------

class ResearchEntityRepository(BaseRepository[ResearchEntity]):
    model = ResearchEntity

    async def get_by_topic(self, topic_id: UUID) -> list[ResearchEntity]:
        stmt = select(self.model).where(self.model.topic_id == topic_id)
        result = await self._session.execute(stmt)
        return list(result.scalars().all())


# ---------------------------------------------------------------------------
# ResearchScoreRepository
# ---------------------------------------------------------------------------

class ResearchScoreRepository(BaseRepository[ResearchScore]):
    model = ResearchScore

    async def get_by_topic(self, topic_id: UUID) -> ResearchScore | None:
        stmt = select(self.model).where(self.model.topic_id == topic_id)
        result = await self._session.execute(stmt)
        return result.scalars().first()

    async def get_top_scores(self, limit: int = 20) -> list[ResearchScore]:
        stmt = (
            select(self.model)
            .order_by(self.model.overall_score.desc())
            .limit(limit)
        )
        result = await self._session.execute(stmt)
        return list(result.scalars().all())


# ---------------------------------------------------------------------------
# ResearchQueueRepository
# ---------------------------------------------------------------------------

class ResearchQueueRepository(BaseRepository[ResearchQueue]):
    model = ResearchQueue

    async def get_pending(
        self, pagination: PaginationParams, project_id: UUID | None = None
    ) -> PaginatedResult[ResearchQueue]:
        stmt = select(self.model).where(self.model.status == "pending")
        if project_id:
            stmt = stmt.where(self.model.project_id == project_id)
        stmt = stmt.order_by(self.model.priority.desc(), self.model.overall_score.desc())

        count_stmt = select(func.count()).select_from(stmt.subquery())
        total = (await self._session.execute(count_stmt)).scalar_one()
        stmt = stmt.offset(pagination.offset).limit(pagination.limit)
        items = list((await self._session.execute(stmt)).scalars().all())
        return PaginatedResult(items=items, total=total, page=pagination.page, page_size=pagination.page_size)

    async def get_by_topic(self, topic_id: UUID) -> ResearchQueue | None:
        stmt = select(self.model).where(self.model.topic_id == topic_id)
        result = await self._session.execute(stmt)
        return result.scalars().first()

    async def get_all_paginated(
        self, pagination: PaginationParams, status: str | None = None
    ) -> PaginatedResult[ResearchQueue]:
        stmt = select(self.model)
        if status:
            stmt = stmt.where(self.model.status == status)
        stmt = stmt.order_by(self.model.priority.desc(), self.model.overall_score.desc())

        count_stmt = select(func.count()).select_from(stmt.subquery())
        total = (await self._session.execute(count_stmt)).scalar_one()
        stmt = stmt.offset(pagination.offset).limit(pagination.limit)
        items = list((await self._session.execute(stmt)).scalars().all())
        return PaginatedResult(items=items, total=total, page=pagination.page, page_size=pagination.page_size)


# ---------------------------------------------------------------------------
# ResearchJobRepository
# ---------------------------------------------------------------------------

class ResearchJobRepository(BaseRepository[ResearchJob]):
    model = ResearchJob

    async def get_pending_retries(self) -> list[ResearchJob]:
        stmt = (
            select(self.model)
            .where(
                self.model.status == "failed",
                self.model.retry_count < self.model.max_retries,
            )
            .order_by(self.model.created_at)
        )
        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    async def get_all_paginated(
        self, pagination: PaginationParams, status: str | None = None, job_type: str | None = None
    ) -> PaginatedResult[ResearchJob]:
        stmt = select(self.model)
        if status:
            stmt = stmt.where(self.model.status == status)
        if job_type:
            stmt = stmt.where(self.model.job_type == job_type)
        stmt = stmt.order_by(self.model.created_at.desc())

        count_stmt = select(func.count()).select_from(stmt.subquery())
        total = (await self._session.execute(count_stmt)).scalar_one()
        stmt = stmt.offset(pagination.offset).limit(pagination.limit)
        items = list((await self._session.execute(stmt)).scalars().all())
        return PaginatedResult(items=items, total=total, page=pagination.page, page_size=pagination.page_size)

    async def status_counts(self) -> dict[str, int]:
        stmt = select(self.model.status, func.count()).group_by(self.model.status)
        result = await self._session.execute(stmt)
        return {row[0]: row[1] for row in result.all()}


# ---------------------------------------------------------------------------
# ResearchHistoryRepository
# ---------------------------------------------------------------------------

class ResearchHistoryRepository(BaseRepository[ResearchHistory]):
    model = ResearchHistory

    async def get_recent(
        self, pagination: PaginationParams, run_type: str | None = None
    ) -> PaginatedResult[ResearchHistory]:
        stmt = select(self.model)
        if run_type:
            stmt = stmt.where(self.model.run_type == run_type)
        stmt = stmt.order_by(self.model.created_at.desc())

        count_stmt = select(func.count()).select_from(stmt.subquery())
        total = (await self._session.execute(count_stmt)).scalar_one()
        stmt = stmt.offset(pagination.offset).limit(pagination.limit)
        items = list((await self._session.execute(stmt)).scalars().all())
        return PaginatedResult(items=items, total=total, page=pagination.page, page_size=pagination.page_size)

    async def get_last_run(self, run_type: str) -> ResearchHistory | None:
        stmt = (
            select(self.model)
            .where(self.model.run_type == run_type)
            .order_by(self.model.created_at.desc())
            .limit(1)
        )
        result = await self._session.execute(stmt)
        return result.scalars().first()


# ---------------------------------------------------------------------------
# ResearchMemoryRepository
# ---------------------------------------------------------------------------

class ResearchMemoryRepository(BaseRepository[ResearchMemory]):
    model = ResearchMemory

    async def get_by_key(self, memory_type: str, key: str) -> ResearchMemory | None:
        stmt = select(self.model).where(
            self.model.memory_type == memory_type,
            self.model.key == key,
            self.model.is_active.is_(True),
        )
        result = await self._session.execute(stmt)
        return result.scalars().first()

    async def get_active_by_type(self, memory_type: str) -> list[ResearchMemory]:
        stmt = select(self.model).where(
            self.model.memory_type == memory_type,
            self.model.is_active.is_(True),
        )
        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    async def is_researched(self, key: str) -> bool:
        stmt = select(func.count()).where(
            self.model.memory_type == "researched_topic",
            self.model.key == key,
            self.model.is_active.is_(True),
        )
        result = await self._session.execute(stmt)
        return (result.scalar_one() or 0) > 0


# ---------------------------------------------------------------------------
# ResearchVersionRepository
# ---------------------------------------------------------------------------

class ResearchVersionRepository(BaseRepository[ResearchVersion]):
    model = ResearchVersion

    async def list_versions(
        self, entity_type: str, entity_id: UUID
    ) -> list[ResearchVersion]:
        stmt = (
            select(self.model)
            .where(
                self.model.entity_type == entity_type,
                self.model.entity_id == entity_id,
            )
            .order_by(self.model.version_number.desc())
        )
        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    async def next_version_number(self, entity_type: str, entity_id: UUID) -> int:
        stmt = select(func.max(self.model.version_number)).where(
            self.model.entity_type == entity_type,
            self.model.entity_id == entity_id,
        )
        result = await self._session.execute(stmt)
        current = result.scalar_one()
        return (current or 0) + 1


# ---------------------------------------------------------------------------
# ResearchAnalyticsRepository
# ---------------------------------------------------------------------------

class ResearchAnalyticsRepository(BaseRepository[ResearchAnalytics]):
    model = ResearchAnalytics

    async def get_recent(
        self, period_type: str = "daily", limit: int = 30
    ) -> list[ResearchAnalytics]:
        stmt = (
            select(self.model)
            .where(self.model.period_type == period_type)
            .order_by(self.model.period_start.desc())
            .limit(limit)
        )
        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    async def get_latest(self, period_type: str = "daily") -> ResearchAnalytics | None:
        stmt = (
            select(self.model)
            .where(self.model.period_type == period_type)
            .order_by(self.model.period_start.desc())
            .limit(1)
        )
        result = await self._session.execute(stmt)
        return result.scalars().first()

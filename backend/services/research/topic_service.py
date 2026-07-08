"""
Topic management service — creates, deduplicates, and clusters topics.
"""
from __future__ import annotations

import re
from typing import Any

import structlog

from database.models.research import ResearchCluster, ResearchTopic
from packages.utils.pagination import PaginatedResult, PaginationParams
from repositories.research_repository import (
    ResearchClusterRepository,
    ResearchMemoryRepository,
    ResearchTopicRepository,
    ResearchTrendRepository,
)

logger = structlog.get_logger()


def _slugify(text: str) -> str:
    text = text.lower().strip()
    text = re.sub(r"[^a-z0-9]+", "-", text)
    return text.strip("-")


class TopicService:
    def __init__(
        self,
        topic_repo: ResearchTopicRepository,
        cluster_repo: ResearchClusterRepository,
        trend_repo: ResearchTrendRepository,
        memory_repo: ResearchMemoryRepository,
    ) -> None:
        self._topic_repo = topic_repo
        self._cluster_repo = cluster_repo
        self._trend_repo = trend_repo
        self._memory_repo = memory_repo

    async def create_topics_from_trends(self) -> dict[str, Any]:
        """Convert active trends into normalised research topics."""
        trends = await self._trend_repo.get_top_trends(limit=50)
        created = 0
        skipped = 0
        for trend in trends:
            slug = _slugify(trend.keyword)
            existing = await self._topic_repo.get_by_slug(slug)
            if existing:
                skipped += 1
                continue
            # Check memory — skip if already researched
            if await self._memory_repo.is_researched(slug):
                skipped += 1
                continue
            topic = ResearchTopic(
                canonical_name=trend.keyword.title(),
                slug=slug,
                description=f"Topic discovered from trending keyword: {trend.keyword}",
                keywords=[trend.keyword, trend.normalized_keyword],
                categories=[trend.category],
                language=trend.language,
                status="discovered",
                research_status="pending",
                trend_score=trend.trend_score,
                source_trend_ids=[str(trend.id)],
            )
            await self._topic_repo.create(topic)
            created += 1

        logger.info("topics_from_trends", created=created, skipped=skipped)
        return {"created": created, "skipped": skipped}

    async def cluster_topics(self) -> dict[str, Any]:
        """Simple keyword-based topic clustering (no ML required)."""
        all_topics_result = await self._topic_repo.get_all_paginated(
            PaginationParams(page=1, page_size=100)
        )
        topics = all_topics_result.items

        # Group by primary category (simplified clustering)
        category_groups: dict[str, list[ResearchTopic]] = {}
        for topic in topics:
            cat = topic.categories[0] if topic.categories else "general"
            category_groups.setdefault(cat, []).append(topic)

        clusters_created = 0
        for cat, cat_topics in category_groups.items():
            if len(cat_topics) < 2:
                continue
            existing = await self._cluster_repo.get_all(PaginationParams(page=1, page_size=1), {"status": "active"})
            cluster_name = f"{cat.title()} Topics Cluster"
            all_keywords: list[str] = []
            for t in cat_topics:
                all_keywords.extend(t.keywords)
            avg_score = (
                sum(t.opportunity_score for t in cat_topics) / len(cat_topics)
                if cat_topics else 0.0
            )
            cluster = ResearchCluster(
                canonical_name=cluster_name,
                description=f"Automatically clustered topics in category: {cat}",
                keywords=list(set(all_keywords))[:20],
                categories=[cat],
                topic_ids=[str(t.id) for t in cat_topics],
                topic_count=len(cat_topics),
                confidence=0.75,
                centroid=[],
                avg_opportunity_score=avg_score,
                status="active",
            )
            await self._cluster_repo.create(cluster)
            clusters_created += 1

        return {"clusters_created": clusters_created}

    async def get_topic(self, topic_id) -> ResearchTopic:
        from packages.core.exceptions import NotFoundError
        t = await self._topic_repo.get_by_id(topic_id)
        if t is None:
            raise NotFoundError("ResearchTopic", topic_id)
        return t

    async def get_all_paginated(
        self,
        pagination: PaginationParams,
        status: str | None = None,
        research_status: str | None = None,
    ) -> PaginatedResult[ResearchTopic]:
        return await self._topic_repo.get_all_paginated(
            pagination, status=status, research_status=research_status
        )

    async def get_pending_research(self, limit: int = 10) -> list[ResearchTopic]:
        return await self._topic_repo.get_pending_research(limit)

    async def get_top_opportunities(self, limit: int = 20) -> list[ResearchTopic]:
        return await self._topic_repo.get_top_opportunities(limit)

    async def update_topic_status(self, topic_id, status: str, **kwargs) -> ResearchTopic:
        topic = await self.get_topic(topic_id)
        update_data = {"status": status, **kwargs}
        return await self._topic_repo.update(topic, update_data)

    async def count_by_status(self) -> dict[str, int]:
        return await self._topic_repo.count_by_status()

    async def get_clusters(self, pagination: PaginationParams):
        return await self._cluster_repo.get_active_clusters(pagination)

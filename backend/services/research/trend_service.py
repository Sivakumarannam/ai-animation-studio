"""
Trend discovery service — normalises and persists trends from providers.
"""
from __future__ import annotations

import hashlib
from datetime import datetime, timezone
from typing import Any

import structlog

from agents.interfaces.trend_provider import TrendProvider, TrendResult
from database.models.research import ResearchTrend
from repositories.research_repository import ResearchTrendRepository, ResearchMemoryRepository

logger = structlog.get_logger()


def _normalize_keyword(kw: str) -> str:
    return kw.lower().strip().replace(" ", "_").replace("-", "_")


def _content_key(kw: str) -> str:
    return hashlib.md5(kw.encode()).hexdigest()


class TrendDiscoveryService:
    def __init__(
        self,
        trend_repo: ResearchTrendRepository,
        memory_repo: ResearchMemoryRepository,
        trend_provider: TrendProvider,
    ) -> None:
        self._trend_repo = trend_repo
        self._memory_repo = memory_repo
        self._provider = trend_provider

    async def discover_and_persist(
        self,
        categories: list[str] | None = None,
        region: str = "global",
        language: str = "en",
        limit: int = 50,
    ) -> dict[str, Any]:
        """
        Run trend discovery from the provider, deduplicate, and persist.
        Returns a summary dict.
        """
        logger.info("trend_discovery_start", provider=self._provider.provider_name)
        raw_trends: list[TrendResult] = await self._provider.discover_trends(
            categories=categories, region=region, language=language, limit=limit
        )

        new_count = 0
        updated_count = 0
        for tr in raw_trends:
            norm = _normalize_keyword(tr.keyword)
            existing = await self._trend_repo.get_by_keyword(norm)
            if existing:
                # Update velocity / scores
                await self._trend_repo.update(existing, {
                    "trend_score": tr.trend_score,
                    "velocity": tr.velocity,
                    "growth_rate": tr.growth_rate,
                    "popularity_index": tr.popularity_index,
                    "is_emerging": tr.is_emerging,
                    "is_declining": tr.is_declining,
                    "raw_data": tr.raw_data,
                })
                updated_count += 1
            else:
                trend = ResearchTrend(
                    keyword=tr.keyword,
                    normalized_keyword=norm,
                    category=tr.category,
                    region=tr.region,
                    language=tr.language,
                    trend_score=tr.trend_score,
                    velocity=tr.velocity,
                    growth_rate=tr.growth_rate,
                    popularity_index=tr.popularity_index,
                    is_emerging=tr.is_emerging,
                    is_declining=tr.is_declining,
                    status="active",
                    raw_data=tr.raw_data,
                    discovered_at=datetime.now(timezone.utc),
                )
                await self._trend_repo.create(trend)
                new_count += 1

        logger.info(
            "trend_discovery_done",
            new=new_count,
            updated=updated_count,
            total=len(raw_trends),
        )
        return {"trends_discovered": new_count, "trends_updated": updated_count, "total": len(raw_trends)}

    async def get_active_trends(
        self, pagination, category: str | None = None, emerging_only: bool = False
    ):
        return await self._trend_repo.get_active_trends(pagination, category=category, emerging_only=emerging_only)

    async def get_top_trends(self, limit: int = 10) -> list[ResearchTrend]:
        return await self._trend_repo.get_top_trends(limit)

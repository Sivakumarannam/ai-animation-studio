"""
Opportunity scoring service — scores topics for video creation priority.
"""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

import structlog

from database.models.research import ResearchQueue, ResearchScore, ResearchTopic
from packages.utils.pagination import PaginationParams
from repositories.research_repository import (
    ResearchQueueRepository,
    ResearchScoreRepository,
    ResearchTopicRepository,
    ResearchFactRepository,
    ResearchArticleRepository,
)

logger = structlog.get_logger()

# Minimum overall score to enter the story queue
_MIN_QUEUE_SCORE = 60.0


def _compute_score(
    topic: ResearchTopic,
    fact_count: int,
    verified_fact_count: int,
    article_count: int,
) -> dict[str, float]:
    """
    Compute all scoring dimensions. Pure Python — no ML needed.
    Returns a dict of {dimension: 0-100 float} plus an "overall_score".
    """
    # Trend score: direct from topic
    trend_score = min(topic.trend_score, 100.0)

    # Research quality: based on article count + quality
    research_quality = min(article_count * 12.0, 100.0)

    # Fact confidence: ratio of verified to total
    if fact_count > 0:
        fact_confidence = (verified_fact_count / fact_count) * 100.0
    else:
        fact_confidence = 40.0

    # Competition: lower is better — simulate by trend score (higher trend = more competition)
    competition_score = max(0.0, 100.0 - trend_score * 0.5)

    # Novelty: check research_status timing (simplified — always moderate for mock)
    novelty_score = 70.0

    # Audience fit: based on category
    cat = topic.categories[0] if topic.categories else "general"
    audience_map = {
        "technology": 88.0,
        "science": 85.0,
        "education": 90.0,
        "environment": 80.0,
        "history": 75.0,
        "health": 82.0,
        "culture": 72.0,
        "nature": 78.0,
        "food": 68.0,
    }
    audience_fit = audience_map.get(cat, 65.0)

    # Seasonality: neutral unless we have month data (simplified)
    seasonality_score = 65.0

    # Educational value: high for science/education
    edu_map = {"education": 92.0, "science": 85.0, "history": 80.0, "environment": 78.0}
    educational_value = edu_map.get(cat, 68.0)

    # Entertainment value: high for culture/nature
    ent_map = {"culture": 85.0, "nature": 82.0, "food": 80.0, "technology": 78.0}
    entertainment_value = ent_map.get(cat, 65.0)

    # Weighted overall score
    weights = {
        "trend_score": 0.15,
        "research_quality": 0.12,
        "fact_confidence": 0.15,
        "competition_score": 0.10,
        "novelty_score": 0.10,
        "audience_fit": 0.15,
        "seasonality_score": 0.05,
        "educational_value": 0.10,
        "entertainment_value": 0.08,
    }
    dims = {
        "trend_score": trend_score,
        "research_quality": research_quality,
        "fact_confidence": fact_confidence,
        "competition_score": competition_score,
        "novelty_score": novelty_score,
        "audience_fit": audience_fit,
        "seasonality_score": seasonality_score,
        "educational_value": educational_value,
        "entertainment_value": entertainment_value,
    }
    overall = sum(dims[k] * weights[k] for k in dims)
    dims["overall_score"] = round(overall, 2)
    return dims


class OpportunityScoringService:
    def __init__(
        self,
        topic_repo: ResearchTopicRepository,
        score_repo: ResearchScoreRepository,
        queue_repo: ResearchQueueRepository,
        fact_repo: ResearchFactRepository,
        article_repo: ResearchArticleRepository,
    ) -> None:
        self._topic_repo = topic_repo
        self._score_repo = score_repo
        self._queue_repo = queue_repo
        self._fact_repo = fact_repo
        self._article_repo = article_repo

    async def score_all_researched(self) -> dict[str, Any]:
        """Score all topics that have completed research."""
        topics = await self._topic_repo.get_top_opportunities(limit=100)
        scored = 0
        queued = 0
        queued_topic_ids: list[Any] = []

        for topic in topics:
            facts_result = await self._fact_repo.get_by_topic(
                topic.id, PaginationParams(page=1, page_size=1)
            )
            verified_result = await self._fact_repo.get_by_topic(
                topic.id, PaginationParams(page=1, page_size=1), verified_only=True
            )
            articles_result = await self._article_repo.get_by_topic(
                topic.id, PaginationParams(page=1, page_size=1)
            )

            dims = _compute_score(
                topic,
                fact_count=facts_result.total,
                verified_fact_count=verified_result.total,
                article_count=articles_result.total,
            )
            overall = dims.pop("overall_score")

            # Upsert score
            existing_score = await self._score_repo.get_by_topic(topic.id)
            if existing_score:
                await self._score_repo.update(existing_score, {
                    **dims,
                    "overall_score": overall,
                    "scored_at": datetime.now(timezone.utc),
                })
            else:
                score_obj = ResearchScore(
                    topic_id=topic.id,
                    overall_score=overall,
                    scored_at=datetime.now(timezone.utc),
                    **dims,
                )
                await self._score_repo.create(score_obj)

            # Update topic's opportunity score
            await self._topic_repo.update(topic, {"opportunity_score": overall})
            scored += 1

            # Queue high-scoring topics
            if overall >= _MIN_QUEUE_SCORE:
                existing_q = await self._queue_repo.get_by_topic(topic.id)
                if not existing_q:
                    queue_entry = ResearchQueue(
                        topic_id=topic.id,
                        priority=int(overall),
                        status="pending",
                        overall_score=overall,
                        research_summary={
                            "topic": topic.canonical_name,
                            "score": overall,
                            "facts": facts_result.total,
                            "articles": articles_result.total,
                        },
                        queued_at=datetime.now(timezone.utc),
                    )
                    await self._queue_repo.create(queue_entry)
                    queued += 1
                    queued_topic_ids.append(topic.id)

        logger.info("opportunity_scoring_done", scored=scored, queued=queued)
        return {"scored": scored, "queued": queued, "queued_topic_ids": queued_topic_ids}

    async def get_queue(self, pagination, status: str | None = None):
        return await self._queue_repo.get_all_paginated(pagination, status=status)

    async def get_top_scores(self, limit: int = 20) -> list[ResearchScore]:
        return await self._score_repo.get_top_scores(limit)

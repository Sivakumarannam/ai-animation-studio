"""
Research engine — collects and stores research articles, facts, and entities for a topic.
"""
from __future__ import annotations

import hashlib
from datetime import datetime, timezone
from typing import Any

import structlog

from agents.interfaces.research_provider import ResearchProvider
from database.models.research import ResearchArticle, ResearchEntity, ResearchFact, ResearchTopic
from packages.utils.pagination import PaginationParams
from repositories.research_repository import (
    ResearchArticleRepository,
    ResearchEntityRepository,
    ResearchFactRepository,
    ResearchMemoryRepository,
    ResearchTopicRepository,
)

logger = structlog.get_logger()


class ResearchEngineService:
    def __init__(
        self,
        topic_repo: ResearchTopicRepository,
        article_repo: ResearchArticleRepository,
        fact_repo: ResearchFactRepository,
        entity_repo: ResearchEntityRepository,
        memory_repo: ResearchMemoryRepository,
        research_provider: ResearchProvider,
    ) -> None:
        self._topic_repo = topic_repo
        self._article_repo = article_repo
        self._fact_repo = fact_repo
        self._entity_repo = entity_repo
        self._memory_repo = memory_repo
        self._provider = research_provider

    async def research_topic(self, topic: ResearchTopic) -> dict[str, Any]:
        """Run full research pipeline for one topic. Returns a summary dict."""
        logger.info("research_topic_start", topic=topic.canonical_name)
        await self._topic_repo.update(topic, {"research_status": "running", "status": "researching"})

        try:
            result = await self._provider.research_topic(
                topic=topic.canonical_name,
                keywords=topic.keywords,
                max_articles=10,
                language=topic.language,
            )

            # Persist articles
            articles_created = 0
            for art in result.articles:
                content_hash = hashlib.sha256(art.content.encode()).hexdigest()[:64]
                existing = await self._article_repo.get_by_content_hash(content_hash)
                if existing:
                    continue
                article = ResearchArticle(
                    topic_id=topic.id,
                    title=art.title,
                    url=art.url,
                    content=art.content,
                    summary=art.summary,
                    author=art.author,
                    published_at=art.published_at,
                    source_type=art.source_type,
                    language=art.language,
                    content_hash=content_hash,
                    quality_score=art.quality_score,
                    relevance_score=art.relevance_score,
                    status="processed",
                    metadata_=art.metadata,
                )
                await self._article_repo.create(article)
                articles_created += 1

            # Persist facts
            facts_created = 0
            for fact_str in result.facts:
                fact = ResearchFact(
                    topic_id=topic.id,
                    fact_type="general",
                    statement=fact_str,
                    confidence=0.6,
                )
                await self._fact_repo.create(fact)
                facts_created += 1

            # Persist entities
            entities_created = 0
            for ent_dict in result.entities:
                normalized_name = ent_dict.get("name", "").lower().strip()
                entity = ResearchEntity(
                    topic_id=topic.id,
                    entity_type=ent_dict.get("entity_type", "concept"),
                    name=ent_dict.get("name", ""),
                    normalized_name=normalized_name,
                    description=ent_dict.get("description", ""),
                    attributes=ent_dict,
                    confidence=0.8,
                )
                await self._entity_repo.create(entity)
                entities_created += 1

            # Update topic
            await self._topic_repo.update(topic, {
                "research_status": "completed",
                "status": "researched",
                "research_quality": result.quality_score,
                "article_count": articles_created,
                "fact_count": facts_created,
                "researched_at": datetime.now(timezone.utc),
            })

            logger.info(
                "research_topic_done",
                topic=topic.canonical_name,
                articles=articles_created,
                facts=facts_created,
                entities=entities_created,
            )
            return {
                "topic_id": str(topic.id),
                "articles_created": articles_created,
                "facts_created": facts_created,
                "entities_created": entities_created,
                "quality_score": result.quality_score,
            }

        except Exception as exc:
            await self._topic_repo.update(topic, {
                "research_status": "failed",
                "status": "discovered",
            })
            logger.error("research_topic_failed", topic=topic.canonical_name, error=str(exc))
            raise

    async def get_articles(self, topic_id, pagination, status: str | None = None):
        return await self._article_repo.get_by_topic(topic_id, pagination, status=status)

    async def get_facts(self, topic_id, pagination, verified_only: bool = False):
        return await self._fact_repo.get_by_topic(topic_id, pagination, verified_only=verified_only)

    async def get_entities(self, topic_id):
        return await self._entity_repo.get_by_topic(topic_id)

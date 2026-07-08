"""
Scheduler service — orchestrates the full research pipeline on schedule.
"""
from __future__ import annotations

import time
from datetime import datetime, timezone
from typing import Any

import structlog

from database.models.research import ResearchHistory
from repositories.research_repository import ResearchHistoryRepository, ResearchMemoryRepository

logger = structlog.get_logger()


class SchedulerService:
    def __init__(
        self,
        history_repo: ResearchHistoryRepository,
        memory_repo: ResearchMemoryRepository,
        session,
    ) -> None:
        self._history_repo = history_repo
        self._memory_repo = memory_repo
        self._session = session

    async def run_trend_discovery(self, triggered_by: str = "scheduler") -> dict[str, Any]:
        """Phase: discover trends and create topics."""
        start = time.monotonic()
        details: dict[str, Any] = {}

        from repositories.research_repository import (
            ResearchTrendRepository,
            ResearchTopicRepository,
            ResearchClusterRepository,
        )
        from services.research.trend_service import TrendDiscoveryService
        from services.research.topic_service import TopicService
        from agents.registry import get_trend_provider

        try:
            trend_repo = ResearchTrendRepository(self._session)
            topic_repo = ResearchTopicRepository(self._session)
            cluster_repo = ResearchClusterRepository(self._session)

            provider = get_trend_provider()
            trend_svc = TrendDiscoveryService(trend_repo, self._memory_repo, provider)
            topic_svc = TopicService(topic_repo, cluster_repo, trend_repo, self._memory_repo)

            trend_result = await trend_svc.discover_and_persist()
            topic_result = await topic_svc.create_topics_from_trends()
            cluster_result = await topic_svc.cluster_topics()
            details = {**trend_result, **topic_result, **cluster_result}

            await self._record_history(
                run_type="trend_discovery",
                status="completed",
                trends_discovered=trend_result.get("trends_discovered", 0),
                topics_researched=topic_result.get("created", 0),
                duration_seconds=time.monotonic() - start,
                details=details,
                triggered_by=triggered_by,
            )
        except Exception as exc:
            logger.error("scheduler_trend_discovery_failed", error=str(exc))
            await self._record_history(
                run_type="trend_discovery",
                status="failed",
                duration_seconds=time.monotonic() - start,
                error_message=str(exc),
                triggered_by=triggered_by,
            )
            raise

        return details

    async def run_research_refresh(self, triggered_by: str = "scheduler") -> dict[str, Any]:
        """Phase: research pending topics, verify facts."""
        start = time.monotonic()
        details: dict[str, Any] = {}

        from repositories.research_repository import (
            ResearchTopicRepository,
            ResearchArticleRepository,
            ResearchFactRepository,
            ResearchEntityRepository,
        )
        from services.research.research_engine_service import ResearchEngineService
        from services.research.fact_verification_service import FactVerificationService
        from agents.registry import get_research_provider, get_fact_verification_provider

        try:
            topic_repo = ResearchTopicRepository(self._session)
            article_repo = ResearchArticleRepository(self._session)
            fact_repo = ResearchFactRepository(self._session)
            entity_repo = ResearchEntityRepository(self._session)

            research_svc = ResearchEngineService(
                topic_repo, article_repo, fact_repo, entity_repo,
                self._memory_repo, get_research_provider()
            )
            verification_svc = FactVerificationService(
                fact_repo, topic_repo, get_fact_verification_provider()
            )

            pending_topics = await topic_repo.get_pending_research(limit=5)
            topics_researched = 0
            for topic in pending_topics:
                try:
                    await research_svc.research_topic(topic)
                    topics_researched += 1
                except Exception as e:
                    logger.warning("topic_research_failed", topic=topic.canonical_name, error=str(e))

            verification_result = await verification_svc.verify_pending_facts(batch_size=30)

            details = {
                "topics_researched": topics_researched,
                **verification_result,
            }

            await self._record_history(
                run_type="research_refresh",
                status="completed",
                topics_researched=topics_researched,
                facts_verified=verification_result.get("verified", 0),
                duration_seconds=time.monotonic() - start,
                details=details,
                triggered_by=triggered_by,
            )
        except Exception as exc:
            logger.error("scheduler_research_refresh_failed", error=str(exc))
            await self._record_history(
                run_type="research_refresh",
                status="failed",
                duration_seconds=time.monotonic() - start,
                error_message=str(exc),
                triggered_by=triggered_by,
            )
            raise

        return details

    async def run_opportunity_report(self, triggered_by: str = "scheduler") -> dict[str, Any]:
        """Phase: score opportunities and queue for Story Intelligence."""
        start = time.monotonic()
        details: dict[str, Any] = {}

        from repositories.research_repository import (
            ResearchTopicRepository,
            ResearchScoreRepository,
            ResearchQueueRepository,
            ResearchFactRepository,
            ResearchArticleRepository,
        )
        from services.research.opportunity_scoring_service import OpportunityScoringService
        from services.research.knowledge_integration_service import KnowledgeIntegrationService

        try:
            topic_repo = ResearchTopicRepository(self._session)
            article_repo = ResearchArticleRepository(self._session)
            fact_repo = ResearchFactRepository(self._session)

            scoring_svc = OpportunityScoringService(
                topic_repo=topic_repo,
                score_repo=ResearchScoreRepository(self._session),
                queue_repo=ResearchQueueRepository(self._session),
                fact_repo=fact_repo,
                article_repo=article_repo,
            )
            score_result = await scoring_svc.score_all_researched()

            # Automatically push newly-queued (high-opportunity, verified) topics
            # into Phase 4's knowledge engine so Story Intelligence can retrieve
            # them via RAG without any manual intervention.
            knowledge_docs_created = 0
            queued_topic_ids = score_result.pop("queued_topic_ids", [])
            if queued_topic_ids:
                integration_svc = KnowledgeIntegrationService(
                    topic_repo=topic_repo,
                    article_repo=article_repo,
                    fact_repo=fact_repo,
                    session=self._session,
                )
                for topic_id in queued_topic_ids:
                    try:
                        result = await integration_svc.integrate_topic(topic_id)
                        if not result.get("error"):
                            knowledge_docs_created += 1
                    except Exception as e:
                        logger.warning(
                            "knowledge_integration_failed", topic_id=str(topic_id), error=str(e)
                        )

            details = {**score_result, "knowledge_docs_created": knowledge_docs_created}

            await self._record_history(
                run_type="opportunity_report",
                status="completed",
                opportunities_scored=score_result.get("scored", 0),
                knowledge_docs_created=knowledge_docs_created,
                duration_seconds=time.monotonic() - start,
                details=details,
                triggered_by=triggered_by,
            )
        except Exception as exc:
            logger.error("scheduler_opportunity_report_failed", error=str(exc))
            await self._record_history(
                run_type="opportunity_report",
                status="failed",
                duration_seconds=time.monotonic() - start,
                error_message=str(exc),
                triggered_by=triggered_by,
            )
            raise

        return details

    async def get_scheduler_status(self) -> dict[str, Any]:
        """Return last-run timestamps and status for each phase."""
        phases = ["trend_discovery", "research_refresh", "opportunity_report"]
        status: dict[str, Any] = {"phases": {}}
        for phase in phases:
            last_run = await self._history_repo.get_last_run(phase)
            status["phases"][phase] = {
                "last_run_at": last_run.created_at.isoformat() if last_run else None,
                "last_status": last_run.status if last_run else "never_run",
                "last_duration_seconds": last_run.duration_seconds if last_run else None,
            }
        return status

    async def get_history(self, pagination, run_type: str | None = None):
        return await self._history_repo.get_recent(pagination, run_type=run_type)

    async def _record_history(
        self,
        run_type: str,
        status: str,
        duration_seconds: float = 0.0,
        trends_discovered: int = 0,
        topics_researched: int = 0,
        facts_verified: int = 0,
        opportunities_scored: int = 0,
        knowledge_docs_created: int = 0,
        error_message: str = "",
        details: dict | None = None,
        triggered_by: str = "scheduler",
    ) -> None:
        history = ResearchHistory(
            run_type=run_type,
            status=status,
            trends_discovered=trends_discovered,
            topics_researched=topics_researched,
            facts_verified=facts_verified,
            opportunities_scored=opportunities_scored,
            knowledge_docs_created=knowledge_docs_created,
            duration_seconds=duration_seconds,
            error_message=error_message,
            details=details or {},
            triggered_by=triggered_by,
        )
        await self._history_repo.create(history)

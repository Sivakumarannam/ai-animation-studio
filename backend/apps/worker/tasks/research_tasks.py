"""
Phase 5 — Research & Trend Intelligence Engine Celery tasks.

Follows the exact Phase 3/4 pattern:
  - @celery_app.task wrapping a thin sync shell
  - _run_async() to bridge sync Celery ↔ async business logic
  - DLQ routing on max retries exhaustion
  - All actual logic delegates to services (no business logic here)

TaskDispatcher calls these via apply_async() when Redis is available,
or calls the underlying async core function directly in sync fallback mode.
"""
from __future__ import annotations


from typing import Any

from celery import Task
from celery.utils.log import get_task_logger
from apps.worker.async_utils import run_async as _run_async
from apps.worker.main import celery_app
from apps.worker.tasks.dead_letter import dead_letter_task

logger = get_task_logger(__name__)




# ---------------------------------------------------------------------------
# Helper — build scheduler service from a session
# ---------------------------------------------------------------------------

def _make_scheduler(session):
    from repositories.research_repository import (
        ResearchHistoryRepository,
        ResearchMemoryRepository,
    )
    from services.research.scheduler_service import SchedulerService
    return SchedulerService(
        history_repo=ResearchHistoryRepository(session),
        memory_repo=ResearchMemoryRepository(session),
        session=session,
    )


# ---------------------------------------------------------------------------
# Async core functions — called directly in sync fallback mode
# ---------------------------------------------------------------------------

async def _discover_trends_core(job_id: str) -> dict[str, Any]:
    from database.connection import get_session
    from repositories.research_repository import ResearchJobRepository
    from services.research.job_service import ResearchJobService
    from uuid import UUID

    async for session in get_session():
        job_svc = ResearchJobService(ResearchJobRepository(session))
        scheduler = _make_scheduler(session)

        job = None
        try:
            job = await job_svc.get_job(UUID(job_id))
            await job_svc.start_job(job.id, mode="sync")
        except Exception:
            job = None

        try:
            result = await scheduler.run_trend_discovery(triggered_by="celery")
            if job:
                await job_svc.complete_job(job.id, result)
            await session.commit()
            return result
        except Exception as exc:
            if job:
                await job_svc.fail_job(job.id, str(exc))
            raise
    return {}


async def _research_topic_core(job_id: str, topic_id: str) -> dict[str, Any]:
    from database.connection import get_session
    from repositories.research_repository import (
        ResearchJobRepository,
        ResearchTopicRepository,
        ResearchArticleRepository,
        ResearchFactRepository,
        ResearchEntityRepository,
        ResearchMemoryRepository,
    )
    from services.research.job_service import ResearchJobService
    from services.research.research_engine_service import ResearchEngineService
    from agents.registry import get_research_provider
    from uuid import UUID

    async for session in get_session():
        job_svc = ResearchJobService(ResearchJobRepository(session))
        topic_repo = ResearchTopicRepository(session)
        engine = ResearchEngineService(
            topic_repo=topic_repo,
            article_repo=ResearchArticleRepository(session),
            fact_repo=ResearchFactRepository(session),
            entity_repo=ResearchEntityRepository(session),
            memory_repo=ResearchMemoryRepository(session),
            research_provider=get_research_provider(),
        )

        job = None
        try:
            job = await job_svc.get_job(UUID(job_id))
            await job_svc.start_job(job.id, mode="sync")
        except Exception:
            job = None

        try:
            topic = await topic_repo.get_by_id(UUID(topic_id))
            if topic is None:
                raise ValueError(f"Topic {topic_id} not found")
            result = await engine.research_topic(topic)
            if job:
                await job_svc.complete_job(job.id, result)
            await session.commit()
            return result
        except Exception as exc:
            if job:
                await job_svc.fail_job(job.id, str(exc))
            raise
    return {}


async def _verify_facts_core(job_id: str) -> dict[str, Any]:
    from database.connection import get_session
    from repositories.research_repository import (
        ResearchJobRepository,
        ResearchFactRepository,
        ResearchTopicRepository,
    )
    from services.research.job_service import ResearchJobService
    from services.research.fact_verification_service import FactVerificationService
    from agents.registry import get_fact_verification_provider
    from uuid import UUID

    async for session in get_session():
        job_svc = ResearchJobService(ResearchJobRepository(session))
        verification_svc = FactVerificationService(
            fact_repo=ResearchFactRepository(session),
            topic_repo=ResearchTopicRepository(session),
            verification_provider=get_fact_verification_provider(),
        )

        job = None
        try:
            job = await job_svc.get_job(UUID(job_id))
            await job_svc.start_job(job.id, mode="sync")
        except Exception:
            job = None

        try:
            result = await verification_svc.verify_pending_facts(batch_size=30)
            if job:
                await job_svc.complete_job(job.id, result)
            await session.commit()
            return result
        except Exception as exc:
            if job:
                await job_svc.fail_job(job.id, str(exc))
            raise
    return {}


async def _research_refresh_core(job_id: str) -> dict[str, Any]:
    """Full research-refresh phase: research pending topics AND verify facts."""
    from database.connection import get_session
    from repositories.research_repository import ResearchJobRepository
    from services.research.job_service import ResearchJobService
    from uuid import UUID

    async for session in get_session():
        job_svc = ResearchJobService(ResearchJobRepository(session))
        scheduler = _make_scheduler(session)

        job = None
        try:
            job = await job_svc.get_job(UUID(job_id))
            await job_svc.start_job(job.id, mode="sync")
        except Exception:
            job = None

        try:
            result = await scheduler.run_research_refresh(triggered_by="celery")
            if job:
                await job_svc.complete_job(job.id, result)
            await session.commit()
            return result
        except Exception as exc:
            if job:
                await job_svc.fail_job(job.id, str(exc))
            raise
    return {}


async def _score_opportunities_core(job_id: str) -> dict[str, Any]:
    from database.connection import get_session
    from repositories.research_repository import (
        ResearchJobRepository,
        ResearchTopicRepository,
        ResearchScoreRepository,
        ResearchQueueRepository,
        ResearchFactRepository,
        ResearchArticleRepository,
    )
    from services.research.job_service import ResearchJobService
    from services.research.opportunity_scoring_service import OpportunityScoringService
    from uuid import UUID

    async for session in get_session():
        job_svc = ResearchJobService(ResearchJobRepository(session))
        scoring_svc = OpportunityScoringService(
            topic_repo=ResearchTopicRepository(session),
            score_repo=ResearchScoreRepository(session),
            queue_repo=ResearchQueueRepository(session),
            fact_repo=ResearchFactRepository(session),
            article_repo=ResearchArticleRepository(session),
        )

        job = None
        try:
            job = await job_svc.get_job(UUID(job_id))
            await job_svc.start_job(job.id, mode="sync")
        except Exception:
            job = None

        try:
            result = await scoring_svc.score_all_researched()
            if job:
                await job_svc.complete_job(job.id, result)
            await session.commit()
            return result
        except Exception as exc:
            if job:
                await job_svc.fail_job(job.id, str(exc))
            raise
    return {}


async def _scheduler_tick_core(job_id: str) -> dict[str, Any]:
    """Run the full pipeline in sequence."""
    from database.connection import get_session
    from repositories.research_repository import ResearchJobRepository
    from services.research.job_service import ResearchJobService
    from uuid import UUID

    async for session in get_session():
        job_svc = ResearchJobService(ResearchJobRepository(session))
        scheduler = _make_scheduler(session)

        job = None
        try:
            job = await job_svc.get_job(UUID(job_id))
            await job_svc.start_job(job.id, mode="sync")
        except Exception:
            job = None

        results: dict[str, Any] = {}
        try:
            results["trends"] = await scheduler.run_trend_discovery(triggered_by="scheduler_tick")
        except Exception as e:
            results["trends_error"] = str(e)

        try:
            results["research"] = await scheduler.run_research_refresh(triggered_by="scheduler_tick")
        except Exception as e:
            results["research_error"] = str(e)

        try:
            results["opportunities"] = await scheduler.run_opportunity_report(triggered_by="scheduler_tick")
        except Exception as e:
            results["opportunities_error"] = str(e)

        if job:
            try:
                await job_svc.complete_job(job.id, results)
            except Exception:
                pass
        await session.commit()
        return results
    return {}


# ---------------------------------------------------------------------------
# Celery task wrappers
# ---------------------------------------------------------------------------

@celery_app.task(
    bind=True,
    name="research.discover_trends",
    queue="ai",
    max_retries=3,
    default_retry_delay=60,
    acks_late=True,
)
def rs_discover_trends(self: Task, job_id: str) -> dict[str, Any]:
    logger.info(f"rs_discover_trends start job_id={job_id}")
    try:
        return _run_async(_discover_trends_core(job_id=job_id))
    except Exception as exc:
        logger.error(f"rs_discover_trends failed job_id={job_id} error={exc}")
        try:
            raise self.retry(exc=exc, countdown=60)
        except self.MaxRetriesExceededError:
            dead_letter_task.apply_async(
                kwargs={"task_name": "research.discover_trends", "task_args": {"job_id": job_id}, "error": str(exc)},
                queue="dlq",
            )
            raise


@celery_app.task(
    bind=True,
    name="research.research_topic",
    queue="ai",
    max_retries=3,
    default_retry_delay=90,
    acks_late=True,
)
def rs_research_topic(self: Task, job_id: str, topic_id: str) -> dict[str, Any]:
    logger.info(f"rs_research_topic start job_id={job_id} topic_id={topic_id}")
    try:
        return _run_async(_research_topic_core(job_id=job_id, topic_id=topic_id))
    except Exception as exc:
        logger.error(f"rs_research_topic failed job_id={job_id} error={exc}")
        try:
            raise self.retry(exc=exc, countdown=90)
        except self.MaxRetriesExceededError:
            dead_letter_task.apply_async(
                kwargs={"task_name": "research.research_topic", "task_args": {"job_id": job_id, "topic_id": topic_id}, "error": str(exc)},
                queue="dlq",
            )
            raise


@celery_app.task(
    bind=True,
    name="research.research_refresh",
    queue="ai",
    max_retries=3,
    default_retry_delay=90,
    acks_late=True,
)
def rs_research_refresh(self: Task, job_id: str) -> dict[str, Any]:
    logger.info(f"rs_research_refresh start job_id={job_id}")
    try:
        return _run_async(_research_refresh_core(job_id=job_id))
    except Exception as exc:
        logger.error(f"rs_research_refresh failed job_id={job_id} error={exc}")
        try:
            raise self.retry(exc=exc, countdown=90)
        except self.MaxRetriesExceededError:
            dead_letter_task.apply_async(
                kwargs={"task_name": "research.research_refresh", "task_args": {"job_id": job_id}, "error": str(exc)},
                queue="dlq",
            )
            raise


@celery_app.task(
    bind=True,
    name="research.verify_facts",
    queue="ai",
    max_retries=3,
    default_retry_delay=60,
    acks_late=True,
)
def rs_verify_facts(self: Task, job_id: str) -> dict[str, Any]:
    logger.info(f"rs_verify_facts start job_id={job_id}")
    try:
        return _run_async(_verify_facts_core(job_id=job_id))
    except Exception as exc:
        logger.error(f"rs_verify_facts failed job_id={job_id} error={exc}")
        try:
            raise self.retry(exc=exc, countdown=60)
        except self.MaxRetriesExceededError:
            dead_letter_task.apply_async(
                kwargs={"task_name": "research.verify_facts", "task_args": {"job_id": job_id}, "error": str(exc)},
                queue="dlq",
            )
            raise


@celery_app.task(
    bind=True,
    name="research.score_opportunities",
    queue="default",
    max_retries=3,
    default_retry_delay=60,
    acks_late=True,
)
def rs_score_opportunities(self: Task, job_id: str) -> dict[str, Any]:
    logger.info(f"rs_score_opportunities start job_id={job_id}")
    try:
        return _run_async(_score_opportunities_core(job_id=job_id))
    except Exception as exc:
        logger.error(f"rs_score_opportunities failed job_id={job_id} error={exc}")
        try:
            raise self.retry(exc=exc, countdown=60)
        except self.MaxRetriesExceededError:
            dead_letter_task.apply_async(
                kwargs={"task_name": "research.score_opportunities", "task_args": {"job_id": job_id}, "error": str(exc)},
                queue="dlq",
            )
            raise


@celery_app.task(
    bind=True,
    name="research.scheduler_tick",
    queue="default",
    max_retries=2,
    default_retry_delay=120,
    acks_late=True,
)
def rs_scheduler_tick(self: Task, job_id: str) -> dict[str, Any]:
    logger.info(f"rs_scheduler_tick start job_id={job_id}")
    try:
        return _run_async(_scheduler_tick_core(job_id=job_id))
    except Exception as exc:
        logger.error(f"rs_scheduler_tick failed job_id={job_id} error={exc}")
        try:
            raise self.retry(exc=exc, countdown=120)
        except self.MaxRetriesExceededError:
            dead_letter_task.apply_async(
                kwargs={"task_name": "research.scheduler_tick", "task_args": {"job_id": job_id}, "error": str(exc)},
                queue="dlq",
            )
            raise
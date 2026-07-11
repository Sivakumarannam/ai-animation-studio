"""
Phase 5 — Research & Trend Intelligence Engine API router.
Prefix: /rs  (avoids collision with /si and /kn routes)
"""
from __future__ import annotations

from typing import Annotated
from uuid import UUID

import structlog
from fastapi import APIRouter, Depends, Query, status

from apps.api.dependencies import CurrentUser, SessionDep
from apps.api.schemas.intelligence import PaginationMeta
from apps.api.schemas.research import (
    DispatchResponse,
    ResearchArticleListResponse,
    ResearchArticleResponse,
    ResearchClusterListResponse,
    ResearchClusterResponse,
    ResearchDashboardStats,
    ResearchFactListResponse,
    ResearchFactResponse,
    ResearchEntityResponse,
    ResearchHistoryListResponse,
    ResearchHistoryResponse,
    ResearchJobListResponse,
    ResearchJobResponse,
    ResearchQueueListResponse,
    ResearchQueueResponse,
    ResearchScoreResponse,
    ResearchSourceCreate,
    ResearchSourceListResponse,
    ResearchSourceResponse,
    ResearchTopicCreate,
    ResearchTopicListResponse,
    ResearchTopicResponse,
    ResearchTrendListResponse,
    ResearchTrendResponse,
    SchedulerStatusResponse,
    SchedulerTriggerRequest,
)
from packages.utils.pagination import PaginationParams

logger = structlog.get_logger()

router = APIRouter(prefix="/rs", tags=["research"])


# ─────────────────────────────────────────────────────────────────────────────
# DI helpers
# ─────────────────────────────────────────────────────────────────────────────

def _make_repos(session):
    from repositories.research_repository import (
        ResearchAnalyticsRepository,
        ResearchArticleRepository,
        ResearchClusterRepository,
        ResearchEntityRepository,
        ResearchFactRepository,
        ResearchHistoryRepository,
        ResearchJobRepository,
        ResearchMemoryRepository,
        ResearchQueueRepository,
        ResearchScoreRepository,
        ResearchSourceRepository,
        ResearchTopicRepository,
        ResearchTrendRepository,
        ResearchVersionRepository,
    )
    return {
        "source": ResearchSourceRepository(session),
        "trend": ResearchTrendRepository(session),
        "topic": ResearchTopicRepository(session),
        "cluster": ResearchClusterRepository(session),
        "article": ResearchArticleRepository(session),
        "fact": ResearchFactRepository(session),
        "entity": ResearchEntityRepository(session),
        "score": ResearchScoreRepository(session),
        "queue": ResearchQueueRepository(session),
        "job": ResearchJobRepository(session),
        "history": ResearchHistoryRepository(session),
        "memory": ResearchMemoryRepository(session),
        "version": ResearchVersionRepository(session),
        "analytics": ResearchAnalyticsRepository(session),
    }


def _make_services(session):
    from agents.registry import (
        get_trend_provider,
        get_research_provider,
        get_fact_verification_provider,
    )
    from repositories.research_repository import (
        ResearchArticleRepository,
        ResearchClusterRepository,
        ResearchEntityRepository,
        ResearchFactRepository,
        ResearchHistoryRepository,
        ResearchJobRepository,
        ResearchMemoryRepository,
        ResearchQueueRepository,
        ResearchScoreRepository,
        ResearchTopicRepository,
        ResearchTrendRepository,
    )
    from services.research.fact_verification_service import FactVerificationService
    from services.research.job_service import ResearchJobService
    from services.research.opportunity_scoring_service import OpportunityScoringService
    from services.research.research_engine_service import ResearchEngineService
    from services.research.scheduler_service import SchedulerService
    from services.research.topic_service import TopicService
    from services.research.trend_service import TrendDiscoveryService

    topic_repo = ResearchTopicRepository(session)
    trend_repo = ResearchTrendRepository(session)
    article_repo = ResearchArticleRepository(session)
    fact_repo = ResearchFactRepository(session)
    entity_repo = ResearchEntityRepository(session)
    cluster_repo = ResearchClusterRepository(session)
    queue_repo = ResearchQueueRepository(session)
    score_repo = ResearchScoreRepository(session)
    job_repo = ResearchJobRepository(session)
    history_repo = ResearchHistoryRepository(session)
    memory_repo = ResearchMemoryRepository(session)

    return {
        "trend": TrendDiscoveryService(trend_repo, memory_repo, get_trend_provider()),
        "topic": TopicService(topic_repo, cluster_repo, trend_repo, memory_repo),
        "engine": ResearchEngineService(topic_repo, article_repo, fact_repo, entity_repo, memory_repo, get_research_provider()),
        "verification": FactVerificationService(fact_repo, topic_repo, get_fact_verification_provider()),
        "scoring": OpportunityScoringService(topic_repo, score_repo, queue_repo, fact_repo, article_repo),
        "scheduler": SchedulerService(history_repo, memory_repo, session),
        "jobs": ResearchJobService(job_repo),
        "article_repo": article_repo,
        "fact_repo": fact_repo,
        "entity_repo": entity_repo,
        "score_repo": score_repo,
        "queue_repo": queue_repo,
        "history_repo": history_repo,
        "topic_repo": topic_repo,
        "trend_repo": trend_repo,
        "source_repo": __import__("repositories.research_repository", fromlist=["ResearchSourceRepository"]).ResearchSourceRepository(session),
    }


def _pagination(page: int = Query(1, ge=1), page_size: int = Query(20, ge=1, le=100)) -> PaginationParams:
    return PaginationParams(page=page, page_size=page_size)


def _meta(result) -> PaginationMeta:
    total_pages = max(1, -(-result.total // result.page_size))
    return PaginationMeta(page=result.page, page_size=result.page_size, total=result.total, total_pages=total_pages)


# ─────────────────────────────────────────────────────────────────────────────
# Dashboard
# ─────────────────────────────────────────────────────────────────────────────

@router.get("/dashboard", response_model=ResearchDashboardStats)
async def get_dashboard(current_user: CurrentUser, session: SessionDep) -> ResearchDashboardStats:
    svc = _make_services(session)
    repos = _make_repos(session)

    trend_result = await svc["trend"].get_active_trends(PaginationParams(page=1, page_size=1))
    emerging_result = await svc["trend"].get_active_trends(PaginationParams(page=1, page_size=1), emerging_only=True)
    top_trends = await svc["trend"].get_top_trends(limit=5)

    topic_counts = await svc["topic"].count_by_status()
    total_topics = sum(topic_counts.values())
    researched_topics = topic_counts.get("researched", 0) + topic_counts.get("queued", 0) + topic_counts.get("completed", 0)

    verified_facts = await svc["verification"].get_verified_count()

    queue_result = await svc["scoring"].get_queue(PaginationParams(page=1, page_size=1), status="pending")
    top_opportunities = await svc["topic"].get_top_opportunities(limit=5)
    jobs_status = await svc["jobs"].status_counts()
    scheduler_status = await svc["scheduler"].get_scheduler_status()

    return ResearchDashboardStats(
        active_trends=trend_result.total,
        emerging_trends=emerging_result.total,
        total_topics=total_topics,
        topics_by_status=topic_counts,
        researched_topics=researched_topics,
        verified_facts=verified_facts,
        knowledge_docs_created=0,
        queue_pending=queue_result.total,
        jobs_by_status=jobs_status,
        scheduler_status=scheduler_status,
        top_trends=[ResearchTrendResponse.model_validate(t) for t in top_trends],
        top_opportunities=[ResearchTopicResponse.model_validate(t) for t in top_opportunities],
    )


# ─────────────────────────────────────────────────────────────────────────────
# Sources
# ─────────────────────────────────────────────────────────────────────────────

@router.post("/sources", response_model=ResearchSourceResponse, status_code=201)
async def create_source(body: ResearchSourceCreate, current_user: CurrentUser, session: SessionDep) -> ResearchSourceResponse:
    from database.models.research import ResearchSource
    repos = _make_repos(session)
    source = ResearchSource(**body.model_dump())
    created = await repos["source"].create(source)
    return ResearchSourceResponse.model_validate(created)


@router.get("/sources", response_model=ResearchSourceListResponse)
async def list_sources(
    current_user: CurrentUser, session: SessionDep,
    pagination: Annotated[PaginationParams, Depends(_pagination)],
) -> ResearchSourceListResponse:
    repos = _make_repos(session)
    result = await repos["source"].get_all(pagination)
    return ResearchSourceListResponse(items=[ResearchSourceResponse.model_validate(s) for s in result.items], meta=_meta(result))


@router.patch("/sources/{source_id}", response_model=ResearchSourceResponse)
async def update_source(source_id: UUID, body: dict, current_user: CurrentUser, session: SessionDep) -> ResearchSourceResponse:
    from fastapi import Request
    from packages.core.exceptions import NotFoundError
    repos = _make_repos(session)
    source = await repos["source"].get_by_id(source_id)
    if source is None:
        raise NotFoundError("ResearchSource", source_id)
    updated = await repos["source"].update(source, body)
    return ResearchSourceResponse.model_validate(updated)


@router.delete("/sources/{source_id}", status_code=204, response_model=None)
async def delete_source(source_id: UUID, current_user: CurrentUser, session: SessionDep) -> None:
    from packages.core.exceptions import NotFoundError
    repos = _make_repos(session)
    source = await repos["source"].get_by_id(source_id)
    if source is None:
        raise NotFoundError("ResearchSource", source_id)
    await repos["source"].delete(source)


# ─────────────────────────────────────────────────────────────────────────────
# Trends
# ─────────────────────────────────────────────────────────────────────────────

@router.get("/trends", response_model=ResearchTrendListResponse)
async def list_trends(
    current_user: CurrentUser, session: SessionDep,
    pagination: Annotated[PaginationParams, Depends(_pagination)],
    category: str | None = None,
    emerging_only: bool = False,
) -> ResearchTrendListResponse:
    svc = _make_services(session)
    result = await svc["trend"].get_active_trends(pagination, category=category, emerging_only=emerging_only)
    return ResearchTrendListResponse(items=[ResearchTrendResponse.model_validate(t) for t in result.items], meta=_meta(result))


@router.get("/trends/{trend_id}", response_model=ResearchTrendResponse)
async def get_trend(trend_id: UUID, current_user: CurrentUser, session: SessionDep) -> ResearchTrendResponse:
    from packages.core.exceptions import NotFoundError
    repos = _make_repos(session)
    trend = await repos["trend"].get_by_id(trend_id)
    if trend is None:
        raise NotFoundError("ResearchTrend", trend_id)
    return ResearchTrendResponse.model_validate(trend)


# ─────────────────────────────────────────────────────────────────────────────
# Topics
# ─────────────────────────────────────────────────────────────────────────────

@router.post("/topics", response_model=ResearchTopicResponse, status_code=201)
async def create_topic(body: ResearchTopicCreate, current_user: CurrentUser, session: SessionDep) -> ResearchTopicResponse:
    import re
    from database.models.research import ResearchTopic
    repos = _make_repos(session)
    slug = re.sub(r"[^a-z0-9]+", "-", body.canonical_name.lower().strip()).strip("-")
    topic = ResearchTopic(
        canonical_name=body.canonical_name,
        slug=slug,
        description=body.description,
        keywords=body.keywords or [body.canonical_name.lower()],
        categories=body.categories or ["general"],
        language=body.language,
        status="discovered",
        research_status="pending",
    )
    created = await repos["topic"].create(topic)
    return ResearchTopicResponse.model_validate(created)


@router.get("/topics", response_model=ResearchTopicListResponse)
async def list_topics(
    current_user: CurrentUser, session: SessionDep,
    pagination: Annotated[PaginationParams, Depends(_pagination)],
    status_filter: str | None = Query(None, alias="status"),
    research_status: str | None = None,
) -> ResearchTopicListResponse:
    svc = _make_services(session)
    result = await svc["topic"].get_all_paginated(pagination, status=status_filter, research_status=research_status)
    return ResearchTopicListResponse(items=[ResearchTopicResponse.model_validate(t) for t in result.items], meta=_meta(result))


@router.get("/topics/{topic_id}", response_model=ResearchTopicResponse)
async def get_topic(topic_id: UUID, current_user: CurrentUser, session: SessionDep) -> ResearchTopicResponse:
    svc = _make_services(session)
    topic = await svc["topic"].get_topic(topic_id)
    return ResearchTopicResponse.model_validate(topic)


@router.post("/topics/{topic_id}/research", response_model=DispatchResponse, status_code=202)
async def trigger_topic_research(topic_id: UUID, current_user: CurrentUser, session: SessionDep) -> DispatchResponse:
    from apps.worker.dispatcher import get_dispatcher
    from apps.worker.tasks.research_tasks import rs_research_topic, _research_topic_core
    svc = _make_services(session)
    topic = await svc["topic"].get_topic(topic_id)
    job = await svc["jobs"].create_job("research_topic", topic_id=topic.id)
    await session.commit()

    dispatcher = get_dispatcher()
    result = await dispatcher.dispatch(
        celery_task=rs_research_topic,
        core_coro_factory=lambda: _research_topic_core(job_id=str(job.id), topic_id=str(topic.id)),
        job_id=str(job.id),
        queue="ai",
        task_kwargs={"topic_id": str(topic.id)},
    )
    return DispatchResponse(**result)


@router.patch("/topics/{topic_id}", response_model=ResearchTopicResponse)
async def update_topic(topic_id: UUID, body: dict, current_user: CurrentUser, session: SessionDep) -> ResearchTopicResponse:
    from packages.core.exceptions import NotFoundError
    repos = _make_repos(session)
    topic = await repos["topic"].get_by_id(topic_id)
    if topic is None:
        raise NotFoundError("ResearchTopic", topic_id)
    updated = await repos["topic"].update(topic, body)
    return ResearchTopicResponse.model_validate(updated)


@router.delete("/topics/{topic_id}", status_code=204, response_model=None)
async def delete_topic(topic_id: UUID, current_user: CurrentUser, session: SessionDep) -> None:
    from repositories.research_repository import ResearchTopicRepository
    svc = _make_services(session)
    topic = await svc["topic"].get_topic(topic_id)
    topic_repo = ResearchTopicRepository(session)
    await topic_repo.delete(topic)


# ─────────────────────────────────────────────────────────────────────────────
# Clusters
# ─────────────────────────────────────────────────────────────────────────────

@router.get("/clusters", response_model=ResearchClusterListResponse)
async def list_clusters(
    current_user: CurrentUser, session: SessionDep,
    pagination: Annotated[PaginationParams, Depends(_pagination)],
) -> ResearchClusterListResponse:
    svc = _make_services(session)
    result = await svc["topic"].get_clusters(pagination)
    return ResearchClusterListResponse(items=[ResearchClusterResponse.model_validate(c) for c in result.items], meta=_meta(result))


# ─────────────────────────────────────────────────────────────────────────────
# Articles
# ─────────────────────────────────────────────────────────────────────────────

@router.get("/topics/{topic_id}/articles", response_model=ResearchArticleListResponse)
async def list_articles(
    topic_id: UUID, current_user: CurrentUser, session: SessionDep,
    pagination: Annotated[PaginationParams, Depends(_pagination)],
) -> ResearchArticleListResponse:
    svc = _make_services(session)
    result = await svc["engine"].get_articles(topic_id, pagination)
    return ResearchArticleListResponse(items=[ResearchArticleResponse.model_validate(a) for a in result.items], meta=_meta(result))


# ─────────────────────────────────────────────────────────────────────────────
# Facts
# ─────────────────────────────────────────────────────────────────────────────

@router.get("/topics/{topic_id}/facts", response_model=ResearchFactListResponse)
async def list_facts(
    topic_id: UUID, current_user: CurrentUser, session: SessionDep,
    pagination: Annotated[PaginationParams, Depends(_pagination)],
    verified_only: bool = False,
) -> ResearchFactListResponse:
    svc = _make_services(session)
    result = await svc["engine"].get_facts(topic_id, pagination, verified_only=verified_only)
    return ResearchFactListResponse(items=[ResearchFactResponse.model_validate(f) for f in result.items], meta=_meta(result))


@router.get("/topics/{topic_id}/entities", response_model=list[ResearchEntityResponse])
async def list_entities(
    topic_id: UUID, current_user: CurrentUser, session: SessionDep,
) -> list[ResearchEntityResponse]:
    svc = _make_services(session)
    entities = await svc["engine"].get_entities(topic_id)
    return [ResearchEntityResponse.model_validate(e) for e in entities]


# ─────────────────────────────────────────────────────────────────────────────
# Scores / Opportunities
# ─────────────────────────────────────────────────────────────────────────────

@router.get("/opportunities", response_model=list[ResearchScoreResponse])
async def get_opportunities(
    current_user: CurrentUser, session: SessionDep,
    limit: int = Query(20, ge=1, le=100),
) -> list[ResearchScoreResponse]:
    svc = _make_services(session)
    scores = await svc["scoring"].get_top_scores(limit=limit)
    return [ResearchScoreResponse.model_validate(s) for s in scores]


# ─────────────────────────────────────────────────────────────────────────────
# Queue
# ─────────────────────────────────────────────────────────────────────────────

@router.get("/queue", response_model=ResearchQueueListResponse)
async def list_queue(
    current_user: CurrentUser, session: SessionDep,
    pagination: Annotated[PaginationParams, Depends(_pagination)],
    status_filter: str | None = Query(None, alias="status"),
) -> ResearchQueueListResponse:
    svc = _make_services(session)
    result = await svc["scoring"].get_queue(pagination, status=status_filter)
    return ResearchQueueListResponse(items=[ResearchQueueResponse.model_validate(q) for q in result.items], meta=_meta(result))


@router.patch("/queue/{queue_id}/pause", response_model=ResearchQueueResponse)
async def pause_queue_item(queue_id: UUID, current_user: CurrentUser, session: SessionDep) -> ResearchQueueResponse:
    from packages.core.exceptions import NotFoundError
    repos = _make_repos(session)
    item = await repos["queue"].get_by_id(queue_id)
    if item is None:
        raise NotFoundError("ResearchQueue", queue_id)
    updated = await repos["queue"].update(item, {"status": "paused"})
    return ResearchQueueResponse.model_validate(updated)


@router.delete("/queue/{queue_id}", status_code=204, response_model=None)
async def delete_queue_item(queue_id: UUID, current_user: CurrentUser, session: SessionDep) -> None:
    from packages.core.exceptions import NotFoundError
    repos = _make_repos(session)
    item = await repos["queue"].get_by_id(queue_id)
    if item is None:
        raise NotFoundError("ResearchQueue", queue_id)
    await repos["queue"].delete(item)


# ─────────────────────────────────────────────────────────────────────────────
# Jobs
# ─────────────────────────────────────────────────────────────────────────────

@router.get("/jobs/retry-queue", response_model=list[ResearchJobResponse])
async def get_retry_queue(current_user: CurrentUser, session: SessionDep) -> list[ResearchJobResponse]:
    svc = _make_services(session)
    jobs = await svc["jobs"].get_pending_retries()
    return [ResearchJobResponse.model_validate(j) for j in jobs]


@router.get("/jobs/{job_id}", response_model=ResearchJobResponse)
async def get_job(job_id: UUID, current_user: CurrentUser, session: SessionDep) -> ResearchJobResponse:
    svc = _make_services(session)
    return ResearchJobResponse.model_validate(await svc["jobs"].get_job(job_id))


@router.get("/jobs", response_model=ResearchJobListResponse)
async def list_jobs(
    current_user: CurrentUser, session: SessionDep,
    pagination: Annotated[PaginationParams, Depends(_pagination)],
    status_filter: str | None = Query(None, alias="status"),
    job_type: str | None = None,
) -> ResearchJobListResponse:
    svc = _make_services(session)
    result = await svc["jobs"].list_jobs(pagination, status=status_filter, job_type=job_type)
    return ResearchJobListResponse(items=[ResearchJobResponse.model_validate(j) for j in result.items], meta=_meta(result))


# ─────────────────────────────────────────────────────────────────────────────
# History
# ─────────────────────────────────────────────────────────────────────────────

@router.get("/history", response_model=ResearchHistoryListResponse)
async def list_history(
    current_user: CurrentUser, session: SessionDep,
    pagination: Annotated[PaginationParams, Depends(_pagination)],
    run_type: str | None = None,
) -> ResearchHistoryListResponse:
    svc = _make_services(session)
    result = await svc["scheduler"].get_history(pagination, run_type=run_type)
    return ResearchHistoryListResponse(items=[ResearchHistoryResponse.model_validate(h) for h in result.items], meta=_meta(result))


# ─────────────────────────────────────────────────────────────────────────────
# Scheduler
# ─────────────────────────────────────────────────────────────────────────────

@router.get("/scheduler/status", response_model=SchedulerStatusResponse)
async def get_scheduler_status(current_user: CurrentUser, session: SessionDep) -> SchedulerStatusResponse:
    svc = _make_services(session)
    status_data = await svc["scheduler"].get_scheduler_status()
    return SchedulerStatusResponse(**status_data)


@router.post("/scheduler/trigger", response_model=DispatchResponse, status_code=202)
async def trigger_scheduler(
    body: SchedulerTriggerRequest, current_user: CurrentUser, session: SessionDep,
) -> DispatchResponse:
    from apps.worker.dispatcher import get_dispatcher
    from apps.worker.tasks.research_tasks import (
        rs_discover_trends, _discover_trends_core,
        rs_research_refresh, _research_refresh_core,
        rs_score_opportunities, _score_opportunities_core,
        rs_scheduler_tick, _scheduler_tick_core,
    )

    svc = _make_services(session)

    phase_map = {
        "trend_discovery": ("discover_trends", rs_discover_trends, _discover_trends_core),
        "research_refresh": ("research_refresh", rs_research_refresh, _research_refresh_core),
        "opportunity_report": ("score_opportunities", rs_score_opportunities, _score_opportunities_core),
        "full": ("scheduler_tick", rs_scheduler_tick, _scheduler_tick_core),
    }

    if body.phase not in phase_map:
        from fastapi import HTTPException
        raise HTTPException(status_code=422, detail=f"Unknown phase: {body.phase}. Valid: {list(phase_map.keys())}")

    job_type_str, celery_task, core_fn = phase_map[body.phase]
    job = await svc["jobs"].create_job(job_type_str)
    await session.commit()

    dispatcher = get_dispatcher()
    result = await dispatcher.dispatch(
        celery_task=celery_task,
        core_coro_factory=lambda: core_fn(job_id=str(job.id)),
        job_id=str(job.id),
        queue="ai" if body.phase in ("trend_discovery", "research_refresh") else "default",
        task_kwargs={},
    )
    return DispatchResponse(**result)


# ─────────────────────────────────────────────────────────────────────────────
# Analytics
# ─────────────────────────────────────────────────────────────────────────────

@router.get("/analytics", response_model=list[dict])
async def get_analytics(
    current_user: CurrentUser, session: SessionDep,
    period_type: str = "daily",
    limit: int = Query(30, ge=1, le=90),
) -> list[dict]:
    repos = _make_repos(session)
    records = await repos["analytics"].get_recent(period_type=period_type, limit=limit)
    return [
        {
            "id": str(r.id),
            "period_type": r.period_type,
            "period_start": r.period_start.isoformat(),
            "period_end": r.period_end.isoformat(),
            "total_trends": r.total_trends,
            "active_trends": r.active_trends,
            "emerging_trends": r.emerging_trends,
            "total_topics": r.total_topics,
            "researched_topics": r.researched_topics,
            "verified_facts": r.verified_facts,
            "opportunities_scored": r.opportunities_scored,
            "avg_opportunity_score": r.avg_opportunity_score,
            "top_categories": r.top_categories,
            "top_keywords": r.top_keywords,
        }
        for r in records
    ]

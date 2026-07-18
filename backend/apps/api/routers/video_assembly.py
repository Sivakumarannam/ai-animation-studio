"""
Phase 10 — Video Assembly Engine API router.
Prefix: /va  (avoids collision with /an, /vo, /mu routes)

IMPORTANT: literal routes (/va/dashboard, /va/outputs, /va/retry-queue,
/va/generate/*) declared BEFORE parameterized routes (/va/jobs/{job_id},
/va/outputs/{output_id}) to prevent FastAPI matching literals as UUIDs.

Lesson applied: every req.model_dump() feeding a JSON column uses mode="json".
Lesson applied: dispatch_result = await dispatcher.dispatch(...)
                mode = dispatch_result["mode"]   ← unwrap the string, not the dict.
"""
from __future__ import annotations

from uuid import UUID

import structlog
from fastapi import APIRouter, Depends, HTTPException, Query, status

from apps.api.dependencies import CurrentUser, SessionDep
from apps.api.schemas.video_assembly import (
    DispatchResponse,
    PaginationMeta,
    TriggerAssembleEpisodeRequest,
    TriggerRetryQueueRequest,
    VideoAssemblyDashboardStats,
    VideoAssemblyJobListResponse,
    VideoAssemblyJobResponse,
    VideoOutputListResponse,
    VideoOutputResponse,
    VideoRetryQueueListResponse,
    VideoRetryQueueResponse,
)

logger = structlog.get_logger()

router = APIRouter(prefix="/va", tags=["video-assembly"])


# ---------------------------------------------------------------------------
# DI helpers
# ---------------------------------------------------------------------------

def _make_repos(session):
    from repositories.video_assembly_repository import (
        VideoAssemblyJobRepository,
        VideoAssemblyRetryQueueRepository,
        VideoOutputRepository,
    )
    return dict(
        job=VideoAssemblyJobRepository(session),
        output=VideoOutputRepository(session),
        retry=VideoAssemblyRetryQueueRepository(session),
    )


def _make_services(repos, session):
    from services.video_assembly.video_assembly_job_service import VideoAssemblyJobService
    from services.video_assembly.video_assembly_service import VideoAssemblyService
    from services.video_assembly.retry_engine_service import VideoRetryEngineService

    return dict(
        job=VideoAssemblyJobService(repos["job"]),
        assembly=VideoAssemblyService(repos["output"], session),
        retry=VideoRetryEngineService(repos["retry"]),
    )


def _meta(result) -> PaginationMeta:
    total_pages = (result.total + result.page_size - 1) // result.page_size if result.page_size else 1
    return PaginationMeta(
        total=result.total,
        page=result.page,
        page_size=result.page_size,
        total_pages=total_pages,
    )


# ---------------------------------------------------------------------------
# Dashboard  (LITERAL — must be before parameterized routes)
# ---------------------------------------------------------------------------

@router.get("/dashboard/{project_id}", response_model=VideoAssemblyDashboardStats)
async def get_dashboard(
    project_id: UUID,
    session: SessionDep,
    _: CurrentUser,
):
    repos = _make_repos(session)
    svcs = _make_services(repos, session)

    status_counts = await repos["job"].count_by_status(project_id)
    total_outputs = await repos["output"].count_by_project(project_id)
    total_retry = await repos["retry"].count_by_project(project_id)
    recent_jobs = await svcs["job"].get_recent(project_id, limit=5)

    total_jobs = sum(status_counts.values())
    return VideoAssemblyDashboardStats(
        total_jobs=total_jobs,
        jobs_completed=status_counts.get("completed", 0),
        jobs_pending=status_counts.get("pending", 0),
        jobs_failed=status_counts.get("failed", 0),
        jobs_running=status_counts.get("running", 0),
        total_video_outputs=total_outputs,
        total_retry_entries=total_retry,
        recent_jobs=[VideoAssemblyJobResponse.model_validate(j) for j in recent_jobs],
    )


# ---------------------------------------------------------------------------
# Retry queue  (LITERAL — before parameterized)
# ---------------------------------------------------------------------------

@router.get("/retry-queue", response_model=VideoRetryQueueListResponse)
async def list_retry_queue(
    session: SessionDep,
    _: CurrentUser,
    project_id: UUID = Query(...),
    status_filter: str | None = Query(None, alias="status"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
):
    repos = _make_repos(session)
    result = await repos["retry"].get_paginated(
        project_id, page=page, page_size=page_size, status=status_filter
    )
    return VideoRetryQueueListResponse(
        items=[VideoRetryQueueResponse.model_validate(i) for i in result.items],
        meta=_meta(result),
    )


@router.post("/retry-queue/sweep", response_model=DispatchResponse)
async def sweep_retry_queue(
    req: TriggerRetryQueueRequest,
    session: SessionDep,
    _: CurrentUser,
):
    """Trigger a retry-queue sweep for a project."""
    from apps.worker.dispatcher import TaskDispatcher
    from apps.worker.tasks.video_assembly_tasks import process_video_retry_queue_task
    from apps.worker.tasks.video_assembly_tasks import assemble_episode_task
    from apps.worker.tasks.video_assembly_tasks import process_video_retry_queue_task, _process_video_retry_queue_core
    

    repos = _make_repos(session)
    svcs = _make_services(repos, session)

    job = await svcs["job"].create_job(
        project_id=req.project_id,
        episode_id=None,
        job_type="process_retry_queue",
        triggered_by="api",
        params=req.model_dump(mode="json"),
    )
    await session.commit()

    dispatcher = TaskDispatcher()
    dispatch_result = await dispatcher.dispatch(
        celery_task=process_video_retry_queue_task,
        core_coro_factory=lambda: _process_video_retry_queue_core(
            job_id=str(job.id),
            project_id=str(req.project_id),
            params=req.model_dump(mode="json"),
        ),
        job_id=str(job.id),
        queue="default",
        task_kwargs=dict(
            job_id=str(job.id),
            project_id=str(req.project_id),
            params=req.model_dump(mode="json"),
        ),
    )
    mode = dispatch_result["mode"]

    return DispatchResponse(
        job_id=str(job.id),
        task_id=dispatch_result.get("task_id", str(job.id)),
        mode=mode,
        status="dispatched",
    )


# ---------------------------------------------------------------------------
# Generate  (LITERAL trigger routes — before parameterized)
# ---------------------------------------------------------------------------

@router.post("/generate/assemble-episode", response_model=DispatchResponse, status_code=status.HTTP_202_ACCEPTED)
async def trigger_assemble_episode(
    req: TriggerAssembleEpisodeRequest,
    session: SessionDep,
    _: CurrentUser,
):
    """Trigger video assembly for an episode (episode cut or short-form cut)."""
    from apps.worker.dispatcher import TaskDispatcher
    from apps.worker.tasks.video_assembly_tasks import assemble_episode_task
    from apps.worker.tasks.video_assembly_tasks import assemble_episode_task, _assemble_episode_core

    repos = _make_repos(session)
    svcs = _make_services(repos, session)

    job = await svcs["job"].create_job(
        project_id=req.project_id,
        episode_id=req.episode_id,
        job_type="assemble_episode",
        triggered_by=req.triggered_by,
        params=req.model_dump(mode="json"),
    )
    await session.commit()

    dispatcher = TaskDispatcher()
    dispatch_result = await dispatcher.dispatch(
        celery_task=assemble_episode_task,
        core_coro_factory=lambda: _assemble_episode_core(
            job_id=str(job.id),
            project_id=str(req.project_id),
            params=req.model_dump(mode="json"),
        ),
        job_id=str(job.id),
        queue="render",
        task_kwargs=dict(
            job_id=str(job.id),
            project_id=str(req.project_id),
            params=req.model_dump(mode="json"),
        ),
    )
    mode = dispatch_result["mode"]

    logger.info(
        "va_assemble_episode_dispatched",
        job_id=str(job.id),
        episode_id=str(req.episode_id) if req.episode_id else None,
        mode=mode,
    )
    return DispatchResponse(
        job_id=str(job.id),
        task_id=dispatch_result.get("task_id", str(job.id)),
        mode=mode,
        status="dispatched",
    )


# ---------------------------------------------------------------------------
# Jobs  (parameterized — after literals)
# ---------------------------------------------------------------------------

@router.get("/jobs", response_model=VideoAssemblyJobListResponse)
async def list_jobs(
    session: SessionDep,
    _: CurrentUser,
    project_id: UUID = Query(...),
    status_filter: str | None = Query(None, alias="status"),
    job_type: str | None = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
):
    repos = _make_repos(session)
    result = await repos["job"].get_paginated(
        project_id, page=page, page_size=page_size,
        status=status_filter, job_type=job_type,
    )
    return VideoAssemblyJobListResponse(
        items=[VideoAssemblyJobResponse.model_validate(j) for j in result.items],
        meta=_meta(result),
    )


@router.get("/jobs/{job_id}", response_model=VideoAssemblyJobResponse)
async def get_job(job_id: UUID, session: SessionDep, _: CurrentUser):
    repos = _make_repos(session)
    svcs = _make_services(repos, session)
    try:
        job = await svcs["job"].get_job(job_id)
    except ValueError:
        raise HTTPException(status_code=404, detail="VideoAssemblyJob not found")
    return VideoAssemblyJobResponse.model_validate(job)


# ---------------------------------------------------------------------------
# Outputs  (parameterized — last)
# ---------------------------------------------------------------------------

@router.get("/outputs", response_model=VideoOutputListResponse)
async def list_outputs(
    session: SessionDep,
    _: CurrentUser,
    project_id: UUID = Query(...),
    output_type: str | None = Query(None),
    status_filter: str | None = Query(None, alias="status"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
):
    repos = _make_repos(session)
    result = await repos["output"].get_paginated(
        project_id, page=page, page_size=page_size,
        output_type=output_type, status=status_filter,
    )
    return VideoOutputListResponse(
        items=[VideoOutputResponse.model_validate(i) for i in result.items],
        meta=_meta(result),
    )


@router.get("/outputs/{output_id}", response_model=VideoOutputResponse)
async def get_output(output_id: UUID, session: SessionDep, _: CurrentUser):
    repos = _make_repos(session)
    output = await repos["output"].get_by_id(output_id)
    if output is None:
        raise HTTPException(status_code=404, detail="VideoOutput not found")
    return VideoOutputResponse.model_validate(output)


# ---------------------------------------------------------------------------
# Internal helper
# ---------------------------------------------------------------------------

async def _noop():
    """Placeholder core_coro_factory for dispatch calls that go via Celery."""
    return {"status": "dispatched"}

"""
Phase 7 — Animation Engine API router.
Prefix: /an  (avoids collision with /ag, /si, /kn, /rs routes)

IMPORTANT: literal routes (e.g. /an/retry-queue, /an/jobs/recent) declared
BEFORE parameterized routes (e.g. /an/jobs/{job_id}) to avoid FastAPI
matching literals as UUID path params and returning 422.
"""
from __future__ import annotations

from uuid import UUID

import structlog
from fastapi import APIRouter, Depends, Query, status

from apps.api.dependencies import CurrentUser, SessionDep
from apps.api.schemas.animation_engine import (
    AnimationDashboardStats,
    AnimationJobListResponse,
    AnimationJobResponse,
    AnimationRenderOutputListResponse,
    AnimationRenderOutputResponse,
    AnimationRetryQueueListResponse,
    AnimationRetryQueueResponse,
    DispatchResponse,
    PaginationMeta,
    TriggerEpisodeAnimationRequest,
    TriggerSceneAnimationRequest,
)
from packages.utils.pagination import PaginationParams

logger = structlog.get_logger()

router = APIRouter(prefix="/an", tags=["animation-engine"])


# ---------------------------------------------------------------------------
# DI helpers
# ---------------------------------------------------------------------------

def _make_repos(session):
    from repositories.animation_engine_repository import (
        AnimationJobRepository,
        AnimationRenderOutputRepository,
        AnimationRetryQueueRepository,
    )
    return dict(
        job=AnimationJobRepository(session),
        output=AnimationRenderOutputRepository(session),
        retry=AnimationRetryQueueRepository(session),
    )


def _make_services(repos):
    from agents.registry import get_provider_registry
    from agents.interfaces.animation_provider import AnimationProvider
    from services.animation.render_job_service import RenderJobService
    from services.animation.scene_composition_service import SceneCompositionService
    from services.animation.retry_engine_service import RetryEngineService

    registry = get_provider_registry()
    animation_provider = registry.resolve(AnimationProvider)

    return dict(
        job=RenderJobService(repos["job"]),
        composition=SceneCompositionService(repos["output"], animation_provider),
        retry=RetryEngineService(repos["retry"]),
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
# Dashboard  (LITERAL before parameterized)
# ---------------------------------------------------------------------------

@router.get("/dashboard/{project_id}", response_model=AnimationDashboardStats)
async def get_dashboard(
    project_id: UUID,
    session: SessionDep,
    _: CurrentUser,
):
    repos = _make_repos(session)
    svcs = _make_services(repos)

    status_counts = await repos["job"].count_by_status(project_id)
    total_outputs = await repos["output"].count_by_project(project_id)
    total_retry = await repos["retry"].count_by_project(project_id)
    recent_jobs = await svcs["job"].get_recent(project_id, limit=5)

    total_jobs = sum(status_counts.values())
    return AnimationDashboardStats(
        total_jobs=total_jobs,
        jobs_completed=status_counts.get("completed", 0),
        jobs_pending=status_counts.get("pending", 0),
        jobs_failed=status_counts.get("failed", 0),
        jobs_running=status_counts.get("running", 0),
        total_render_outputs=total_outputs,
        total_retry_queue=total_retry,
        recent_jobs=[AnimationJobResponse.model_validate(j) for j in recent_jobs],
    )


# ---------------------------------------------------------------------------
# Generation triggers  (LITERAL before parameterized)
# ---------------------------------------------------------------------------

@router.post("/generate/scene", response_model=DispatchResponse, status_code=status.HTTP_202_ACCEPTED)
async def trigger_scene_animation(
    body: TriggerSceneAnimationRequest,
    session: SessionDep,
    _: CurrentUser,
):
    from apps.worker.dispatcher import TaskDispatcher
    from apps.worker.tasks.animation_tasks import (
        render_scene_task,
        _render_scene_core,
    )

    repos = _make_repos(session)
    svcs = _make_services(repos)
    job_svc = svcs["job"]

    job = await job_svc.create_job(
        job_type="render_scene",
        project_id=body.project_id,
        scene_id=body.scene_id,
        episode_id=body.episode_id,
        params={
            "background_storage_key": body.background_storage_key,
            "characters": body.characters,
            "duration_seconds": body.duration_seconds,
            "fps": body.fps,
            "width": body.width,
            "height": body.height,
            "camera_motion": body.camera_motion,
            "dialogue_segments": body.dialogue_segments,
            "extra": body.extra_params,
        },
        triggered_by="api",
    )
    await session.commit()

    dispatcher = TaskDispatcher()
    dispatch_result = await dispatcher.dispatch(
        celery_task=render_scene_task,
        core_coro_factory=lambda: _render_scene_core(
            str(job.id),
            str(body.scene_id),
            str(body.project_id),
            job.params,
        ),
        job_id=str(job.id),
        queue="render",
        task_kwargs={
            "scene_id": str(body.scene_id),
            "project_id": str(body.project_id),
            "params": job.params,
        },
    )
    mode = dispatch_result["mode"]
    return DispatchResponse(
        job_id=job.id,
        status="dispatched",
        message=f"Scene animation render dispatched (mode={mode})",
        dispatch_mode=mode,
    )


@router.post("/generate/episode", response_model=DispatchResponse, status_code=status.HTTP_202_ACCEPTED)
async def trigger_episode_animation(
    body: TriggerEpisodeAnimationRequest,
    session: SessionDep,
    _: CurrentUser,
):
    from apps.worker.dispatcher import TaskDispatcher
    from apps.worker.tasks.animation_tasks import (
        render_episode_task,
        _render_episode_core,
    )

    repos = _make_repos(session)
    svcs = _make_services(repos)
    job_svc = svcs["job"]

    # Pass scenes as dicts so _render_episode_core can call scene_params.get("scene_id")
    params = {
        "scenes": [
            {
                "scene_id": str(s),
                "fps": body.fps,
                "width": body.width,
                "height": body.height,
                "background_storage_key": "",
                "characters": [],
                "duration_seconds": 5.0,
                "camera_motion": "static",
            }
            for s in (body.scene_ids or [])
        ],
        "fps": body.fps,
        "width": body.width,
        "height": body.height,
        "force_re_render": body.force_re_render,
    }

    job = await job_svc.create_job(
        job_type="render_episode",
        project_id=body.project_id,
        episode_id=body.episode_id,
        params=params,
        triggered_by="api",
    )
    await session.commit()

    dispatcher = TaskDispatcher()
    dispatch_result = await dispatcher.dispatch(
        celery_task=render_episode_task,
        core_coro_factory=lambda: _render_episode_core(
            str(job.id),
            str(body.episode_id),
            str(body.project_id),
            params,
        ),
        job_id=str(job.id),
        queue="render",
        task_kwargs={
            "episode_id": str(body.episode_id),
            "project_id": str(body.project_id),
            "params": params,
        },
    )
    mode = dispatch_result["mode"]
    return DispatchResponse(
        job_id=job.id,
        status="dispatched",
        message=f"Episode animation render dispatched (mode={mode})",
        dispatch_mode=mode,
    )


# ---------------------------------------------------------------------------
# Retry Queue  (LITERAL before /jobs/{job_id})
# ---------------------------------------------------------------------------

@router.get("/retry-queue", response_model=AnimationRetryQueueListResponse)
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
        project_id, PaginationParams(page=page, page_size=page_size), status=status_filter
    )
    return AnimationRetryQueueListResponse(
        items=[AnimationRetryQueueResponse.model_validate(i) for i in result.items],
        meta=_meta(result),
    )


@router.post("/retry-queue/{entry_id}/retry", response_model=DispatchResponse, status_code=status.HTTP_202_ACCEPTED)
async def retry_entry(entry_id: UUID, session: SessionDep, _: CurrentUser):
    from apps.worker.dispatcher import TaskDispatcher
    from apps.worker.tasks.animation_tasks import (
        process_animation_retry_queue_task,
        _process_animation_retry_queue_core,
    )

    repos = _make_repos(session)
    entry = await repos["retry"].get_by_id(entry_id)
    if entry is None:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="AnimationRetryQueue entry not found")

    svcs = _make_services(repos)
    job = await svcs["job"].create_job(
        job_type="render_retry_queue",
        project_id=entry.project_id,
    )
    await session.commit()

    dispatcher = TaskDispatcher()
    dispatch_result = await dispatcher.dispatch(
        celery_task=process_animation_retry_queue_task,
        core_coro_factory=lambda: _process_animation_retry_queue_core(
            str(job.id), str(entry.project_id), {"limit": 1}
        ),
        job_id=str(job.id),
        queue="default",
        task_kwargs={"project_id": str(entry.project_id), "params": {"limit": 1}},
    )
    mode = dispatch_result["mode"]
    return DispatchResponse(
        job_id=job.id,
        status="dispatched",
        message=f"Animation retry dispatched (mode={mode})",
        dispatch_mode=mode,
    )


# ---------------------------------------------------------------------------
# Jobs
# ---------------------------------------------------------------------------

@router.get("/jobs", response_model=AnimationJobListResponse)
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
    svcs = _make_services(repos)
    result = await svcs["job"].get_jobs(
        project_id, PaginationParams(page=page, page_size=page_size),
        status=status_filter, job_type=job_type,
    )
    return AnimationJobListResponse(
        items=[AnimationJobResponse.model_validate(i) for i in result.items],
        meta=_meta(result),
    )


@router.get("/jobs/{job_id}", response_model=AnimationJobResponse)
async def get_job(job_id: UUID, session: SessionDep, _: CurrentUser):
    repos = _make_repos(session)
    svcs = _make_services(repos)
    try:
        job = await svcs["job"].get_job(job_id)
    except Exception:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="AnimationJob not found")
    return AnimationJobResponse.model_validate(job)


# ---------------------------------------------------------------------------
# Render Outputs
# ---------------------------------------------------------------------------

@router.get("/outputs", response_model=AnimationRenderOutputListResponse)
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
    result = await repos["output"].get_by_project(
        project_id, PaginationParams(page=page, page_size=page_size),
        output_type=output_type, status=status_filter,
    )
    return AnimationRenderOutputListResponse(
        items=[AnimationRenderOutputResponse.model_validate(i) for i in result.items],
        meta=_meta(result),
    )


@router.get("/outputs/{output_id}", response_model=AnimationRenderOutputResponse)
async def get_output(output_id: UUID, session: SessionDep, _: CurrentUser):
    repos = _make_repos(session)
    output = await repos["output"].get_by_id(output_id)
    if output is None:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="AnimationRenderOutput not found")
    return AnimationRenderOutputResponse.model_validate(output)

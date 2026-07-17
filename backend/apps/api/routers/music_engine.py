"""
Phase 9 — Music & Sound Engine API router.
Prefix: /mu  (avoids collision with /ag, /si, /kn, /rs, /an, /vo routes)

IMPORTANT: literal routes (/mu/dashboard, /mu/sfx, /mu/retry-queue, /mu/generate/*)
declared BEFORE parameterized routes (/mu/jobs/{job_id}) to avoid FastAPI
matching literals as UUID path params and returning 422.
"""
from __future__ import annotations

from uuid import UUID

import structlog
from fastapi import APIRouter, Depends, HTTPException, Query, status

from apps.api.dependencies import CurrentUser, SessionDep
from apps.api.schemas.music_engine import (
    DispatchResponse,
    MusicDashboardStats,
    MusicJobListResponse,
    MusicJobResponse,
    MusicOutputListResponse,
    MusicOutputResponse,
    MusicRetryQueueListResponse,
    MusicRetryQueueResponse,
    PaginationMeta,
    SFXAssetListResponse,
    SFXAssetResponse,
    TriggerMusicTrackRequest,
    TriggerSceneAudioRequest,
)
from packages.utils.pagination import PaginationParams

logger = structlog.get_logger()

router = APIRouter(prefix="/mu", tags=["music-engine"])


# ---------------------------------------------------------------------------
# DI helpers
# ---------------------------------------------------------------------------

def _make_repos(session):
    from repositories.music_engine_repository import (
        MusicJobRepository,
        MusicOutputRepository,
        MusicRetryQueueRepository,
        SFXAssetRepository,
    )
    return dict(
        job=MusicJobRepository(session),
        output=MusicOutputRepository(session),
        sfx=SFXAssetRepository(session),
        retry=MusicRetryQueueRepository(session),
    )


def _make_services(repos):
    from agents.registry import get_provider_registry
    from agents.interfaces.music_provider import MusicProvider
    from services.music.music_job_service import MusicJobService
    from services.music.music_generation_service import MusicGenerationService
    from services.music.sfx_library_service import SFXLibraryService
    from services.music.retry_engine_service import MusicRetryEngineService

    registry = get_provider_registry()
    music_provider = registry.resolve(MusicProvider)

    return dict(
        job=MusicJobService(repos["job"]),
        generation=MusicGenerationService(repos["output"], music_provider),
        sfx=SFXLibraryService(repos["sfx"]),
        retry=MusicRetryEngineService(repos["retry"]),
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

@router.get("/dashboard/{project_id}", response_model=MusicDashboardStats)
async def get_dashboard(
    project_id: UUID,
    session: SessionDep,
    _: CurrentUser,
):
    repos = _make_repos(session)
    svcs = _make_services(repos)

    status_counts = await repos["job"].count_by_status(project_id)
    total_outputs = await repos["output"].count_by_project(project_id)
    total_sfx = await repos["sfx"].count_active()
    total_retry = await repos["retry"].count_by_project(project_id)
    recent_jobs = await svcs["job"].get_recent(project_id, limit=5)

    total_jobs = sum(status_counts.values())
    return MusicDashboardStats(
        total_jobs=total_jobs,
        jobs_completed=status_counts.get("completed", 0),
        jobs_pending=status_counts.get("pending", 0),
        jobs_failed=status_counts.get("failed", 0),
        jobs_running=status_counts.get("running", 0),
        total_music_outputs=total_outputs,
        total_sfx_assets=total_sfx,
        total_retry_queue=total_retry,
        recent_jobs=[MusicJobResponse.model_validate(j) for j in recent_jobs],
    )


# ---------------------------------------------------------------------------
# SFX Library  (LITERAL — must be before /jobs/{job_id})
# ---------------------------------------------------------------------------

@router.get("/sfx", response_model=SFXAssetListResponse)
async def list_sfx(
    session: SessionDep,
    _: CurrentUser,
    category: str | None = Query(None),
    search: str | None = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
):
    repos = _make_repos(session)
    svcs = _make_services(repos)
    result = await svcs["sfx"].list_sfx(
        PaginationParams(page=page, page_size=page_size),
        category=category,
        search=search,
    )
    return SFXAssetListResponse(
        items=[SFXAssetResponse.model_validate(i) for i in result.items],
        meta=_meta(result),
    )


@router.get("/sfx/{sfx_key}", response_model=SFXAssetResponse)
async def get_sfx(sfx_key: str, session: SessionDep, _: CurrentUser):
    repos = _make_repos(session)
    svcs = _make_services(repos)
    asset = await svcs["sfx"].get_by_key(sfx_key)
    if asset is None:
        raise HTTPException(status_code=404, detail="SoundEffectAsset not found")
    return SFXAssetResponse.model_validate(asset)


# ---------------------------------------------------------------------------
# Generation triggers  (LITERAL before parameterized)
# ---------------------------------------------------------------------------

@router.post("/generate/track", response_model=DispatchResponse, status_code=status.HTTP_202_ACCEPTED)
async def generate_track(
    req: TriggerMusicTrackRequest,
    session: SessionDep,
    _: CurrentUser,
):
    """Dispatch a background music generation job for a scene or episode."""
    from apps.worker.dispatcher import TaskDispatcher
    from apps.worker.tasks.music_tasks import generate_track_task, _generate_track_core

    repos = _make_repos(session)
    svcs = _make_services(repos)

    job = await svcs["job"].create_job(
        job_type="generate_track",
        project_id=req.project_id,
        scene_id=req.scene_id,
        episode_id=req.episode_id,
        mood=req.mood,
        params=req.model_dump(mode="json"),
        triggered_by="api",
    )
    await session.flush()

    dispatcher = TaskDispatcher()
    dispatch_result = await dispatcher.dispatch(
        celery_task=generate_track_task,
        core_coro_factory=lambda: _generate_track_core(
            job_id=str(job.id),
            project_id=str(req.project_id),
            params=req.model_dump(mode="json"),
        ),
        job_id=str(job.id),
        queue="ai",
        task_kwargs=dict(
            job_id=str(job.id),
            project_id=str(req.project_id),
            params=req.model_dump(mode="json"),
        ),
    )
    mode = dispatch_result["mode"]

    logger.info("music_generate_track_dispatched", job_id=str(job.id), mode=mode)
    return DispatchResponse(
        job_id=job.id,
        status="accepted",
        message=f"Music generation job dispatched ({mode})",
        dispatch_mode=mode,
    )


@router.post("/generate/scene-audio", response_model=DispatchResponse, status_code=status.HTTP_202_ACCEPTED)
async def generate_scene_audio(
    req: TriggerSceneAudioRequest,
    session: SessionDep,
    _: CurrentUser,
):
    """Dispatch a scene audio generation job (music + optional SFX)."""
    from apps.worker.dispatcher import TaskDispatcher
    from apps.worker.tasks.music_tasks import generate_scene_audio_task, _generate_scene_audio_core

    repos = _make_repos(session)
    svcs = _make_services(repos)

    job = await svcs["job"].create_job(
        job_type="generate_scene_audio",
        project_id=req.project_id,
        scene_id=req.scene_id,
        episode_id=req.episode_id,
        mood=req.mood,
        params=req.model_dump(mode="json"),
        triggered_by="api",
    )
    await session.flush()

    dispatcher = TaskDispatcher()
    dispatch_result = await dispatcher.dispatch(
        celery_task=generate_scene_audio_task,
        core_coro_factory=lambda: _generate_scene_audio_core(
            job_id=str(job.id),
            scene_id=str(req.scene_id),
            project_id=str(req.project_id),
            params=req.model_dump(mode="json"),
        ),
        job_id=str(job.id),
        queue="ai",
        task_kwargs=dict(
            job_id=str(job.id),
            scene_id=str(req.scene_id),
            project_id=str(req.project_id),
            params=req.model_dump(mode="json"),
        ),
    )
    mode = dispatch_result["mode"]

    logger.info("music_generate_scene_audio_dispatched", job_id=str(job.id), mode=mode)
    return DispatchResponse(
        job_id=job.id,
        status="accepted",
        message=f"Scene audio generation job dispatched ({mode})",
        dispatch_mode=mode,
    )


# ---------------------------------------------------------------------------
# Retry Queue  (LITERAL before parameterized)
# ---------------------------------------------------------------------------

@router.get("/retry-queue", response_model=MusicRetryQueueListResponse)
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
        project_id,
        PaginationParams(page=page, page_size=page_size),
        status=status_filter,
    )
    return MusicRetryQueueListResponse(
        items=[MusicRetryQueueResponse.model_validate(i) for i in result.items],
        meta=_meta(result),
    )


@router.post("/retry-queue/process", response_model=DispatchResponse, status_code=status.HTTP_202_ACCEPTED)
async def process_retry_queue(
    session: SessionDep,
    _: CurrentUser,
    project_id: UUID = Query(...),
):
    """Manually trigger a retry queue sweep for a project."""
    from apps.worker.dispatcher import TaskDispatcher
    from apps.worker.tasks.music_tasks import process_music_retry_queue_task, _process_music_retry_queue_core

    repos = _make_repos(session)
    svcs = _make_services(repos)

    job = await svcs["job"].create_job(
        job_type="process_retry_queue",
        project_id=project_id,
        mood="neutral",
        params={"project_id": str(project_id)},
        triggered_by="api",
    )
    await session.flush()

    dispatcher = TaskDispatcher()
    dispatch_result = await dispatcher.dispatch(
        celery_task=process_music_retry_queue_task,
        core_coro_factory=lambda: _process_music_retry_queue_core(
            job_id=str(job.id),
            project_id=str(project_id),
            params={},
        ),
        job_id=str(job.id),
        queue="default",
        task_kwargs=dict(
            job_id=str(job.id),
            project_id=str(project_id),
            params={},
        ),
    )
    mode = dispatch_result["mode"]

    return DispatchResponse(
        job_id=job.id,
        status="accepted",
        message=f"Retry queue sweep dispatched ({mode})",
        dispatch_mode=mode,
    )


# ---------------------------------------------------------------------------
# Jobs  (parameterized — must be LAST)
# ---------------------------------------------------------------------------

@router.get("/jobs", response_model=MusicJobListResponse)
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
        project_id,
        PaginationParams(page=page, page_size=page_size),
        status=status_filter,
        job_type=job_type,
    )
    return MusicJobListResponse(
        items=[MusicJobResponse.model_validate(i) for i in result.items],
        meta=_meta(result),
    )


@router.get("/jobs/{job_id}", response_model=MusicJobResponse)
async def get_job(job_id: UUID, session: SessionDep, _: CurrentUser):
    repos = _make_repos(session)
    svcs = _make_services(repos)
    try:
        job = await svcs["job"].get_job(job_id)
    except Exception:
        raise HTTPException(status_code=404, detail="MusicGenerationJob not found")
    return MusicJobResponse.model_validate(job)


# ---------------------------------------------------------------------------
# Outputs  (parameterized — must be LAST)
# ---------------------------------------------------------------------------

@router.get("/outputs", response_model=MusicOutputListResponse)
async def list_outputs(
    session: SessionDep,
    _: CurrentUser,
    project_id: UUID = Query(...),
    mood: str | None = Query(None),
    output_type: str | None = Query(None),
    status_filter: str | None = Query(None, alias="status"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
):
    repos = _make_repos(session)
    result = await repos["output"].get_paginated(
        project_id,
        PaginationParams(page=page, page_size=page_size),
        mood=mood,
        output_type=output_type,
        status=status_filter,
    )
    return MusicOutputListResponse(
        items=[MusicOutputResponse.model_validate(i) for i in result.items],
        meta=_meta(result),
    )


@router.get("/outputs/{output_id}", response_model=MusicOutputResponse)
async def get_output(output_id: UUID, session: SessionDep, _: CurrentUser):
    repos = _make_repos(session)
    output = await repos["output"].get_by_id(output_id)
    if output is None:
        raise HTTPException(status_code=404, detail="MusicOutput not found")
    return MusicOutputResponse.model_validate(output)
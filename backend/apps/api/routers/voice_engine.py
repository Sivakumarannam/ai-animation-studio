"""
Phase 8 — Voice Engine API router.
Prefix: /vo  (avoids collision with /ag, /si, /kn, /rs, /an routes)

IMPORTANT: literal routes (/vo/retry-queue, /vo/generate/line, /vo/generate/scene)
declared BEFORE parameterized routes (/vo/jobs/{job_id}) to avoid FastAPI
matching literals as UUID path params and returning 422.
"""
from __future__ import annotations

from uuid import UUID

import structlog
from fastapi import APIRouter, Depends, Query, status

from apps.api.dependencies import CurrentUser, SessionDep
from apps.api.schemas.voice_engine import (
    DispatchResponse,
    PaginationMeta,
    TriggerSceneVoiceRequest,
    TriggerVoiceLineRequest,
    VoiceDashboardStats,
    VoiceJobListResponse,
    VoiceJobResponse,
    VoiceOutputListResponse,
    VoiceOutputResponse,
    VoiceRetryQueueListResponse,
    VoiceRetryQueueResponse,
)
from packages.utils.pagination import PaginationParams

logger = structlog.get_logger()

router = APIRouter(prefix="/vo", tags=["voice-engine"])


# ---------------------------------------------------------------------------
# DI helpers
# ---------------------------------------------------------------------------

def _make_repos(session):
    from repositories.voice_engine_repository import (
        VoiceJobRepository,
        VoiceOutputRepository,
        VoiceRetryQueueRepository,
    )
    return dict(
        job=VoiceJobRepository(session),
        output=VoiceOutputRepository(session),
        retry=VoiceRetryQueueRepository(session),
    )


def _make_services(repos):
    from agents.registry import get_provider_registry
    from agents.interfaces.voice_provider import VoiceProvider
    from services.voice.voice_job_service import VoiceJobService
    from services.voice.line_synthesis_service import LineSynthesisService
    from services.voice.retry_engine_service import VoiceRetryEngineService

    registry = get_provider_registry()
    voice_provider = registry.resolve(VoiceProvider)

    return dict(
        job=VoiceJobService(repos["job"]),
        synthesis=LineSynthesisService(repos["output"], voice_provider),
        retry=VoiceRetryEngineService(repos["retry"]),
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

@router.get("/dashboard/{project_id}", response_model=VoiceDashboardStats)
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
    return VoiceDashboardStats(
        total_jobs=total_jobs,
        jobs_completed=status_counts.get("completed", 0),
        jobs_pending=status_counts.get("pending", 0),
        jobs_failed=status_counts.get("failed", 0),
        jobs_running=status_counts.get("running", 0),
        total_voice_outputs=total_outputs,
        total_retry_queue=total_retry,
        recent_jobs=[VoiceJobResponse.model_validate(j) for j in recent_jobs],
    )


# ---------------------------------------------------------------------------
# Generation triggers  (LITERAL before parameterized)
# ---------------------------------------------------------------------------

@router.post("/generate/line", response_model=DispatchResponse, status_code=status.HTTP_202_ACCEPTED)
async def trigger_voice_line(
    body: TriggerVoiceLineRequest,
    session: SessionDep,
    _: CurrentUser,
):
    from apps.worker.dispatcher import TaskDispatcher
    from apps.worker.tasks.voice_tasks import generate_line_task, _generate_line_core

    repos = _make_repos(session)
    svcs = _make_services(repos)

    line_params = {
        "character_id": body.character_id,
        "character_name": body.character_name,
        "dialogue_line": body.dialogue_line,
        "language": body.language,
        "voice_id": body.voice_id,
        "emotion": body.emotion,
        "speed": body.speed,
        "pitch": body.pitch,
        "output_format": body.output_format,
        "voice_seed": body.voice_seed,
    }

    job = await svcs["job"].create_job(
        job_type="generate_line",
        project_id=body.project_id,
        scene_id=body.scene_id,
        episode_id=body.episode_id,
        character_id=body.character_id or None,
        params=line_params,
        triggered_by="api",
    )
    await session.commit()

    dispatcher = TaskDispatcher()
    dispatch_result = await dispatcher.dispatch(
        celery_task=generate_line_task,
        core_coro_factory=lambda: _generate_line_core(
            str(job.id), str(body.project_id), line_params
        ),
        job_id=str(job.id),
        queue="ai",
        task_kwargs={
            "project_id": str(body.project_id),
            "params": line_params,
        },
    )
    mode = dispatch_result["mode"]
    return DispatchResponse(
        job_id=job.id,
        status="dispatched",
        message=f"Voice line generation dispatched (mode={mode})",
        dispatch_mode=mode,
    )


@router.post("/generate/scene", response_model=DispatchResponse, status_code=status.HTTP_202_ACCEPTED)
async def trigger_scene_voice(
    body: TriggerSceneVoiceRequest,
    session: SessionDep,
    _: CurrentUser,
):
    from apps.worker.dispatcher import TaskDispatcher
    from apps.worker.tasks.voice_tasks import generate_scene_task, _generate_scene_core

    repos = _make_repos(session)
    svcs = _make_services(repos)

    scene_params = {
        "dialogue_lines": [dl.model_dump() for dl in body.dialogue_lines],
        "output_format": body.output_format,
        "episode_id": str(body.episode_id) if body.episode_id else None,
        **body.extra_params,
    }

    job = await svcs["job"].create_job(
        job_type="generate_scene",
        project_id=body.project_id,
        scene_id=body.scene_id,
        episode_id=body.episode_id,
        params=scene_params,
        triggered_by="api",
    )
    await session.commit()

    dispatcher = TaskDispatcher()
    dispatch_result = await dispatcher.dispatch(
        celery_task=generate_scene_task,
        core_coro_factory=lambda: _generate_scene_core(
            str(job.id), str(body.scene_id), str(body.project_id), scene_params
        ),
        job_id=str(job.id),
        queue="ai",
        task_kwargs={
            "scene_id": str(body.scene_id),
            "project_id": str(body.project_id),
            "params": scene_params,
        },
    )
    mode = dispatch_result["mode"]
    return DispatchResponse(
        job_id=job.id,
        status="dispatched",
        message=f"Scene voice generation dispatched (mode={mode})",
        dispatch_mode=mode,
    )


# ---------------------------------------------------------------------------
# Retry Queue  (LITERAL before /jobs/{job_id})
# ---------------------------------------------------------------------------

@router.get("/retry-queue", response_model=VoiceRetryQueueListResponse)
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
    return VoiceRetryQueueListResponse(
        items=[VoiceRetryQueueResponse.model_validate(i) for i in result.items],
        meta=_meta(result),
    )


@router.post("/retry-queue/{entry_id}/retry", response_model=DispatchResponse, status_code=status.HTTP_202_ACCEPTED)
async def retry_entry(entry_id: UUID, session: SessionDep, _: CurrentUser):
    from apps.worker.dispatcher import TaskDispatcher
    from apps.worker.tasks.voice_tasks import (
        process_voice_retry_queue_task,
        _process_voice_retry_queue_core,
    )

    repos = _make_repos(session)
    entry = await repos["retry"].get_by_id(entry_id)
    if entry is None:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="VoiceRetryQueue entry not found")

    svcs = _make_services(repos)
    job = await svcs["job"].create_job(
        job_type="process_retry_queue",
        project_id=entry.project_id,
    )
    await session.commit()

    dispatcher = TaskDispatcher()
    dispatch_result = await dispatcher.dispatch(
        celery_task=process_voice_retry_queue_task,
        core_coro_factory=lambda: _process_voice_retry_queue_core(
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
        message=f"Voice retry dispatched (mode={mode})",
        dispatch_mode=mode,
    )


# ---------------------------------------------------------------------------
# Jobs
# ---------------------------------------------------------------------------

@router.get("/jobs", response_model=VoiceJobListResponse)
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
    return VoiceJobListResponse(
        items=[VoiceJobResponse.model_validate(i) for i in result.items],
        meta=_meta(result),
    )


@router.get("/jobs/{job_id}", response_model=VoiceJobResponse)
async def get_job(job_id: UUID, session: SessionDep, _: CurrentUser):
    repos = _make_repos(session)
    svcs = _make_services(repos)
    try:
        job = await svcs["job"].get_job(job_id)
    except Exception:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="VoiceGenerationJob not found")
    return VoiceJobResponse.model_validate(job)


# ---------------------------------------------------------------------------
# Voice Outputs
# ---------------------------------------------------------------------------

@router.get("/outputs", response_model=VoiceOutputListResponse)
async def list_outputs(
    session: SessionDep,
    _: CurrentUser,
    project_id: UUID = Query(...),
    character_id: str | None = Query(None),
    language: str | None = Query(None),
    status_filter: str | None = Query(None, alias="status"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
):
    repos = _make_repos(session)
    result = await repos["output"].get_by_project(
        project_id, PaginationParams(page=page, page_size=page_size),
        character_id=character_id, language=language, status=status_filter,
    )
    return VoiceOutputListResponse(
        items=[VoiceOutputResponse.model_validate(i) for i in result.items],
        meta=_meta(result),
    )


@router.get("/outputs/{output_id}", response_model=VoiceOutputResponse)
async def get_output(output_id: UUID, session: SessionDep, _: CurrentUser):
    repos = _make_repos(session)
    output = await repos["output"].get_by_id(output_id)
    if output is None:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="VoiceOutput not found")
    return VoiceOutputResponse.model_validate(output)

"""
Phase 6 — AI Asset Generation Engine API router.
Prefix: /ag  (avoids collision with /si, /kn, /rs routes)

IMPORTANT: literal routes (e.g. /ag/retry-queue) declared BEFORE
parameterized routes (e.g. /ag/jobs/{job_id}) to avoid FastAPI
matching literals as UUID path params and returning 422.
"""
from __future__ import annotations

from typing import Annotated
from uuid import UUID

import structlog
from fastapi import APIRouter, Depends, Query, status

from apps.api.dependencies import CurrentUser, SessionDep
from apps.api.schemas.asset_generation import (
    AssetCollectionCreate,
    AssetCollectionListResponse,
    AssetCollectionResponse,
    AssetCreate,
    AssetDashboardStats,
    AssetEvaluationListResponse,
    AssetEvaluationResponse,
    AssetListResponse,
    AssetMemoryListResponse,
    AssetProjectCreate,
    AssetProjectListResponse,
    AssetProjectResponse,
    AssetProjectUpdate,
    AssetPromptListResponse,
    AssetPromptResponse,
    AssetResponse,
    AssetSearchRequest,
    AssetSearchResponse,
    AssetStyleCreate,
    AssetStyleListResponse,
    AssetStyleResponse,
    AssetVersionListResponse,
    AssetVersionResponse,
    CameraShotListResponse,
    DispatchResponse,
    ExpressionPresetListResponse,
    ExpressionPresetResponse,
    GenerationHistoryListResponse,
    GenerationJobListResponse,
    GenerationJobResponse,
    LightingPresetListResponse,
    LightingPresetResponse,
    PaginationMeta,
    PosePresetListResponse,
    PosePresetResponse,
    RetryQueueListResponse,
    RetryQueueResponse,
    SceneCompositionListResponse,
    TriggerAssetGenerationRequest,
    TriggerEpisodeGenerationRequest,
)
from packages.utils.pagination import PaginationParams

logger = structlog.get_logger()

router = APIRouter(prefix="/ag", tags=["asset-generation"])


# ─────────────────────────────────────────────────────────────────────────────
# DI helpers
# ─────────────────────────────────────────────────────────────────────────────

def _make_repos(session):
    from repositories.asset_generation_repository import (
        AssetCacheRepository,
        AssetCollectionRepository,
        AssetEmbeddingRepository,
        AssetEvaluationRepository,
        AssetMemoryRepository,
        AssetProjectRepository,
        AssetPromptRepository,
        AssetRelationshipRepository,
        AssetRepository,
        AssetStyleRepository,
        AssetTagRepository,
        AssetVersionRepository,
        CameraShotRepository,
        ExpressionPresetRepository,
        GeneratedImageRepository,
        GenerationHistoryRepository,
        GenerationJobRepository,
        LightingPresetRepository,
        NegativePromptRepository,
        PosePresetRepository,
        PromptHistoryRepository,
        PromptTemplateRepository,
        RetryQueueRepository,
        SceneCompositionRepository,
    )
    return {
        "ap": AssetProjectRepository(session),
        "style": AssetStyleRepository(session),
        "collection": AssetCollectionRepository(session),
        "asset": AssetRepository(session),
        "version": AssetVersionRepository(session),
        "prompt": AssetPromptRepository(session),
        "template": PromptTemplateRepository(session),
        "negative": NegativePromptRepository(session),
        "history_p": PromptHistoryRepository(session),
        "image": GeneratedImageRepository(session),
        "evaluation": AssetEvaluationRepository(session),
        "tag": AssetTagRepository(session),
        "embedding": AssetEmbeddingRepository(session),
        "memory": AssetMemoryRepository(session),
        "composition": SceneCompositionRepository(session),
        "shot": CameraShotRepository(session),
        "lighting": LightingPresetRepository(session),
        "pose": PosePresetRepository(session),
        "expression": ExpressionPresetRepository(session),
        "retry": RetryQueueRepository(session),
        "job": GenerationJobRepository(session),
        "gen_history": GenerationHistoryRepository(session),
        "cache": AssetCacheRepository(session),
        "relationship": AssetRelationshipRepository(session),
    }


def _make_services(session, repos):
    from agents.registry import (
        get_asset_evaluation_provider,
        get_embedding_provider,
        get_image_provider,
    )
    from services.asset_generation.asset_library_service import AssetLibraryService
    from services.asset_generation.asset_planning_service import AssetPlanningService
    from services.asset_generation.consistency_engine_service import ConsistencyEngineService
    from services.asset_generation.generation_job_service import GenerationJobService
    from services.asset_generation.image_generation_service import ImageGenerationService
    from services.asset_generation.prompt_generation_service import PromptGenerationService
    from services.asset_generation.quality_evaluation_service import QualityEvaluationService
    from services.asset_generation.retry_engine_service import RetryEngineService
    from services.asset_generation.shot_planning_service import ShotPlanningService

    return {
        "job": GenerationJobService(repos["job"]),
        "prompt": PromptGenerationService(
            repos["prompt"], repos["template"], repos["negative"],
            repos["history_p"], repos["memory"],
        ),
        "shot": ShotPlanningService(repos["composition"], repos["shot"]),
        "planner": AssetPlanningService(repos["asset"], repos["cache"]),
        "gen": ImageGenerationService(
            repos["asset"], repos["version"], repos["image"],
            get_image_provider(),
        ),
        "eval": QualityEvaluationService(
            repos["evaluation"], repos["asset"], repos["version"],
            repos["retry"], get_asset_evaluation_provider(),
        ),
        "retry": RetryEngineService(repos["retry"], repos["asset"]),
        "library": AssetLibraryService(
            repos["asset"], repos["embedding"], repos["cache"],
            repos["memory"], get_embedding_provider(),
        ),
        "consistency": ConsistencyEngineService(
            repos["asset"], repos["relationship"], repos["memory"],
        ),
    }


def _pagination(page: int = 1, page_size: int = 20) -> PaginationParams:
    return PaginationParams(page=page, page_size=page_size)


def _meta(result) -> PaginationMeta:
    total_pages = (result.total + result.page_size - 1) // result.page_size if result.page_size else 1
    return PaginationMeta(
        total=result.total,
        page=result.page,
        page_size=result.page_size,
        total_pages=total_pages,
    )


# ─────────────────────────────────────────────────────────────────────────────
# Dashboard
# ─────────────────────────────────────────────────────────────────────────────

@router.get("/dashboard/{project_id}", response_model=AssetDashboardStats)
async def get_dashboard(
    project_id: UUID,
    session: SessionDep,
    _: CurrentUser,
):
    repos = _make_repos(session)
    status_counts = await repos["asset"].count_by_status(project_id)
    type_counts = await repos["asset"].count_by_type(project_id)
    recent_jobs_result = await repos["job"].get_recent(project_id, limit=5)
    history_7d = await repos["gen_history"].get_recent_7d_stats(project_id)

    total = sum(status_counts.values())
    return AssetDashboardStats(
        total_assets=total,
        assets_completed=status_counts.get("completed", 0),
        assets_pending=status_counts.get("pending", 0),
        assets_failed=status_counts.get("failed", 0),
        assets_generating=status_counts.get("generating", 0)
            + status_counts.get("evaluating", 0)
            + status_counts.get("planning", 0),
        total_retries=sum(
            a.retry_count
            for a in (await repos["asset"].get_by_project(
                project_id,
                PaginationParams(page=1, page_size=1000),
            )).items
        ),
        avg_quality_score=await repos["evaluation"].get_avg_score([project_id]),
        assets_by_type=type_counts,
        recent_jobs=[GenerationJobResponse.model_validate(j) for j in recent_jobs_result],
        storage_bytes_used=0,
        generation_history_7d=history_7d,
    )


# ─────────────────────────────────────────────────────────────────────────────
# Asset Projects
# ─────────────────────────────────────────────────────────────────────────────

@router.post("/projects", response_model=AssetProjectResponse, status_code=status.HTTP_201_CREATED)
async def create_asset_project(
    body: AssetProjectCreate,
    session: SessionDep,
    _: CurrentUser,
):
    from database.models.asset_generation import AssetProject
    repos = _make_repos(session)
    existing = await repos["ap"].get_by_project_id(body.project_id)
    if existing:
        return AssetProjectResponse.model_validate(existing)
    ap = AssetProject(**body.model_dump())
    saved = await repos["ap"].create(ap)
    await session.commit()
    return AssetProjectResponse.model_validate(saved)


@router.get("/projects", response_model=AssetProjectListResponse)
async def list_asset_projects(
    session: SessionDep,
    _: CurrentUser,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
):
    repos = _make_repos(session)
    result = await repos["ap"].get_active_projects(PaginationParams(page=page, page_size=page_size))
    return AssetProjectListResponse(
        items=[AssetProjectResponse.model_validate(i) for i in result.items],
        meta=_meta(result),
    )


@router.get("/projects/{ap_id}", response_model=AssetProjectResponse)
async def get_asset_project(ap_id: UUID, session: SessionDep, _: CurrentUser):
    repos = _make_repos(session)
    ap = await repos["ap"].get_by_id(ap_id)
    if ap is None:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="AssetProject not found")
    return AssetProjectResponse.model_validate(ap)


# ─────────────────────────────────────────────────────────────────────────────
# Styles
# ─────────────────────────────────────────────────────────────────────────────

@router.post("/styles", response_model=AssetStyleResponse, status_code=status.HTTP_201_CREATED)
async def create_style(body: AssetStyleCreate, session: SessionDep, _: CurrentUser):
    from database.models.asset_generation import AssetStyle
    repos = _make_repos(session)
    s = AssetStyle(**body.model_dump())
    saved = await repos["style"].create(s)
    await session.commit()
    return AssetStyleResponse.model_validate(saved)


@router.get("/styles", response_model=AssetStyleListResponse)
async def list_styles(
    session: SessionDep,
    _: CurrentUser,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    style_type: str | None = Query(None),
):
    repos = _make_repos(session)
    result = await repos["style"].get_active_styles(
        PaginationParams(page=page, page_size=page_size),
        style_type=style_type,
    )
    return AssetStyleListResponse(
        items=[AssetStyleResponse.model_validate(i) for i in result.items],
        meta=_meta(result),
    )


# ─────────────────────────────────────────────────────────────────────────────
# Collections
# ─────────────────────────────────────────────────────────────────────────────

@router.post("/collections", response_model=AssetCollectionResponse, status_code=status.HTTP_201_CREATED)
async def create_collection(body: AssetCollectionCreate, session: SessionDep, _: CurrentUser):
    from database.models.asset_generation import AssetCollection
    repos = _make_repos(session)
    c = AssetCollection(**body.model_dump())
    saved = await repos["collection"].create(c)
    await session.commit()
    return AssetCollectionResponse.model_validate(saved)


@router.get("/collections", response_model=AssetCollectionListResponse)
async def list_collections(
    session: SessionDep,
    _: CurrentUser,
    project_id: UUID = Query(...),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
):
    repos = _make_repos(session)
    result = await repos["collection"].get_by_project(project_id, PaginationParams(page=page, page_size=page_size))
    return AssetCollectionListResponse(
        items=[AssetCollectionResponse.model_validate(i) for i in result.items],
        meta=_meta(result),
    )


# ─────────────────────────────────────────────────────────────────────────────
# Assets
# ─────────────────────────────────────────────────────────────────────────────

@router.post("/assets", response_model=AssetResponse, status_code=status.HTTP_201_CREATED)
async def create_asset(body: AssetCreate, session: SessionDep, _: CurrentUser):
    from database.models.asset_generation import Asset
    repos = _make_repos(session)
    asset = Asset(**body.model_dump())
    saved = await repos["asset"].create(asset)
    await session.commit()
    return AssetResponse.model_validate(saved)


@router.get("/assets", response_model=AssetListResponse)
async def list_assets(
    session: SessionDep,
    _: CurrentUser,
    project_id: UUID = Query(...),
    asset_type: str | None = Query(None),
    status_filter: str | None = Query(None, alias="status"),
    character_id: UUID | None = Query(None),
    episode_id: UUID | None = Query(None),
    collection_id: UUID | None = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
):
    repos = _make_repos(session)
    result = await repos["asset"].get_by_project(
        project_id=project_id,
        pagination=PaginationParams(page=page, page_size=page_size),
        asset_type=asset_type,
        status=status_filter,
        character_id=character_id,
        episode_id=episode_id,
        collection_id=collection_id,
    )
    return AssetListResponse(
        items=[AssetResponse.model_validate(i) for i in result.items],
        meta=_meta(result),
    )


@router.get("/assets/{asset_id}", response_model=AssetResponse)
async def get_asset(asset_id: UUID, session: SessionDep, _: CurrentUser):
    repos = _make_repos(session)
    asset = await repos["asset"].get_by_id(asset_id)
    if asset is None:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Asset not found")
    return AssetResponse.model_validate(asset)


@router.delete("/assets/{asset_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_asset(asset_id: UUID, session: SessionDep, _: CurrentUser):
    repos = _make_repos(session)
    await repos["asset"].soft_delete(asset_id)
    await session.commit()


# ─────────────────────────────────────────────────────────────────────────────
# Asset Versions
# ─────────────────────────────────────────────────────────────────────────────

@router.get("/assets/{asset_id}/versions", response_model=AssetVersionListResponse)
async def list_asset_versions(
    asset_id: UUID,
    session: SessionDep,
    _: CurrentUser,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
):
    repos = _make_repos(session)
    result = await repos["version"].get_paginated(asset_id, PaginationParams(page=page, page_size=page_size))
    return AssetVersionListResponse(
        items=[AssetVersionResponse.model_validate(i) for i in result.items],
        meta=_meta(result),
    )


@router.post("/assets/{asset_id}/versions/{version_id}/promote", response_model=AssetResponse)
async def promote_version(asset_id: UUID, version_id: UUID, session: SessionDep, _: CurrentUser):
    repos = _make_repos(session)
    asset = await repos["asset"].get_by_id(asset_id)
    version = await repos["version"].get_by_id(version_id)
    if asset is None or version is None:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Asset or version not found")
    asset.best_version_id = version.id
    asset.current_version_id = version.id
    asset.storage_key = version.storage_key
    asset.quality_score = version.quality_score
    await session.commit()
    return AssetResponse.model_validate(asset)


# ─────────────────────────────────────────────────────────────────────────────
# Generation triggers  (LITERAL before parameterized)
# ─────────────────────────────────────────────────────────────────────────────

@router.post("/generate/episode", response_model=DispatchResponse, status_code=status.HTTP_202_ACCEPTED)
async def trigger_episode_generation(
    body: TriggerEpisodeGenerationRequest,
    session: SessionDep,
    _: CurrentUser,
):
    from apps.worker.dispatcher import TaskDispatcher
    from apps.worker.tasks.asset_tasks import (
        generate_episode_assets,
        _generate_episode_assets_core,
    )

    repos = _make_repos(session)
    from services.asset_generation.generation_job_service import GenerationJobService
    job_svc = GenerationJobService(repos["job"])
    job = await job_svc.create_job(
        job_type="generate_episode_assets",
        project_id=body.project_id,
        episode_id=body.episode_id,
        params={
            "asset_types": body.asset_types,
            "quality_threshold": body.quality_threshold,
            "max_retries": body.max_retries,
            "force_regenerate": body.force_regenerate,
            "triggered_by": "api",
        },
    )
    await session.commit()

    dispatcher = TaskDispatcher()
    mode = await dispatcher.dispatch(
        task=generate_episode_assets,
        core_coro=_generate_episode_assets_core(
            str(job.id), str(body.episode_id), str(body.project_id),
            {"asset_types": body.asset_types, "quality_threshold": body.quality_threshold,
             "force_regenerate": body.force_regenerate, "triggered_by": "api"},
        ),
        kwargs={
            "job_id": str(job.id),
            "episode_id": str(body.episode_id),
            "project_id": str(body.project_id),
            "params": {
                "asset_types": body.asset_types,
                "quality_threshold": body.quality_threshold,
                "force_regenerate": body.force_regenerate,
            },
        },
    )
    return DispatchResponse(
        job_id=job.id,
        status="dispatched",
        message=f"Episode asset generation dispatched (mode={mode})",
        dispatch_mode=mode,
    )


@router.post("/generate/asset", response_model=DispatchResponse, status_code=status.HTTP_202_ACCEPTED)
async def trigger_asset_generation(
    body: TriggerAssetGenerationRequest,
    session: SessionDep,
    _: CurrentUser,
):
    from apps.worker.dispatcher import TaskDispatcher
    from apps.worker.tasks.asset_tasks import generate_asset, _generate_asset_core

    repos = _make_repos(session)
    asset = await repos["asset"].get_by_id(body.asset_id)
    if asset is None:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Asset not found")

    from services.asset_generation.generation_job_service import GenerationJobService
    job_svc = GenerationJobService(repos["job"])
    job = await job_svc.create_job(
        job_type="generate_asset",
        project_id=asset.project_id,
        asset_id=body.asset_id,
        params={"force_regenerate": body.force_regenerate, **body.custom_params},
    )
    await session.commit()

    dispatcher = TaskDispatcher()
    mode = await dispatcher.dispatch(
        task=generate_asset,
        core_coro=_generate_asset_core(str(job.id), str(body.asset_id), body.custom_params),
        kwargs={"job_id": str(job.id), "asset_id": str(body.asset_id), "params": body.custom_params},
    )
    return DispatchResponse(
        job_id=job.id,
        status="dispatched",
        message=f"Asset generation dispatched (mode={mode})",
        dispatch_mode=mode,
    )


# ─────────────────────────────────────────────────────────────────────────────
# Retry Queue  (LITERAL before /jobs/{job_id})
# ─────────────────────────────────────────────────────────────────────────────

@router.get("/retry-queue", response_model=RetryQueueListResponse)
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
    return RetryQueueListResponse(
        items=[RetryQueueResponse.model_validate(i) for i in result.items],
        meta=_meta(result),
    )


@router.post("/retry-queue/{entry_id}/retry", response_model=DispatchResponse, status_code=status.HTTP_202_ACCEPTED)
async def retry_entry(entry_id: UUID, session: SessionDep, _: CurrentUser):
    from apps.worker.dispatcher import TaskDispatcher
    from apps.worker.tasks.asset_tasks import process_retry_queue, _process_retry_queue_core

    repos = _make_repos(session)
    entry = await repos["retry"].get_by_id(entry_id)
    if entry is None:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="RetryQueue entry not found")

    from services.asset_generation.generation_job_service import GenerationJobService
    job_svc = GenerationJobService(repos["job"])
    job = await job_svc.create_job(
        job_type="process_retry_queue",
        project_id=entry.project_id,
    )
    await session.commit()

    dispatcher = TaskDispatcher()
    mode = await dispatcher.dispatch(
        task=process_retry_queue,
        core_coro=_process_retry_queue_core(str(job.id), str(entry.project_id), {"limit": 1}),
        kwargs={"job_id": str(job.id), "project_id": str(entry.project_id), "params": {"limit": 1}},
    )
    return DispatchResponse(
        job_id=job.id,
        status="dispatched",
        message=f"Retry dispatched (mode={mode})",
        dispatch_mode=mode,
    )


# ─────────────────────────────────────────────────────────────────────────────
# Jobs
# ─────────────────────────────────────────────────────────────────────────────

@router.get("/jobs", response_model=GenerationJobListResponse)
async def list_jobs(
    session: SessionDep,
    _: CurrentUser,
    project_id: UUID = Query(...),
    status_filter: str | None = Query(None, alias="status"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
):
    repos = _make_repos(session)
    result = await repos["job"].get_by_project(
        project_id, PaginationParams(page=page, page_size=page_size), status=status_filter
    )
    return GenerationJobListResponse(
        items=[GenerationJobResponse.model_validate(i) for i in result.items],
        meta=_meta(result),
    )


@router.get("/jobs/{job_id}", response_model=GenerationJobResponse)
async def get_job(job_id: UUID, session: SessionDep, _: CurrentUser):
    repos = _make_repos(session)
    job = await repos["job"].get_by_id(job_id)
    if job is None:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="GenerationJob not found")
    return GenerationJobResponse.model_validate(job)


# ─────────────────────────────────────────────────────────────────────────────
# Evaluations
# ─────────────────────────────────────────────────────────────────────────────

@router.get("/evaluations/{asset_id}", response_model=AssetEvaluationListResponse)
async def list_evaluations(
    asset_id: UUID,
    session: SessionDep,
    _: CurrentUser,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
):
    repos = _make_repos(session)
    result = await repos["evaluation"].get_by_asset(
        asset_id, PaginationParams(page=page, page_size=page_size)
    )
    return AssetEvaluationListResponse(
        items=[AssetEvaluationResponse.model_validate(i) for i in result.items],
        meta=_meta(result),
    )


# ─────────────────────────────────────────────────────────────────────────────
# Prompts
# ─────────────────────────────────────────────────────────────────────────────

@router.get("/prompts", response_model=AssetPromptListResponse)
async def list_prompts(
    session: SessionDep,
    _: CurrentUser,
    prompt_type: str | None = Query(None),
    successful_only: bool = Query(False),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
):
    repos = _make_repos(session)
    result = await repos["prompt"].get_paginated(
        PaginationParams(page=page, page_size=page_size),
        prompt_type=prompt_type,
        successful_only=successful_only,
    )
    return AssetPromptListResponse(
        items=[AssetPromptResponse.model_validate(i) for i in result.items],
        meta=_meta(result),
    )


@router.get("/prompts/{prompt_id}", response_model=AssetPromptResponse)
async def get_prompt(prompt_id: UUID, session: SessionDep, _: CurrentUser):
    repos = _make_repos(session)
    p = await repos["prompt"].get_by_id(prompt_id)
    if p is None:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Prompt not found")
    return AssetPromptResponse.model_validate(p)


# ─────────────────────────────────────────────────────────────────────────────
# Library search
# ─────────────────────────────────────────────────────────────────────────────

@router.post("/library/search", response_model=AssetSearchResponse)
async def search_library(
    body: AssetSearchRequest,
    session: SessionDep,
    _: CurrentUser,
):
    repos = _make_repos(session)
    svcs = _make_services(session, repos)
    results = await svcs["library"].search(
        project_id=body.project_id or UUID("00000000-0000-0000-0000-000000000000"),
        query=body.query,
        asset_type=body.asset_type,
        character_id=body.character_id,
        episode_id=body.episode_id,
        tags=body.tags,
        min_quality=body.min_quality,
        status=body.status,
        limit=body.limit,
        offset=body.offset,
    )
    return AssetSearchResponse(
        items=[AssetResponse.model_validate(a) for a in results["items"]],
        total=results["total"],
        query=body.query,
    )


@router.get("/library/characters", response_model=AssetListResponse)
async def character_library(
    session: SessionDep,
    _: CurrentUser,
    project_id: UUID = Query(...),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
):
    repos = _make_repos(session)
    svcs = _make_services(session, repos)
    result = await svcs["library"].get_character_library(
        project_id, PaginationParams(page=page, page_size=page_size)
    )
    return AssetListResponse(
        items=[AssetResponse.model_validate(i) for i in result.items],
        meta=_meta(result),
    )


@router.get("/library/backgrounds", response_model=AssetListResponse)
async def background_library(
    session: SessionDep,
    _: CurrentUser,
    project_id: UUID = Query(...),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
):
    repos = _make_repos(session)
    svcs = _make_services(session, repos)
    result = await svcs["library"].get_background_library(
        project_id, PaginationParams(page=page, page_size=page_size)
    )
    return AssetListResponse(
        items=[AssetResponse.model_validate(i) for i in result.items],
        meta=_meta(result),
    )


@router.get("/library/props", response_model=AssetListResponse)
async def prop_library(
    session: SessionDep,
    _: CurrentUser,
    project_id: UUID = Query(...),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
):
    repos = _make_repos(session)
    svcs = _make_services(session, repos)
    result = await svcs["library"].get_prop_library(
        project_id, PaginationParams(page=page, page_size=page_size)
    )
    return AssetListResponse(
        items=[AssetResponse.model_validate(i) for i in result.items],
        meta=_meta(result),
    )


# ─────────────────────────────────────────────────────────────────────────────
# Presets
# ─────────────────────────────────────────────────────────────────────────────

@router.get("/presets/lighting", response_model=LightingPresetListResponse)
async def list_lighting_presets(
    session: SessionDep,
    _: CurrentUser,
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
):
    repos = _make_repos(session)
    result = await repos["lighting"].get_active(PaginationParams(page=page, page_size=page_size))
    return LightingPresetListResponse(
        items=[LightingPresetResponse.model_validate(i) for i in result.items],
        meta=_meta(result),
    )


@router.get("/presets/poses", response_model=PosePresetListResponse)
async def list_pose_presets(
    session: SessionDep,
    _: CurrentUser,
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
):
    repos = _make_repos(session)
    result = await repos["pose"].get_active(PaginationParams(page=page, page_size=page_size))
    return PosePresetListResponse(
        items=[PosePresetResponse.model_validate(i) for i in result.items],
        meta=_meta(result),
    )


@router.get("/presets/expressions", response_model=ExpressionPresetListResponse)
async def list_expression_presets(
    session: SessionDep,
    _: CurrentUser,
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
):
    repos = _make_repos(session)
    result = await repos["expression"].get_active(PaginationParams(page=page, page_size=page_size))
    return ExpressionPresetListResponse(
        items=[ExpressionPresetResponse.model_validate(i) for i in result.items],
        meta=_meta(result),
    )


# ─────────────────────────────────────────────────────────────────────────────
# Compositions & Shots
# ─────────────────────────────────────────────────────────────────────────────

@router.get("/compositions", response_model=SceneCompositionListResponse)
async def list_compositions(
    session: SessionDep,
    _: CurrentUser,
    project_id: UUID = Query(...),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
):
    repos = _make_repos(session)
    result = await repos["composition"].get_by_project(
        project_id, PaginationParams(page=page, page_size=page_size)
    )
    return SceneCompositionListResponse(
        items=[i for i in result.items],
        meta=_meta(result),
    )


@router.get("/shots", response_model=CameraShotListResponse)
async def list_shots(
    session: SessionDep,
    _: CurrentUser,
    episode_id: UUID = Query(...),
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
):
    from apps.api.schemas.asset_generation import CameraShotResponse
    repos = _make_repos(session)
    result = await repos["shot"].get_paginated(
        episode_id, PaginationParams(page=page, page_size=page_size)
    )
    return CameraShotListResponse(
        items=[CameraShotResponse.model_validate(i) for i in result.items],
        meta=_meta(result),
    )


# ─────────────────────────────────────────────────────────────────────────────
# Generation History
# ─────────────────────────────────────────────────────────────────────────────

@router.get("/history", response_model=GenerationHistoryListResponse)
async def list_generation_history(
    session: SessionDep,
    _: CurrentUser,
    project_id: UUID = Query(...),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
):
    from apps.api.schemas.asset_generation import GenerationHistoryResponse
    repos = _make_repos(session)
    result = await repos["gen_history"].get_by_project(
        project_id, PaginationParams(page=page, page_size=page_size)
    )
    return GenerationHistoryListResponse(
        items=[GenerationHistoryResponse.model_validate(i) for i in result.items],
        meta=_meta(result),
    )


# ─────────────────────────────────────────────────────────────────────────────
# Asset Memory
# ─────────────────────────────────────────────────────────────────────────────

@router.get("/memory", response_model=AssetMemoryListResponse)
async def list_memory(
    session: SessionDep,
    _: CurrentUser,
    project_id: UUID = Query(...),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
):
    repos = _make_repos(session)
    result = await repos["memory"].get_paginated(
        project_id, PaginationParams(page=page, page_size=page_size)
    )
    return AssetMemoryListResponse(
        items=[i for i in result.items],
        meta=_meta(result),
    )


# ─────────────────────────────────────────────────────────────────────────────
# Embeddings update trigger
# ─────────────────────────────────────────────────────────────────────────────

@router.post("/embeddings/update", response_model=DispatchResponse, status_code=status.HTTP_202_ACCEPTED)
async def trigger_embedding_update(
    session: SessionDep,
    _: CurrentUser,
    project_id: UUID = Query(...),
):
    from apps.worker.dispatcher import TaskDispatcher
    from apps.worker.tasks.asset_tasks import update_embeddings, _update_embeddings_core

    repos = _make_repos(session)
    from services.asset_generation.generation_job_service import GenerationJobService
    job_svc = GenerationJobService(repos["job"])
    job = await job_svc.create_job(job_type="update_embeddings", project_id=project_id)
    await session.commit()

    dispatcher = TaskDispatcher()
    mode = await dispatcher.dispatch(
        task=update_embeddings,
        core_coro=_update_embeddings_core(str(job.id), str(project_id), {}),
        kwargs={"job_id": str(job.id), "project_id": str(project_id), "params": {}},
    )
    return DispatchResponse(
        job_id=job.id,
        status="dispatched",
        message=f"Embedding update dispatched (mode={mode})",
        dispatch_mode=mode,
    )

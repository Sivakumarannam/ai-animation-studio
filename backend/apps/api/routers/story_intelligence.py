"""
Phase 3 — Story Intelligence API router.
Prefix: /si  (avoids collision with existing /stories and /generation)
"""
from __future__ import annotations

from typing import Annotated, Any
from uuid import UUID

import structlog
from fastapi import APIRouter, Depends, HTTPException, Query, status

from apps.api.dependencies import CurrentUser, SessionDep
from apps.api.schemas.intelligence import (
    DispatchResponse,
    EpisodeCreate,
    EpisodeListResponse,
    EpisodeResponse,
    EpisodeUpdate,
    GenerateEpisodeRequest,
    GenerateIdeasRequest,
    GenerationJobListResponse,
    GenerationJobResponse,
    RunFullPipelineRequest,
    SeasonCreate,
    SeasonListResponse,
    SeasonResponse,
    SeasonUpdate,
    StoryEvaluationResponse,
    StoryIdeaCreate,
    StoryIdeaListResponse,
    StoryIdeaResponse,
    StoryIdeaUpdate,
    StoryIntelligenceStats,
    StoryMemoryCreate,
    StoryMemoryListResponse,
    StoryMemoryResponse,
    StorySceneCreate,
    StorySceneListResponse,
    StorySceneResponse,
    StorySceneUpdate,
    StoryVersionResponse,
    WorldCreate,
    WorldListResponse,
    WorldResponse,
    WorldUpdate,
    PaginationMeta,
)
from packages.utils.pagination import PaginationParams

logger = structlog.get_logger()

router = APIRouter(prefix="/si", tags=["story-intelligence"])


# ─────────────────────────────────────────────────────────────────────────────
# DI helpers — built per-request from session
# ─────────────────────────────────────────────────────────────────────────────

def _make_services(session):
    """Instantiate all Phase 3 services from a single session."""
    from agents.registry import get_provider_registry
    from agents.interfaces.llm_provider import LLMProvider
    from repositories.intelligence_repository import (
        WorldRepository, SeasonRepository, EpisodeRepository, StorySceneRepository,
        StoryIdeaRepository, StoryMemoryRepository, StoryEvaluationRepository,
        GenerationJobRepository, GenerationLogRepository, RetryQueueRepository,
        StoryVersionRepository,
    )
    from services.intelligence.world_service import WorldService
    from services.intelligence.season_service import SeasonService
    from services.intelligence.episode_service import EpisodeService
    from services.intelligence.scene_service import StorySceneService
    from services.intelligence.idea_service import StoryIdeaService
    from services.intelligence.evaluator_service import StoryEvaluatorService
    from services.intelligence.memory_service import MemoryService
    from services.intelligence.job_service import GenerationJobService
    from services.intelligence.version_service import VersionService
    from services.intelligence.orchestrator import StoryIntelligenceOrchestrator
    from services.knowledge import build_retrieval_service

    llm = get_provider_registry().resolve(LLMProvider)
    version_repo = StoryVersionRepository(session)
    retrieval_svc = build_retrieval_service(session)

    world_svc = WorldService(WorldRepository(session), version_repo)
    idea_svc = StoryIdeaService(StoryIdeaRepository(session), llm)
    season_svc = SeasonService(SeasonRepository(session), llm)
    episode_svc = EpisodeService(
        EpisodeRepository(session), StoryEvaluationRepository(session), version_repo, llm
    )
    scene_svc = StorySceneService(StorySceneRepository(session), llm)
    eval_svc = StoryEvaluatorService(EpisodeRepository(session), StoryEvaluationRepository(session), llm)
    memory_svc = MemoryService(StoryMemoryRepository(session), llm)
    job_svc = GenerationJobService(
        GenerationJobRepository(session),
        GenerationLogRepository(session),
        RetryQueueRepository(session),
    )
    version_svc = VersionService(version_repo)
    orchestrator = StoryIntelligenceOrchestrator(
        world_svc=world_svc, idea_svc=idea_svc, season_svc=season_svc,
        episode_svc=episode_svc, scene_svc=scene_svc, evaluator_svc=eval_svc,
        memory_svc=memory_svc, job_svc=job_svc, version_svc=version_svc, llm=llm,
        retrieval_svc=retrieval_svc,
    )
    return {
        "world": world_svc, "idea": idea_svc, "season": season_svc,
        "episode": episode_svc, "scene": scene_svc, "eval": eval_svc,
        "memory": memory_svc, "jobs": job_svc, "version": version_svc,
        "orchestrator": orchestrator,
    }


def _pagination(page: int = Query(1, ge=1), page_size: int = Query(20, ge=1, le=100)) -> PaginationParams:
    return PaginationParams(page=page, page_size=page_size)


def _meta(result) -> PaginationMeta:
    total_pages = max(1, -(-result.total // result.page_size))
    return PaginationMeta(
        page=result.page, page_size=result.page_size,
        total=result.total, total_pages=total_pages,
    )


# ─────────────────────────────────────────────────────────────────────────────
# Worlds
# ─────────────────────────────────────────────────────────────────────────────

@router.post("/projects/{project_id}/worlds", response_model=WorldResponse, status_code=201)
async def create_world(
    project_id: UUID,
    body: WorldCreate,
    current_user: CurrentUser,
    session: SessionDep,
) -> WorldResponse:
    svc = _make_services(session)
    world = await svc["world"].create(project_id, body.model_dump())
    return WorldResponse.model_validate(world)


@router.get("/projects/{project_id}/worlds", response_model=WorldListResponse)
async def list_worlds(
    project_id: UUID,
    current_user: CurrentUser,
    session: SessionDep,
    pagination: Annotated[PaginationParams, Depends(_pagination)],
) -> WorldListResponse:
    svc = _make_services(session)
    result = await svc["world"].list_by_project(project_id, pagination)
    return WorldListResponse(
        items=[WorldResponse.model_validate(w) for w in result.items],
        meta=_meta(result),
    )


@router.get("/worlds/{world_id}", response_model=WorldResponse)
async def get_world(world_id: UUID, current_user: CurrentUser, session: SessionDep) -> WorldResponse:
    svc = _make_services(session)
    return WorldResponse.model_validate(await svc["world"].get_by_id(world_id))


@router.patch("/worlds/{world_id}", response_model=WorldResponse)
async def update_world(
    world_id: UUID, body: WorldUpdate, current_user: CurrentUser, session: SessionDep
) -> WorldResponse:
    svc = _make_services(session)
    world = await svc["world"].update(world_id, body.model_dump(exclude_none=True))
    return WorldResponse.model_validate(world)


@router.delete("/worlds/{world_id}", status_code=204, response_model=None)
async def delete_world(world_id: UUID, current_user: CurrentUser, session: SessionDep) -> None:
    svc = _make_services(session)
    await svc["world"].delete(world_id)


# ─────────────────────────────────────────────────────────────────────────────
# Seasons
# ─────────────────────────────────────────────────────────────────────────────

@router.post("/worlds/{world_id}/seasons", response_model=SeasonResponse, status_code=201)
async def create_season(
    world_id: UUID,
    body: SeasonCreate,
    current_user: CurrentUser,
    session: SessionDep,
) -> SeasonResponse:
    svc = _make_services(session)
    world = await svc["world"].get_by_id(world_id)
    season = await svc["season"].create(
        world_id, world.project_id, body.model_dump()
    )
    return SeasonResponse.model_validate(season)


@router.get("/worlds/{world_id}/seasons", response_model=SeasonListResponse)
async def list_seasons(
    world_id: UUID,
    current_user: CurrentUser,
    session: SessionDep,
    pagination: Annotated[PaginationParams, Depends(_pagination)],
) -> SeasonListResponse:
    svc = _make_services(session)
    result = await svc["season"].list_by_world(world_id, pagination)
    return SeasonListResponse(
        items=[SeasonResponse.model_validate(s) for s in result.items],
        meta=_meta(result),
    )


@router.get("/seasons/{season_id}", response_model=SeasonResponse)
async def get_season(season_id: UUID, current_user: CurrentUser, session: SessionDep) -> SeasonResponse:
    svc = _make_services(session)
    return SeasonResponse.model_validate(await svc["season"].get_by_id(season_id))


@router.patch("/seasons/{season_id}", response_model=SeasonResponse)
async def update_season(
    season_id: UUID, body: SeasonUpdate, current_user: CurrentUser, session: SessionDep
) -> SeasonResponse:
    svc = _make_services(session)
    return SeasonResponse.model_validate(
        await svc["season"].update(season_id, body.model_dump(exclude_none=True))
    )


@router.delete("/seasons/{season_id}", status_code=204, response_model=None)
async def delete_season(season_id: UUID, current_user: CurrentUser, session: SessionDep) -> None:
    svc = _make_services(session)
    await svc["season"].delete(season_id)


# ─────────────────────────────────────────────────────────────────────────────
# Episodes
# ─────────────────────────────────────────────────────────────────────────────

@router.post("/seasons/{season_id}/episodes", response_model=EpisodeResponse, status_code=201)
async def create_episode(
    season_id: UUID,
    body: EpisodeCreate,
    current_user: CurrentUser,
    session: SessionDep,
) -> EpisodeResponse:
    svc = _make_services(session)
    season = await svc["season"].get_by_id(season_id)
    ep = await svc["episode"].create(
        season_id, season.world_id, season.project_id, body.model_dump()
    )
    return EpisodeResponse.model_validate(ep)


@router.get("/seasons/{season_id}/episodes", response_model=EpisodeListResponse)
async def list_episodes(
    season_id: UUID,
    current_user: CurrentUser,
    session: SessionDep,
    pagination: Annotated[PaginationParams, Depends(_pagination)],
) -> EpisodeListResponse:
    svc = _make_services(session)
    result = await svc["episode"].list_by_season(season_id, pagination)
    return EpisodeListResponse(
        items=[EpisodeResponse.model_validate(e) for e in result.items],
        meta=_meta(result),
    )


@router.get("/episodes/{episode_id}", response_model=EpisodeResponse)
async def get_episode(episode_id: UUID, current_user: CurrentUser, session: SessionDep) -> EpisodeResponse:
    svc = _make_services(session)
    return EpisodeResponse.model_validate(await svc["episode"].get_by_id(episode_id))


@router.patch("/episodes/{episode_id}", response_model=EpisodeResponse)
async def update_episode(
    episode_id: UUID, body: EpisodeUpdate, current_user: CurrentUser, session: SessionDep
) -> EpisodeResponse:
    svc = _make_services(session)
    return EpisodeResponse.model_validate(
        await svc["episode"].update(episode_id, body.model_dump(exclude_none=True))
    )


@router.delete("/episodes/{episode_id}", status_code=204, response_model=None)
async def delete_episode(episode_id: UUID, current_user: CurrentUser, session: SessionDep) -> None:
    svc = _make_services(session)
    await svc["episode"].delete(episode_id)


@router.get("/episodes/{episode_id}/evaluation", response_model=StoryEvaluationResponse | None)
async def get_episode_evaluation(
    episode_id: UUID, current_user: CurrentUser, session: SessionDep
) -> StoryEvaluationResponse | None:
    svc = _make_services(session)
    ev = await svc["episode"].get_evaluation(episode_id)
    return StoryEvaluationResponse.model_validate(ev) if ev else None


@router.post("/episodes/{episode_id}/evaluate", response_model=StoryEvaluationResponse)
async def evaluate_episode(
    episode_id: UUID, current_user: CurrentUser, session: SessionDep
) -> StoryEvaluationResponse:
    svc = _make_services(session)
    ev = await svc["eval"].evaluate_episode(episode_id)
    return StoryEvaluationResponse.model_validate(ev)


@router.get("/episodes/{episode_id}/versions", response_model=list[StoryVersionResponse])
async def get_episode_versions(
    episode_id: UUID, current_user: CurrentUser, session: SessionDep
) -> list[StoryVersionResponse]:
    svc = _make_services(session)
    versions = await svc["version"].list_versions("episode", episode_id)
    return [StoryVersionResponse.model_validate(v) for v in versions]


# ─────────────────────────────────────────────────────────────────────────────
# Story Scenes
# ─────────────────────────────────────────────────────────────────────────────

@router.post("/episodes/{episode_id}/scenes", response_model=StorySceneResponse, status_code=201)
async def create_story_scene(
    episode_id: UUID,
    body: StorySceneCreate,
    current_user: CurrentUser,
    session: SessionDep,
) -> StorySceneResponse:
    svc = _make_services(session)
    scene = await svc["scene"].create(episode_id, body.model_dump())
    return StorySceneResponse.model_validate(scene)


@router.get("/episodes/{episode_id}/scenes", response_model=StorySceneListResponse)
async def list_story_scenes(
    episode_id: UUID,
    current_user: CurrentUser,
    session: SessionDep,
    pagination: Annotated[PaginationParams, Depends(_pagination)],
) -> StorySceneListResponse:
    svc = _make_services(session)
    result = await svc["scene"].list_by_episode(episode_id, pagination)
    return StorySceneListResponse(
        items=[StorySceneResponse.model_validate(s) for s in result.items],
        meta=_meta(result),
    )


@router.get("/scenes/{scene_id}", response_model=StorySceneResponse)
async def get_story_scene(scene_id: UUID, current_user: CurrentUser, session: SessionDep) -> StorySceneResponse:
    svc = _make_services(session)
    return StorySceneResponse.model_validate(await svc["scene"].get_by_id(scene_id))


@router.patch("/scenes/{scene_id}", response_model=StorySceneResponse)
async def update_story_scene(
    scene_id: UUID, body: StorySceneUpdate, current_user: CurrentUser, session: SessionDep
) -> StorySceneResponse:
    svc = _make_services(session)
    return StorySceneResponse.model_validate(
        await svc["scene"].update(scene_id, body.model_dump(exclude_none=True))
    )


@router.delete("/scenes/{scene_id}", status_code=204, response_model=None)
async def delete_story_scene(scene_id: UUID, current_user: CurrentUser, session: SessionDep) -> None:
    svc = _make_services(session)
    await svc["scene"].delete(scene_id)


# ─────────────────────────────────────────────────────────────────────────────
# Story Ideas
# ─────────────────────────────────────────────────────────────────────────────

@router.post("/projects/{project_id}/ideas/generate", response_model=list[StoryIdeaResponse], status_code=201)
async def generate_ideas(
    project_id: UUID,
    body: GenerateIdeasRequest,
    current_user: CurrentUser,
    session: SessionDep,
) -> list[StoryIdeaResponse]:
    svc = _make_services(session)
    world_ctx = None
    if body.world_id:
        world = await svc["world"].get_by_id(body.world_id)
        world_ctx = {"name": world.name, "description": world.description}
    ideas = await svc["idea"].generate_ideas(
        project_id, genre=body.genre, story_type=body.story_type,
        count=body.count, world_id=body.world_id, world_context=world_ctx,
    )
    return [StoryIdeaResponse.model_validate(i) for i in ideas]


@router.post("/projects/{project_id}/ideas", response_model=StoryIdeaResponse, status_code=201)
async def create_idea(
    project_id: UUID,
    body: StoryIdeaCreate,
    current_user: CurrentUser,
    session: SessionDep,
) -> StoryIdeaResponse:
    from database.models.intelligence import StoryIdea
    from repositories.intelligence_repository import StoryIdeaRepository
    session_repo = StoryIdeaRepository(session)
    idea = StoryIdea(project_id=project_id, **body.model_dump())
    created = await session_repo.create(idea)
    return StoryIdeaResponse.model_validate(created)


@router.get("/projects/{project_id}/ideas", response_model=StoryIdeaListResponse)
async def list_ideas(
    project_id: UUID,
    current_user: CurrentUser,
    session: SessionDep,
    pagination: Annotated[PaginationParams, Depends(_pagination)],
    idea_status: str | None = Query(None),
) -> StoryIdeaListResponse:
    svc = _make_services(session)
    result = await svc["idea"].list_by_project(project_id, pagination, status=idea_status)
    return StoryIdeaListResponse(
        items=[StoryIdeaResponse.model_validate(i) for i in result.items],
        meta=_meta(result),
    )


@router.patch("/ideas/{idea_id}", response_model=StoryIdeaResponse)
async def update_idea(
    idea_id: UUID, body: StoryIdeaUpdate, current_user: CurrentUser, session: SessionDep
) -> StoryIdeaResponse:
    svc = _make_services(session)
    return StoryIdeaResponse.model_validate(
        await svc["idea"].update_status(idea_id, body.status or "idea") if body.status else
        await svc["idea"].get_by_id(idea_id)
    )


@router.delete("/ideas/{idea_id}", status_code=204, response_model=None)
async def delete_idea(idea_id: UUID, current_user: CurrentUser, session: SessionDep) -> None:
    svc = _make_services(session)
    await svc["idea"].delete(idea_id)


# ─────────────────────────────────────────────────────────────────────────────
# Story Memory
# ─────────────────────────────────────────────────────────────────────────────

@router.post("/worlds/{world_id}/memory", response_model=StoryMemoryResponse, status_code=201)
async def store_memory(
    world_id: UUID,
    body: StoryMemoryCreate,
    current_user: CurrentUser,
    session: SessionDep,
) -> StoryMemoryResponse:
    svc = _make_services(session)
    mem = await svc["memory"].store(
        world_id, body.memory_type, body.key, body.value,
        episode_id=body.episode_id,
    )
    return StoryMemoryResponse.model_validate(mem)


@router.get("/worlds/{world_id}/memory", response_model=StoryMemoryListResponse)
async def list_memory(
    world_id: UUID,
    current_user: CurrentUser,
    session: SessionDep,
    pagination: Annotated[PaginationParams, Depends(_pagination)],
    memory_type: str | None = Query(None),
) -> StoryMemoryListResponse:
    svc = _make_services(session)
    result = await svc["memory"].get_memories(world_id, pagination, memory_type=memory_type)
    return StoryMemoryListResponse(
        items=[StoryMemoryResponse.model_validate(m) for m in result.items],
        meta=_meta(result),
    )


# ─────────────────────────────────────────────────────────────────────────────
# Generation Jobs (queue / status)
# ─────────────────────────────────────────────────────────────────────────────

@router.get("/projects/{project_id}/jobs", response_model=GenerationJobListResponse)
async def list_jobs(
    project_id: UUID,
    current_user: CurrentUser,
    session: SessionDep,
    pagination: Annotated[PaginationParams, Depends(_pagination)],
    job_status: str | None = Query(None),
    job_type: str | None = Query(None),
) -> GenerationJobListResponse:
    svc = _make_services(session)
    result = await svc["jobs"].list_jobs(
        project_id, pagination, status=job_status, job_type=job_type
    )
    return GenerationJobListResponse(
        items=[GenerationJobResponse.model_validate(j) for j in result.items],
        meta=_meta(result),
    )


@router.get("/jobs/{job_id}", response_model=GenerationJobResponse)
async def get_job(job_id: UUID, current_user: CurrentUser, session: SessionDep) -> GenerationJobResponse:
    svc = _make_services(session)
    return GenerationJobResponse.model_validate(await svc["jobs"].get_job(job_id))


@router.get("/jobs/{job_id}/logs")
async def get_job_logs(job_id: UUID, current_user: CurrentUser, session: SessionDep) -> dict[str, Any]:
    svc = _make_services(session)
    logs = await svc["jobs"].get_logs(job_id)
    return {"logs": [
        {
            "step_name": l.step_name, "duration_ms": l.duration_ms,
            "tokens_used": l.tokens_used, "is_error": l.is_error,
            "score": l.score, "created_at": l.created_at.isoformat(),
        }
        for l in logs
    ]}


# ─────────────────────────────────────────────────────────────────────────────
# Generation / Dispatch
# ─────────────────────────────────────────────────────────────────────────────

@router.post("/projects/{project_id}/generate", response_model=DispatchResponse)
async def run_full_pipeline(
    project_id: UUID,
    body: RunFullPipelineRequest,
    current_user: CurrentUser,
    session: SessionDep,
) -> DispatchResponse:
    """
    Dispatch the full story generation pipeline.
    Uses Celery when available, falls back to synchronous execution otherwise.
    """
    from apps.worker.dispatcher import get_dispatcher
    from apps.worker.tasks.intelligence_tasks import si_run_full_pipeline

    svc = _make_services(session)
    job = await svc["jobs"].create_job(
        job_type="generate_full_pipeline",
        project_id=project_id,
        entity_type="world",
    )
    dispatcher = get_dispatcher()
    dispatch_result = await dispatcher.dispatch(
        celery_task=si_run_full_pipeline,
        core_coro_factory=lambda: _run_pipeline_core(
            project_id=project_id, job_id=job.id,
            body=body, session=session,
        ),
        job_id=str(job.id),
        queue="ai",
        task_kwargs={
            "project_id": str(project_id),
            "world_id": str(body.world_id) if body.world_id else None,
            "genre": body.genre,
            "story_type": body.story_type,
            "episode_count": body.episode_count,
            "world_data": body.world_data,
            "knowledge_collection_id": str(body.knowledge_collection_id) if body.knowledge_collection_id else None,
        },
    )
    return DispatchResponse(**dispatch_result)


async def _run_pipeline_core(
    project_id: UUID,
    job_id: UUID,
    body: RunFullPipelineRequest,
    session: Any,
) -> dict[str, Any]:
    svc = _make_services(session)
    return await svc["orchestrator"].run_full_pipeline(
        project_id=project_id,
        job_id=job_id,
        world_id=body.world_id,
        genre=body.genre,
        story_type=body.story_type,
        episode_count=body.episode_count,
        world_data=body.world_data,
        knowledge_collection_id=body.knowledge_collection_id,
    )


@router.post("/seasons/{season_id}/generate-episode", response_model=DispatchResponse)
async def generate_episode(
    season_id: UUID,
    body: GenerateEpisodeRequest,
    current_user: CurrentUser,
    session: SessionDep,
) -> DispatchResponse:
    from apps.worker.dispatcher import get_dispatcher
    from apps.worker.tasks.intelligence_tasks import si_generate_episode

    season = None
    svc = _make_services(session)
    season = await svc["season"].get_by_id(season_id)
    job = await svc["jobs"].create_job(
        job_type="generate_episode",
        project_id=season.project_id,
        entity_type="episode",
    )
    dispatcher = get_dispatcher()
    dispatch_result = await dispatcher.dispatch(
        celery_task=si_generate_episode,
        core_coro_factory=lambda: _run_episode_core(
            project_id=season.project_id, job_id=job.id,
            season_id=season_id, world_id=body.world_id,
            session=session, knowledge_collection_id=body.knowledge_collection_id,
        ),
        job_id=str(job.id),
        queue="ai",
        task_kwargs={
            "project_id": str(season.project_id),
            "season_id": str(season_id),
            "world_id": str(body.world_id),
            "knowledge_collection_id": str(body.knowledge_collection_id) if body.knowledge_collection_id else None,
        },
    )
    return DispatchResponse(**dispatch_result)


async def _run_episode_core(
    project_id: UUID,
    job_id: UUID,
    season_id: UUID,
    world_id: UUID,
    session: Any,
    knowledge_collection_id: UUID | None = None,
) -> dict[str, Any]:
    svc = _make_services(session)
    return await svc["orchestrator"].generate_episode_only(
        project_id=project_id, job_id=job_id,
        season_id=season_id, world_id=world_id,
        knowledge_collection_id=knowledge_collection_id,
    )


# ─────────────────────────────────────────────────────────────────────────────
# Analytics
# ─────────────────────────────────────────────────────────────────────────────

@router.get("/projects/{project_id}/stats", response_model=StoryIntelligenceStats)
async def get_stats(
    project_id: UUID,
    current_user: CurrentUser,
    session: SessionDep,
) -> StoryIntelligenceStats:
    from repositories.intelligence_repository import (
        WorldRepository, SeasonRepository, EpisodeRepository,
        StorySceneRepository, StoryIdeaRepository, StoryMemoryRepository,
        GenerationJobRepository,
    )
    from sqlalchemy import func, select

    async def count_all(Model, filters: dict | None = None):
        stmt = select(func.count(Model.id))
        if filters:
            for k, v in filters.items():
                stmt = stmt.where(getattr(Model, k) == v)
        result = await session.execute(stmt)
        return result.scalar_one()

    from database.models.intelligence import (
        World, Season, Episode, StoryScene, StoryIdea, StoryMemory, GenerationJob
    )
    from sqlalchemy import func, select

    worlds = await count_all(World, {"project_id": project_id})
    seasons = await count_all(Season, {"project_id": project_id})
    episodes = await count_all(Episode, {"project_id": project_id})
    ideas = await count_all(StoryIdea, {"project_id": project_id})
    jobs_svc = _make_services(session)["jobs"]
    job_counts = await jobs_svc.status_counts()

    # Count scenes and memories indirectly
    from sqlalchemy import text
    scenes_res = await session.execute(
        text("SELECT COUNT(*) FROM si_story_scenes ss JOIN si_episodes e ON ss.episode_id = e.id WHERE e.project_id = :pid"),
        {"pid": str(project_id)}
    )
    scenes = scenes_res.scalar_one() or 0

    memories_res = await session.execute(
        text("SELECT COUNT(*) FROM si_story_memory sm JOIN si_worlds w ON sm.world_id = w.id WHERE w.project_id = :pid"),
        {"pid": str(project_id)}
    )
    memories = memories_res.scalar_one() or 0

    # Average story score for this project
    avg_res = await session.execute(
        text("SELECT AVG(story_score) FROM si_episodes WHERE project_id = :pid AND story_score > 0"),
        {"pid": str(project_id)}
    )
    avg_score = float(avg_res.scalar_one() or 0.0)

    return StoryIntelligenceStats(
        worlds=worlds, seasons=seasons, episodes=episodes, scenes=scenes,
        ideas=ideas, memories=memories,
        jobs_by_status=job_counts,
        avg_story_score=round(avg_score, 2),
    )

"""
Phase 3 — Story Intelligence Celery tasks.

Each task follows the pattern:
  - A @celery_app.task decorator wrapping a thin sync shell
  - _run_async() to bridge sync Celery ↔ async business logic
  - DLQ routing on max retries exhaustion
  - All actual logic delegates to StoryIntelligenceOrchestrator (no logic here)

TaskDispatcher calls these via apply_async() when Redis is available,
or calls the underlying async core function directly in sync fallback mode.
"""
from __future__ import annotations

import os
from typing import Any
from uuid import UUID

from celery import Task
from celery.utils.log import get_task_logger
from apps.worker.async_utils import run_async as _run_async
from apps.worker.main import celery_app
from apps.worker.tasks.dead_letter import dead_letter_task

logger = get_task_logger(__name__)



# ---------------------------------------------------------------------------
# Async core functions — called directly by dispatcher in sync fallback mode
# These must be pure async functions with no Celery dependencies.
# ---------------------------------------------------------------------------

async def _run_full_pipeline_core(
    project_id: str,
    job_id: str,
    world_id: str | None = None,
    genre: str = "comedy",
    story_type: str = "comedy",
    episode_count: int | None = None,
    world_data: dict[str, Any] | None = None,
    knowledge_collection_id: str | None = None,
) -> dict[str, Any]:
    from database.connection import get_session
    from agents.registry import get_provider_registry
    from agents.interfaces.llm_provider import LLMProvider
    from repositories.intelligence_repository import (
        WorldRepository, StoryIdeaRepository, SeasonRepository, EpisodeRepository,
        StorySceneRepository, StoryEvaluationRepository, StoryMemoryRepository,
        GenerationJobRepository, GenerationLogRepository, RetryQueueRepository,
        StoryVersionRepository,
    )
    from services.intelligence.orchestrator import StoryIntelligenceOrchestrator
    from services.intelligence.world_service import WorldService
    from services.intelligence.idea_service import StoryIdeaService
    from services.intelligence.season_service import SeasonService
    from services.intelligence.episode_service import EpisodeService
    from services.intelligence.scene_service import StorySceneService
    from services.intelligence.evaluator_service import StoryEvaluatorService
    from services.intelligence.memory_service import MemoryService
    from services.intelligence.job_service import GenerationJobService
    from services.intelligence.version_service import VersionService
    from services.knowledge import build_retrieval_service

    llm = get_provider_registry().resolve(LLMProvider)

    async for session in get_session():
        version_repo = StoryVersionRepository(session)
        orchestrator = StoryIntelligenceOrchestrator(
            world_svc=WorldService(WorldRepository(session), version_repo),
            idea_svc=StoryIdeaService(StoryIdeaRepository(session), llm),
            season_svc=SeasonService(SeasonRepository(session), llm),
            episode_svc=EpisodeService(
                EpisodeRepository(session), StoryEvaluationRepository(session), version_repo, llm
            ),
            scene_svc=StorySceneService(StorySceneRepository(session), llm),
            evaluator_svc=StoryEvaluatorService(
                EpisodeRepository(session), StoryEvaluationRepository(session), llm
            ),
            memory_svc=MemoryService(StoryMemoryRepository(session), llm),
            job_svc=GenerationJobService(
                GenerationJobRepository(session),
                GenerationLogRepository(session),
                RetryQueueRepository(session),
            ),
            version_svc=VersionService(version_repo),
            llm=llm,
            retrieval_svc=build_retrieval_service(session),
        )
        return await orchestrator.run_full_pipeline(
            project_id=UUID(project_id),
            job_id=UUID(job_id),
            world_id=UUID(world_id) if world_id else None,
            genre=genre,
            story_type=story_type,
            episode_count=episode_count,
            world_data=world_data or {},
            knowledge_collection_id=UUID(knowledge_collection_id) if knowledge_collection_id else None,
        )
    return {}


async def _generate_episode_core(
    project_id: str,
    job_id: str,
    season_id: str,
    world_id: str,
    knowledge_collection_id: str | None = None,
) -> dict[str, Any]:
    from database.connection import get_session
    from agents.registry import get_provider_registry
    from agents.interfaces.llm_provider import LLMProvider
    from repositories.intelligence_repository import (
        WorldRepository, SeasonRepository, EpisodeRepository,
        StorySceneRepository, StoryEvaluationRepository, StoryMemoryRepository,
        GenerationJobRepository, GenerationLogRepository, RetryQueueRepository,
        StoryVersionRepository, StoryIdeaRepository,
    )
    from services.intelligence.orchestrator import StoryIntelligenceOrchestrator
    from services.intelligence.world_service import WorldService
    from services.intelligence.idea_service import StoryIdeaService
    from services.intelligence.season_service import SeasonService
    from services.intelligence.episode_service import EpisodeService
    from services.intelligence.scene_service import StorySceneService
    from services.intelligence.evaluator_service import StoryEvaluatorService
    from services.intelligence.memory_service import MemoryService
    from services.intelligence.job_service import GenerationJobService
    from services.intelligence.version_service import VersionService
    from services.knowledge import build_retrieval_service

    llm = get_provider_registry().resolve(LLMProvider)

    async for session in get_session():
        version_repo = StoryVersionRepository(session)
        orchestrator = StoryIntelligenceOrchestrator(
            world_svc=WorldService(WorldRepository(session), version_repo),
            idea_svc=StoryIdeaService(StoryIdeaRepository(session), llm),
            season_svc=SeasonService(SeasonRepository(session), llm),
            episode_svc=EpisodeService(
                EpisodeRepository(session), StoryEvaluationRepository(session), version_repo, llm
            ),
            scene_svc=StorySceneService(StorySceneRepository(session), llm),
            evaluator_svc=StoryEvaluatorService(
                EpisodeRepository(session), StoryEvaluationRepository(session), llm
            ),
            memory_svc=MemoryService(StoryMemoryRepository(session), llm),
            job_svc=GenerationJobService(
                GenerationJobRepository(session),
                GenerationLogRepository(session),
                RetryQueueRepository(session),
            ),
            version_svc=VersionService(version_repo),
            llm=llm,
            retrieval_svc=build_retrieval_service(session),
        )
        return await orchestrator.generate_episode_only(
            project_id=UUID(project_id),
            job_id=UUID(job_id),
            season_id=UUID(season_id),
            world_id=UUID(world_id),
            knowledge_collection_id=UUID(knowledge_collection_id) if knowledge_collection_id else None,
        )
    return {}


# ---------------------------------------------------------------------------
# Celery Task wrappers
# ---------------------------------------------------------------------------

@celery_app.task(
    bind=True,
    name="intelligence.run_full_pipeline",
    queue="ai",
    max_retries=3,
    default_retry_delay=60,
    acks_late=True,
)
def si_run_full_pipeline(
    self: Task,
    project_id: str,
    job_id: str,
    world_id: str | None = None,
    genre: str = "comedy",
    story_type: str = "comedy",
    episode_count: int | None = None,
    world_data: dict[str, Any] | None = None,
    knowledge_collection_id: str | None = None,
) -> dict[str, Any]:
    logger.info(f"si_run_full_pipeline start job_id={job_id}")
    try:
        return _run_async(_run_full_pipeline_core(
            project_id=project_id, job_id=job_id,
            world_id=world_id, genre=genre, story_type=story_type,
            episode_count=episode_count, world_data=world_data,
            knowledge_collection_id=knowledge_collection_id,
        ))
    except Exception as exc:
        logger.error(f"si_run_full_pipeline failed job_id={job_id} error={exc}")
        try:
            raise self.retry(exc=exc, countdown=90)
        except self.MaxRetriesExceededError:
            dead_letter_task.apply_async(
                kwargs={
                    "task_name": "intelligence.run_full_pipeline",
                    "task_args": {"job_id": job_id},
                    "error": str(exc),
                },
                queue="dlq",
            )
            raise


@celery_app.task(
    bind=True,
    name="intelligence.generate_episode",
    queue="ai",
    max_retries=3,
    default_retry_delay=60,
    acks_late=True,
)
def si_generate_episode(
    self: Task,
    project_id: str,
    job_id: str,
    season_id: str,
    world_id: str,
    knowledge_collection_id: str | None = None,
) -> dict[str, Any]:
    logger.info(f"si_generate_episode start job_id={job_id}")
    try:
        return _run_async(_generate_episode_core(
            project_id=project_id, job_id=job_id,
            season_id=season_id, world_id=world_id,
            knowledge_collection_id=knowledge_collection_id,
        ))
    except Exception as exc:
        logger.error(f"si_generate_episode failed job_id={job_id} error={exc}")
        try:
            raise self.retry(exc=exc, countdown=60)
        except self.MaxRetriesExceededError:
            dead_letter_task.apply_async(
                kwargs={"task_name": "intelligence.generate_episode", "task_args": {"job_id": job_id}, "error": str(exc)},
                queue="dlq",
            )
            raise
"""
StoryIntelligenceOrchestrator — coordinates the full generation pipeline.

Pipeline stages:
  1. BuildWorld (if no world specified)
  2. GenerateIdea
  3. PlanSeason
  4. PlanEpisode
  5. BreakdownScenes
  6. GenerateDialogue (per scene)
  7. GenerateNarration (per scene)
  8. GenerateImagePrompt (per scene)
  9. GenerateAnimationPrompt (per scene)
  10. EvaluateQuality
  11. AutoRetry (if below threshold)
  12. SaveMemory

The orchestrator is designed to be called either:
  - Directly by an API route (sync path, no Celery required)
  - From a Celery task (async path)
Both paths run the same logic — the dispatcher decides which one.
"""
from __future__ import annotations

import structlog
from typing import Any
from uuid import UUID

from agents.interfaces.llm_provider import LLMProvider
from apps.api.config import get_settings
from database.models.intelligence import (
    Episode, GenerationJob, Season, StoryIdea, World,
)
from repositories.intelligence_repository import (
    EpisodeRepository, GenerationJobRepository, GenerationLogRepository,
    RetryQueueRepository, SeasonRepository, StoryEvaluationRepository,
    StoryIdeaRepository, StoryMemoryRepository, StorySceneRepository,
    StoryVersionRepository, WorldRepository,
)
from services.intelligence.episode_service import EpisodeService
from services.intelligence.evaluator_service import StoryEvaluatorService
from services.intelligence.idea_service import StoryIdeaService
from services.intelligence.job_service import GenerationJobService
from services.intelligence.memory_service import MemoryService
from services.intelligence.scene_service import StorySceneService
from services.intelligence.season_service import SeasonService
from services.intelligence.version_service import VersionService
from services.intelligence.world_service import WorldService

logger = structlog.get_logger()


class StoryIntelligenceOrchestrator:
    """
    Coordinates all Phase 3 services to run the full story generation pipeline.
    This is the single entry point for both sync and async dispatch paths.
    """

    def __init__(
        self,
        world_svc: WorldService,
        idea_svc: StoryIdeaService,
        season_svc: SeasonService,
        episode_svc: EpisodeService,
        scene_svc: StorySceneService,
        evaluator_svc: StoryEvaluatorService,
        memory_svc: MemoryService,
        job_svc: GenerationJobService,
        version_svc: VersionService,
        llm: LLMProvider,
    ) -> None:
        self._world = world_svc
        self._idea = idea_svc
        self._season = season_svc
        self._episode = episode_svc
        self._scene = scene_svc
        self._evaluator = evaluator_svc
        self._memory = memory_svc
        self._jobs = job_svc
        self._versions = version_svc
        self._llm = llm
        self._cfg = get_settings()

    # ──────────────────────────────────────────────────────────────────────────
    # Public pipeline entry points
    # ──────────────────────────────────────────────────────────────────────────

    async def run_full_pipeline(
        self,
        project_id: UUID,
        job_id: UUID,
        *,
        world_id: UUID | None = None,
        genre: str = "comedy",
        story_type: str = "comedy",
        episode_count: int | None = None,
        world_data: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """
        Full pipeline: World → Idea → Season → Episode → Scenes → Eval → Memory.
        Updates job progress throughout.  Returns a summary dict.
        """
        try:
            await self._jobs.start_job(job_id, mode="sync")
            result: dict[str, Any] = {}

            # Stage 1: World
            await self._jobs.update_progress(job_id, 5, "Building world")
            if world_id:
                world = await self._world.get_by_id(world_id)
            else:
                world = await self._build_world(project_id, world_data or {})
            result["world_id"] = str(world.id)
            logger.info("pipeline_world_ready", world_id=str(world.id))

            # Stage 2: Story Idea
            await self._jobs.update_progress(job_id, 15, "Generating story idea")
            ideas = await self._idea.generate_ideas(
                project_id, genre=genre, story_type=story_type,
                count=1, world_id=world.id,
                world_context={"name": world.name, "description": world.description},
            )
            idea = ideas[0]
            result["idea_id"] = str(idea.id)
            logger.info("pipeline_idea_ready", idea_id=str(idea.id))

            # Stage 3: Season Plan
            await self._jobs.update_progress(job_id, 25, "Planning season")
            season = await self._create_season(project_id, world, idea, episode_count)
            result["season_id"] = str(season.id)
            logger.info("pipeline_season_ready", season_id=str(season.id))

            # Stage 4: Episode Plan
            await self._jobs.update_progress(job_id, 40, "Planning episode")
            episode = await self._create_episode(project_id, world, season, idea)
            result["episode_id"] = str(episode.id)
            logger.info("pipeline_episode_ready", episode_id=str(episode.id))

            # Stage 5: Scene Breakdown
            await self._jobs.update_progress(job_id, 55, "Breaking down scenes")
            scenes = await self._create_scenes(world, episode)
            result["scene_count"] = len(scenes)
            logger.info("pipeline_scenes_ready", count=len(scenes))

            # Stage 6–9: Dialogue + Narration + Prompts per scene
            for i, scene in enumerate(scenes):
                pct = 55 + int(20 * (i + 1) / max(len(scenes), 1))
                await self._jobs.update_progress(job_id, pct, f"Generating content for scene {i+1}")
                await self._enrich_scene(world, episode, scene)

            # Stage 10: Quality Evaluation
            await self._jobs.update_progress(job_id, 85, "Evaluating quality")
            evaluation = await self._evaluator.evaluate_episode(episode.id)
            result["quality_score"] = evaluation.overall_score
            result["approved"] = evaluation.approved
            logger.info("pipeline_evaluated", score=evaluation.overall_score)

            # Stage 11: Auto-retry if below threshold
            if not evaluation.approved and episode.generation_metadata.get("retry_count", 0) < self._cfg.SI_MAX_RETRIES:
                await self._jobs.update_progress(job_id, 88, "Auto-improving episode quality")
                episode = await self._auto_improve_episode(world, episode, evaluation)
                result["improved"] = True

            # Stage 12: Save Memory
            await self._jobs.update_progress(job_id, 95, "Saving story memory")
            memories = await self._memory.ai_extract_and_save(
                world_id=world.id,
                episode_id=episode.id,
                episode_content={
                    "title": episode.title,
                    "summary": episode.summary,
                    "moral": episode.moral,
                },
            )
            result["memories_stored"] = len(memories)

            await self._jobs.complete_job(job_id, result)
            logger.info("pipeline_complete", job_id=str(job_id))
            return result

        except Exception as exc:
            await self._jobs.fail_job(job_id, str(exc))
            logger.error("pipeline_failed", job_id=str(job_id), error=str(exc))
            raise

    async def generate_episode_only(
        self,
        project_id: UUID,
        job_id: UUID,
        season_id: UUID,
        world_id: UUID,
    ) -> dict[str, Any]:
        """Generate a single episode (including scenes) within an existing season."""
        await self._jobs.start_job(job_id, mode="sync")
        try:
            world = await self._world.get_by_id(world_id)
            season = await self._season.get_by_id(season_id)
            idea = StoryIdea(
                project_id=project_id, world_id=world_id,
                title=season.title, premise=season.description,
                genre="comedy", tone="light", story_type="comedy",
                target_audience="general",
            )

            await self._jobs.update_progress(job_id, 20, "Planning episode")
            episode = await self._create_episode(project_id, world, season, idea)

            await self._jobs.update_progress(job_id, 50, "Breaking scenes")
            scenes = await self._create_scenes(world, episode)

            for i, scene in enumerate(scenes):
                pct = 50 + int(35 * (i + 1) / max(len(scenes), 1))
                await self._jobs.update_progress(job_id, pct, f"Scene {i+1} content")
                await self._enrich_scene(world, episode, scene)

            await self._jobs.update_progress(job_id, 90, "Evaluating")
            evaluation = await self._evaluator.evaluate_episode(episode.id)

            result = {
                "episode_id": str(episode.id),
                "scene_count": len(scenes),
                "quality_score": evaluation.overall_score,
                "approved": evaluation.approved,
            }
            await self._jobs.complete_job(job_id, result)
            return result
        except Exception as exc:
            await self._jobs.fail_job(job_id, str(exc))
            raise

    # ──────────────────────────────────────────────────────────────────────────
    # Private helpers
    # ──────────────────────────────────────────────────────────────────────────

    async def _build_world(self, project_id: UUID, world_data: dict[str, Any]) -> World:
        if not world_data.get("name"):
            ai_data = await self._llm.generate_json(
                "Build a detailed story world for a Telugu family comedy animation. "
                "Include name, description, rules (list), locations (dict), factions (list), lore.",
                system="You are a world-building AI. Return ONLY valid JSON.",
                temperature=self._cfg.SI_AI_TEMPERATURE,
            )
            world_data = {**ai_data, **world_data}

        return await self._world.create(project_id, {
            "name": world_data.get("name", "New World"),
            "description": world_data.get("description", ""),
            "rules": world_data.get("rules", []),
            "locations": world_data.get("locations", {}),
            "timeline_data": world_data.get("timeline_data", []),
            "factions": world_data.get("factions", []),
            "objects": world_data.get("objects", []),
            "lore": world_data.get("lore", ""),
        })

    async def _create_season(
        self, project_id: UUID, world: World, idea: StoryIdea, episode_count: int | None
    ) -> Season:
        plan = await self._season.ai_plan_season(
            world_context={"name": world.name, "description": world.description},
            story_idea=idea.premise,
            season_number=1,
            episode_count=episode_count,
        )
        return await self._season.create(world.id, project_id, {
            "title": plan.get("title", idea.title),
            "description": plan.get("description", ""),
            "story_arc": plan.get("story_arc", ""),
            "episode_count": episode_count or self._cfg.SI_DEFAULT_EPISODES_PER_SEASON,
        })

    async def _create_episode(
        self, project_id: UUID, world: World, season: Season, idea: StoryIdea
    ) -> Episode:
        plan = await self._episode.ai_plan_episode(
            world_context={"name": world.name, "description": world.description},
            season_context={"title": season.title, "story_arc": season.story_arc},
            episode_number=1,
        )
        return await self._episode.create(season.id, world.id, project_id, {
            "title": plan.get("title", idea.title),
            "summary": plan.get("summary", idea.premise),
            "opening": plan.get("opening", ""),
            "middle": plan.get("middle", ""),
            "ending": plan.get("ending", ""),
            "moral": plan.get("moral", ""),
            "duration_target_seconds": self._cfg.SI_TARGET_EPISODE_LENGTH_SECONDS,
            "generation_metadata": plan,
        })

    async def _create_scenes(self, world: World, episode: Episode) -> list[Any]:
        from database.models.intelligence import StoryScene
        scene_plans = await self._scene.ai_plan_scenes(
            episode_context={
                "title": episode.title, "summary": episode.summary,
                "opening": episode.opening, "middle": episode.middle, "ending": episode.ending,
            },
            world_context={"name": world.name},
        )
        scenes = []
        for plan in scene_plans:
            scene = await self._scene.create(episode.id, {
                "scene_number": plan.get("scene_number", len(scenes) + 1),
                "scene_goal": plan.get("scene_goal", ""),
                "location": plan.get("location", ""),
                "character_names": plan.get("character_names", []),
                "camera_direction": plan.get("camera_direction", ""),
                "duration_seconds": float(plan.get("duration_seconds", 60)),
            })
            scenes.append(scene)
        return scenes

    async def _enrich_scene(
        self, world: World, episode: Episode, scene: Any
    ) -> None:
        world_ctx = {"name": world.name}
        episode_ctx = {"title": episode.title}

        dialogue = await self._scene.ai_generate_dialogue(scene, world_ctx)
        narration = await self._scene.ai_generate_narration(scene, episode_ctx)
        image_prompt = await self._scene.ai_generate_image_prompt(scene)
        animation_prompt = await self._scene.ai_generate_animation_prompt(scene)

        await self._scene.update(scene.id, {
            "dialogue": dialogue,
            "narration": narration,
            "image_prompt": image_prompt,
            "animation_prompt": animation_prompt,
            "status": "generated",
        })

    async def _auto_improve_episode(
        self,
        world: World,
        episode: Episode,
        evaluation: Any,
    ) -> Episode:
        feedback = evaluation.feedback.get("improvements", [])
        feedback_text = "; ".join(feedback) if feedback else "Improve overall quality"
        improve_prompt = (
            f"Improve this episode based on feedback:\n"
            f"Title: {episode.title}\n"
            f"Current summary: {episode.summary}\n"
            f"Feedback: {feedback_text}\n\n"
            "Return JSON with improved: title, summary, opening, middle, ending, moral."
        )
        improved = await self._llm.generate_json(
            improve_prompt,
            system="You are a story improvement AI. Return ONLY valid JSON.",
            temperature=self._cfg.SI_AI_TEMPERATURE,
        )
        meta = dict(episode.generation_metadata)
        meta["retry_count"] = meta.get("retry_count", 0) + 1
        return await self._episode.update(episode.id, {
            "title": improved.get("title", episode.title),
            "summary": improved.get("summary", episode.summary),
            "opening": improved.get("opening", episode.opening),
            "middle": improved.get("middle", episode.middle),
            "ending": improved.get("ending", episode.ending),
            "moral": improved.get("moral", episode.moral),
            "generation_metadata": meta,
        })

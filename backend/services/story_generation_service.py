"""
StoryGenerationService — orchestrates story creation via the LLM Provider.

Design constraints (enforced):
  ✓ Depends only on LLMProvider interface — never imports OllamaProvider
  ✓ Uses ProviderRegistry for provider lookup — no hard-coded instantiation
  ✓ Dispatches Celery tasks for full pipeline execution
  ✓ Returns progress run_id for WebSocket streaming
"""
from __future__ import annotations

import uuid
from typing import Any

import structlog

from agents.interfaces.llm_provider import LLMProvider
from agents.registry import ProviderRegistry, get_provider_registry

logger = structlog.get_logger()


class StoryGenerationService:
    """
    High-level service for generating stories.

    Injects LLMProvider via constructor — the caller (FastAPI dependency, test, etc.)
    decides which concrete provider to use by populating the ProviderRegistry.
    """

    def __init__(
        self,
        llm: LLMProvider,
        registry: ProviderRegistry | None = None,
    ) -> None:
        self._llm = llm
        self._registry = registry or get_provider_registry()

    # ------------------------------------------------------------------
    # Synchronous quick generation (short stories, previews)
    # ------------------------------------------------------------------

    async def generate_story_outline(
        self,
        story_prompt: str,
        plugin_id: str,
        language: str = "Telugu",
        scene_count: int = 5,
        episode_title: str = "",
    ) -> dict[str, Any]:
        """
        Generate a story outline directly (no Celery, no pipeline).
        Used for quick previews and single-scene generation.
        Returns the parsed story dict.
        """
        from workflow.steps.story_step import StoryGenerationStep
        from workflow.context import WorkflowContext

        # Build a minimal context for the step
        ctx = WorkflowContext(
            story_id=str(uuid.uuid4()),
            project_id="preview",
            user_id="system",
            plugin_id=plugin_id,
            settings={
                "story_prompt": story_prompt,
                "episode_title": episode_title,
                "scene_count": scene_count,
                "language": language,
            },
        )

        step = StoryGenerationStep(llm=self._llm)
        result = await step.run(ctx)
        if not result.success:
            raise RuntimeError(f"Story generation failed: {result.error}")

        return ctx.get_step_result("story_generation", {})

    # ------------------------------------------------------------------
    # Full async pipeline (dispatches Celery task chain)
    # ------------------------------------------------------------------

    def start_full_pipeline(
        self,
        story_id: str,
        project_id: str,
        user_id: str,
        plugin_id: str,
        settings: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """
        Dispatch the full generation pipeline as a Celery task.
        Returns {"run_id": str, "task_id": str} immediately.
        The client subscribes to /ws/progress/{run_id} for updates.
        """
        from apps.worker.tasks.workflow_tasks import run_pipeline

        run_id = str(uuid.uuid4())
        final_settings = settings or {}
        final_settings["_run_id"] = run_id

        task = run_pipeline.apply_async(
            kwargs={
                "story_id": story_id,
                "project_id": project_id,
                "user_id": user_id,
                "plugin_id": plugin_id,
                "settings": final_settings,
            },
            queue="ai",
        )

        logger.info(
            "pipeline_dispatched",
            story_id=story_id,
            run_id=run_id,
            task_id=task.id,
        )

        return {
            "run_id": run_id,
            "task_id": task.id,
            "ws_url": f"/api/v1/ws/progress/{run_id}",
            "status": "queued",
        }

    def resume_pipeline(self, run_id: str) -> dict[str, Any]:
        """Re-queue a failed or paused pipeline by run_id."""
        from apps.worker.tasks.workflow_tasks import resume_pipeline

        task = resume_pipeline.apply_async(
            kwargs={"run_id": run_id},
            queue="ai",
        )
        logger.info("pipeline_resume_dispatched", run_id=run_id, task_id=task.id)
        return {
            "run_id": run_id,
            "task_id": task.id,
            "status": "resuming",
        }

    async def get_pipeline_status(self, run_id: str) -> dict[str, Any] | None:
        """Fetch the latest persisted WorkflowContext for a run_id."""
        from workflow.executor import WorkflowExecutor
        executor = WorkflowExecutor()
        try:
            return await executor.get_status(run_id)
        finally:
            await executor.close()

    # ------------------------------------------------------------------
    # Story refinement helpers (pure LLM calls)
    # ------------------------------------------------------------------

    async def suggest_story_variations(
        self,
        original_prompt: str,
        plugin_id: str,
        count: int = 3,
    ) -> list[dict[str, Any]]:
        """
        Generate alternative story ideas based on the original prompt.
        Returns a list of {title, synopsis, suggested_prompt} dicts.
        """
        plugin_context = await self._get_plugin_context(plugin_id)
        genre = plugin_context.get("genre", "family comedy")

        prompt = (
            f"Generate {count} different {genre} story ideas inspired by: '{original_prompt}'.\n"
            "Return JSON array of objects with keys: title, synopsis (2 sentences), suggested_prompt.\n"
            "Reply with ONLY the JSON array."
        )
        variations = await self._llm.generate_json(prompt, temperature=0.9)
        if isinstance(variations, list):
            return variations
        return variations.get("variations", [])  # type: ignore[union-attr]

    async def refine_scene_dialogue(
        self,
        scene_description: str,
        characters: list[str],
        language: str,
        tone_notes: str = "",
    ) -> list[dict[str, Any]]:
        """
        Refine or regenerate dialogue for a single scene.
        Returns list of {character, line, emotion} dicts.
        """
        char_str = ", ".join(characters)
        prompt = (
            f"Write natural {language} dialogue for this scene:\n{scene_description}\n\n"
            f"Characters: {char_str}\n"
            f"Tone: {tone_notes or 'warm family comedy'}\n\n"
            'Return JSON array of: [{"character": "...", "line": "...", "emotion": "..."}]'
        )
        result = await self._llm.generate_json(prompt, temperature=0.75)
        return result if isinstance(result, list) else []

    async def generate_episode_thumbnail_prompt(
        self,
        story_title: str,
        synopsis: str,
        style_hint: str = "cartoon animation",
    ) -> str:
        """Generate an image prompt for the episode thumbnail."""
        prompt = (
            f"Write a detailed image generation prompt for a YouTube thumbnail.\n"
            f"Show title: {story_title}\n"
            f"Synopsis: {synopsis}\n"
            f"Style: {style_hint}\n"
            "Make it vibrant, eye-catching, and 16:9 aspect ratio friendly.\n"
            "Return ONLY the prompt text, no JSON."
        )
        return await self._llm.generate_text(prompt, temperature=0.7, max_tokens=200)

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    async def _get_plugin_context(self, plugin_id: str) -> dict[str, Any]:
        try:
            from plugins.registry import get_registry
            registry = get_registry()
            plugin = registry.get_plugin(plugin_id)
            if plugin:
                return plugin.get_prompt_context()
        except Exception:
            pass
        return {}


# ---------------------------------------------------------------------------
# FastAPI dependency
# ---------------------------------------------------------------------------

def get_story_generation_service() -> StoryGenerationService:
    """FastAPI Depends() helper — resolves LLMProvider from the registry."""
    llm: LLMProvider = get_provider_registry().resolve(LLMProvider)
    return StoryGenerationService(llm=llm)

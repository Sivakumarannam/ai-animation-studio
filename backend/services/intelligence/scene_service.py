"""ScenePlannerService — story scene CRUD and AI-driven planning."""
from __future__ import annotations

from typing import Any
from uuid import UUID

from agents.interfaces.llm_provider import LLMProvider
from apps.api.config import get_settings
from database.models.intelligence import StoryScene
from packages.core.exceptions import NotFoundError
from packages.utils.pagination import PaginatedResult, PaginationParams
from repositories.intelligence_repository import StorySceneRepository


class StorySceneService:
    def __init__(self, repo: StorySceneRepository, llm: LLMProvider) -> None:
        self._repo = repo
        self._llm = llm
        self._cfg = get_settings()

    async def create(self, episode_id: UUID, data: dict[str, Any]) -> StoryScene:
        scene = StoryScene(episode_id=episode_id, **data)
        return await self._repo.create(scene)

    async def get_by_id(self, scene_id: UUID) -> StoryScene:
        s = await self._repo.get_by_id(scene_id)
        if s is None:
            raise NotFoundError(f"StoryScene {scene_id} not found")
        return s

    async def list_by_episode(
        self, episode_id: UUID, pagination: PaginationParams
    ) -> PaginatedResult[StoryScene]:
        return await self._repo.get_by_episode(episode_id, pagination)

    async def update(self, scene_id: UUID, data: dict[str, Any]) -> StoryScene:
        scene = await self.get_by_id(scene_id)
        return await self._repo.update(scene, data)

    async def delete(self, scene_id: UUID) -> None:
        scene = await self.get_by_id(scene_id)
        await self._repo.delete(scene)

    async def ai_plan_scenes(
        self,
        episode_context: dict[str, Any],
        world_context: dict[str, Any],
        scene_count: int | None = None,
    ) -> list[dict[str, Any]]:
        count = scene_count or self._cfg.SI_DEFAULT_SCENE_COUNT
        prompt = (
            f"Break this episode into {count} scenes:\n"
            f"Episode: {episode_context.get('title', '')}\n"
            f"Summary: {episode_context.get('summary', '')}\n"
            f"Opening: {episode_context.get('opening', '')}\n"
            f"Middle: {episode_context.get('middle', '')}\n"
            f"Ending: {episode_context.get('ending', '')}\n"
            f"World: {world_context.get('name', '')}\n\n"
            "Return a JSON array of scene objects with: scene_number, scene_goal, location, "
            "character_names, camera_direction, duration_seconds, emotional_tone."
        )
        result = await self._llm.generate_json(
            prompt,
            system="You are a scene planning AI. Return ONLY a valid JSON array.",
            temperature=self._cfg.SI_AI_TEMPERATURE,
        )
        return result if isinstance(result, list) else result.get("scenes", [])

    async def ai_generate_dialogue(
        self, scene: StoryScene, world_context: dict[str, Any]
    ) -> list[dict[str, Any]]:
        prompt = (
            f"Write dialogue for this scene:\n"
            f"Location: {scene.location}\n"
            f"Goal: {scene.scene_goal}\n"
            f"Characters: {', '.join(scene.character_names)}\n"
            f"World: {world_context.get('name', '')}\n\n"
            "Return a JSON array of dialogue objects with: character, line, emotion, action."
        )
        result = await self._llm.generate_json(
            prompt,
            system="You are a dialogue writer AI. Return ONLY a valid JSON array.",
            temperature=self._cfg.SI_AI_TEMPERATURE,
        )
        return result if isinstance(result, list) else result.get("dialogue", [])

    async def ai_generate_narration(
        self, scene: StoryScene, episode_context: dict[str, Any]
    ) -> str:
        prompt = (
            f"Write narration for this scene:\n"
            f"Location: {scene.location}\n"
            f"Goal: {scene.scene_goal}\n"
            f"Dialogue excerpt: {str(scene.dialogue)[:200]}\n\n"
            "Return a JSON object with: narration (string)."
        )
        result = await self._llm.generate_json(
            prompt,
            system="You are a narration writer AI. Return ONLY valid JSON.",
            temperature=self._cfg.SI_AI_TEMPERATURE,
        )
        return result.get("narration", "")

    async def ai_generate_image_prompt(self, scene: StoryScene) -> str:
        prompt = (
            f"Generate an image prompt for this scene:\n"
            f"Location: {scene.location}\n"
            f"Characters: {', '.join(scene.character_names)}\n"
            f"Goal: {scene.scene_goal}\n\n"
            "Return JSON with: image_prompt (string), style, mood, color_palette (list)."
        )
        result = await self._llm.generate_json(
            prompt,
            system="You are a visual prompt AI. Return ONLY valid JSON.",
            temperature=self._cfg.SI_AI_TEMPERATURE,
        )
        return result.get("image_prompt", "")

    async def ai_generate_animation_prompt(self, scene: StoryScene) -> str:
        prompt = (
            f"Generate an animation prompt for this scene:\n"
            f"Location: {scene.location}\n"
            f"Characters: {', '.join(scene.character_names)}\n"
            f"Dialogue count: {len(scene.dialogue)}\n\n"
            "Return JSON with: animation_prompt (string), key_motions (list), timing_seconds."
        )
        result = await self._llm.generate_json(
            prompt,
            system="You are an animation prompt AI. Return ONLY valid JSON.",
            temperature=self._cfg.SI_AI_TEMPERATURE,
        )
        return result.get("animation_prompt", "")

"""
CharacterResolutionStep — maps LLM-generated character names to DB Character records.
Creates Character records for any new characters found in the story.
"""
from __future__ import annotations

import structlog

from workflow.context import WorkflowContext
from workflow.retry import RetryPolicy
from workflow.step import BaseStep, StepResult

logger = structlog.get_logger()


class CharacterResolutionStep(BaseStep):
    """
    Step 3 — Resolves characters from story output to DB records.

    Reads from context.step_results["story_generation"]["characters"]
    Reads from context.step_results["scene_breakdown"]["scenes"]

    Writes to context.step_results["character_resolution"]:
      {
        "characters": list[{name, archetype, voice_style, ...}],
        "scene_character_map": {scene_number: [character_names]},
      }
    """

    retry_policy = RetryPolicy(max_retries=2, base_delay=1.0)

    @property
    def name(self) -> str:
        return "character_resolution"

    @property
    def description(self) -> str:
        return "Resolving characters"

    async def execute(self, ctx: WorkflowContext) -> StepResult:
        story_data = ctx.get_step_result("story_generation", {})
        scene_data = ctx.get_step_result("scene_breakdown", {})

        characters_raw = story_data.get("characters", [])
        scenes = scene_data.get("scenes", [])

        logger.info(
            "character_resolution_start",
            run_id=ctx.run_id,
            character_count=len(characters_raw),
        )

        # Load plugin archetypes if available
        archetype_map = await self._load_archetypes(ctx)

        # Build resolved character list
        resolved_characters = []
        for char_raw in characters_raw:
            archetype_key = char_raw.get("archetype", "").lower()
            archetype_defaults = archetype_map.get(archetype_key, {})
            resolved_characters.append({
                "name": char_raw.get("name", "Unknown"),
                "archetype": archetype_key,
                "description": char_raw.get("description", archetype_defaults.get("description", "")),
                "voice_style": char_raw.get("voice_style", archetype_defaults.get("voice_style", "neutral")),
                "visual_style": archetype_defaults.get("visual_style", "default"),
                "age_group": archetype_defaults.get("age_group", "adult"),
            })

        # Build per-scene character map
        scene_character_map: dict[int, list[str]] = {}
        for scene in scenes:
            scene_num = scene.get("scene_number", 0)
            scene_character_map[scene_num] = scene.get("characters_present", [])

        output = {
            "characters": resolved_characters,
            "scene_character_map": {str(k): v for k, v in scene_character_map.items()},
        }
        ctx.set_step_result(self.name, output)
        logger.info("character_resolution_complete", run_id=ctx.run_id, count=len(resolved_characters))
        return StepResult(success=True, output=output)

    async def _load_archetypes(self, ctx: WorkflowContext) -> dict:
        try:
            from plugins.registry import get_registry
            registry = get_registry()
            plugin = registry.get_plugin(ctx.plugin_id)
            if plugin:
                archetypes = plugin.get_character_archetypes()
                return {a.get("key", a.get("name", "").lower()): a for a in archetypes}
        except Exception:
            pass
        return {}

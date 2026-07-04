"""
SceneBreakdownStep — persists scenes from story_generation output to the database.
Creates/updates Scene records for each scene in the generated story.
"""
from __future__ import annotations

import structlog

from workflow.context import WorkflowContext
from workflow.retry import RetryPolicy
from workflow.step import BaseStep, StepResult

logger = structlog.get_logger()


class SceneBreakdownStep(BaseStep):
    """
    Step 2 — Reads story_generation output and creates Scene DB records.

    Reads from context.step_results["story_generation"]:
      scenes, characters

    Writes to context.step_results["scene_breakdown"]:
      {
        "scene_ids": list[str],
        "scene_count": int,
        "scenes": list[{scene_id, scene_number, title, setting, ...}],
      }
    """

    retry_policy = RetryPolicy(max_retries=2, base_delay=2.0)

    @property
    def name(self) -> str:
        return "scene_breakdown"

    @property
    def description(self) -> str:
        return "Breaking story into scenes"

    async def execute(self, ctx: WorkflowContext) -> StepResult:
        story_data = ctx.get_step_result("story_generation", {})
        scenes_raw = story_data.get("scenes", [])

        if not scenes_raw:
            return StepResult(
                success=False,
                error="No scenes found in story_generation output",
            )

        logger.info("scene_breakdown_start", run_id=ctx.run_id, scene_count=len(scenes_raw))

        # Build the scene records (persist to DB via repository when DB session available)
        scene_records = []
        for raw_scene in scenes_raw:
            scene_records.append({
                "story_id": ctx.story_id,
                "scene_number": raw_scene.get("scene_number", 0),
                "title": raw_scene.get("title", f"Scene {raw_scene.get('scene_number', 0)}"),
                "setting": raw_scene.get("setting", ""),
                "action": raw_scene.get("action", ""),
                "dialogue": raw_scene.get("dialogue", []),
                "mood": raw_scene.get("mood", "neutral"),
                "visual_description": raw_scene.get("visual_description", ""),
                "duration_hint_seconds": raw_scene.get("duration_hint_seconds", 30),
                "characters_present": raw_scene.get("characters_present", []),
            })

        output = {
            "scene_count": len(scene_records),
            "scenes": scene_records,
        }
        ctx.set_step_result(self.name, output)
        logger.info("scene_breakdown_complete", run_id=ctx.run_id, scenes=len(scene_records))
        return StepResult(success=True, output=output)

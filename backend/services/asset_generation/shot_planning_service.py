"""
Phase 6 — Shot Planning Service.

Automatically generates camera shots and scene compositions from
episode/scene metadata. No manual shot planning required.
"""
from __future__ import annotations

from typing import Any
from uuid import UUID

from database.models.asset_generation import CameraShot, AgSceneComposition as SceneComposition
from repositories.asset_generation_repository import (
    CameraShotRepository,
    SceneCompositionRepository,
)

# ---------------------------------------------------------------------------
# Shot type definitions — maps scene mood/type to preferred shots
# ---------------------------------------------------------------------------

_SHOT_TYPE_MAP: dict[str, list[str]] = {
    "action": ["wide", "tracking", "low_angle", "medium"],
    "dialogue": ["medium", "over_shoulder", "close_up"],
    "emotional": ["close_up", "extreme_close_up", "medium"],
    "establishing": ["wide", "top_view", "high_angle"],
    "comedy": ["medium", "wide", "over_shoulder"],
    "dramatic": ["low_angle", "close_up", "side_view"],
    "default": ["wide", "medium", "close_up"],
}

_COMPOSITION_MAP: dict[str, str] = {
    "wide": "rule of thirds, wide establishing shot, expansive environment",
    "medium": "rule of thirds, balanced framing, character centered",
    "close_up": "leading lines, face centered, shallow depth of field",
    "extreme_close_up": "centered, eye contact, extreme detail",
    "over_shoulder": "rule of thirds, over shoulder perspective, depth",
    "tracking": "leading lines, motion blur, dynamic angle",
    "top_view": "bird's eye view, symmetrical, overhead perspective",
    "side_view": "profile view, silhouette, lateral perspective",
    "low_angle": "low angle, heroic perspective, upward tilt",
    "high_angle": "high angle, downward tilt, diminishing perspective",
}

_CAMERA_PROMPT_MAP: dict[str, str] = {
    "wide": "wide angle lens, 24mm, full scene visible",
    "medium": "50mm lens, medium shot, waist up",
    "close_up": "85mm lens, face close-up, shallow DOF",
    "extreme_close_up": "100mm macro, extreme close-up, eyes detail",
    "over_shoulder": "50mm, over-shoulder shot, two person depth",
    "tracking": "tracking shot, motion, cinematic movement",
    "top_view": "drone view, top-down, 90 degrees overhead",
    "side_view": "side profile, 35mm, lateral angle",
    "low_angle": "low angle, worm's eye view, upward tilt, dramatic",
    "high_angle": "high angle, downward tilt, 70mm lens",
}


class ShotPlanningService:
    """Plans camera shots and scene compositions from story data."""

    def __init__(
        self,
        composition_repo: SceneCompositionRepository,
        shot_repo: CameraShotRepository,
    ) -> None:
        self._comp_repo = composition_repo
        self._shot_repo = shot_repo

    async def plan_episode_shots(
        self,
        project_id: UUID,
        episode_id: UUID,
        scenes: list[dict[str, Any]],
    ) -> dict[str, Any]:
        """Plan all shots for an episode from scene descriptors."""
        compositions_created = 0
        shots_created = 0

        for scene_idx, scene in enumerate(scenes):
            scene_id = scene.get("id")
            scene_type = scene.get("scene_type", "default")
            scene_description = scene.get("description", "")

            # Create composition for scene
            comp = await self._create_composition(
                project_id=project_id,
                episode_id=episode_id,
                scene_id=UUID(scene_id) if scene_id else None,
                scene_type=scene_type,
                description=scene_description,
                scene_data=scene,
            )
            compositions_created += 1

            # Create shots for this scene
            shot_types = _SHOT_TYPE_MAP.get(scene_type, _SHOT_TYPE_MAP["default"])
            for order, shot_type in enumerate(shot_types):
                await self._create_shot(
                    composition_id=comp.id,
                    scene_id=UUID(scene_id) if scene_id else None,
                    episode_id=episode_id,
                    shot_type=shot_type,
                    shot_order=scene_idx * 10 + order,
                )
                shots_created += 1

        return {
            "episode_id": str(episode_id),
            "compositions_created": compositions_created,
            "shots_created": shots_created,
        }

    async def _create_composition(
        self,
        project_id: UUID,
        episode_id: UUID,
        scene_id: UUID | None,
        scene_type: str,
        description: str,
        scene_data: dict[str, Any],
    ) -> SceneComposition:
        comp_type = "rule_of_thirds"
        if scene_type in ("action", "dramatic"):
            comp_type = "leading_lines"
        elif scene_type == "emotional":
            comp_type = "centered"

        lighting_dir = scene_data.get("time_of_day", "day")
        lighting_map = {"day": "natural", "night": "dramatic", "evening": "warm", "morning": "soft"}
        lighting_direction = lighting_map.get(lighting_dir, "natural")

        comp = SceneComposition(
            project_id=project_id,
            episode_id=episode_id,
            scene_id=scene_id,
            name=f"Scene {scene_id or 'unknown'} composition",
            description=description,
            composition_type=comp_type,
            focus_point="main character",
            lighting_direction=lighting_direction,
            color_harmony="complementary",
            negative_space=0.3,
            composition_prompt=_COMPOSITION_MAP.get("medium", ""),
            layout_data=scene_data,
        )
        return await self._comp_repo.create(comp)

    async def _create_shot(
        self,
        composition_id: UUID,
        scene_id: UUID | None,
        episode_id: UUID,
        shot_type: str,
        shot_order: int,
    ) -> CameraShot:
        shot = CameraShot(
            composition_id=composition_id,
            scene_id=scene_id,
            episode_id=episode_id,
            shot_type=shot_type,
            shot_order=shot_order,
            description=f"{shot_type.replace('_', ' ').title()} shot",
            camera_movement="static",
            camera_prompt=_CAMERA_PROMPT_MAP.get(shot_type, ""),
            shot_data={"composition_prompt": _COMPOSITION_MAP.get(shot_type, "")},
        )
        return await self._shot_repo.create(shot)

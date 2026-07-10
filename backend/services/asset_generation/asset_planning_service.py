"""
Phase 6 — Asset Planning Service.

From an episode + scenes, determines what assets need to be generated:
  - Characters present in each scene
  - Backgrounds for each scene
  - Props referenced in dialogue/action
  - Scene layouts / thumbnails

Avoids regenerating existing high-quality assets (checks cache and library).
"""
from __future__ import annotations

from typing import Any
from uuid import UUID

from database.models.asset_generation import GeneratedAsset as Asset
from repositories.asset_generation_repository import (
    AssetCacheRepository,
    AssetRepository,
)


# Asset types to plan per episode
_CHARACTER_ASSET_TYPES = [
    "character",
    "character_expression",
    "character_pose",
]

_SCENE_ASSET_TYPES = [
    "background",
    "scene_layout",
]

_PROP_ASSET_TYPES = [
    "prop",
]


class AssetPlanningService:
    """Determines what assets need generating for an episode."""

    def __init__(
        self,
        asset_repo: AssetRepository,
        cache_repo: AssetCacheRepository,
    ) -> None:
        self._asset_repo = asset_repo
        self._cache_repo = cache_repo

    async def plan_episode_assets(
        self,
        project_id: UUID,
        episode_id: UUID,
        episode_data: dict[str, Any],
        requested_asset_types: list[str] | None = None,
        force_regenerate: bool = False,
        quality_threshold: float = 90.0,
    ) -> dict[str, Any]:
        """
        Plan assets for an episode. Returns a list of Asset records
        (newly created with status='pending') to be generated.
        """
        requested_types = set(requested_asset_types or [
            "character", "character_expression", "character_pose",
            "background", "prop", "scene_layout",
        ])

        assets_to_generate: list[Asset] = []
        assets_reused: list[dict[str, Any]] = []

        scenes = episode_data.get("scenes", [])
        characters = episode_data.get("characters", [])

        # 1. Plan character assets
        if any(t in requested_types for t in _CHARACTER_ASSET_TYPES):
            char_assets = await self._plan_character_assets(
                project_id=project_id,
                episode_id=episode_id,
                characters=characters,
                requested_types=requested_types,
                force_regenerate=force_regenerate,
                quality_threshold=quality_threshold,
            )
            assets_to_generate.extend(char_assets)

        # 2. Plan background assets
        if "background" in requested_types or "scene_layout" in requested_types:
            bg_assets = await self._plan_background_assets(
                project_id=project_id,
                episode_id=episode_id,
                scenes=scenes,
                requested_types=requested_types,
                force_regenerate=force_regenerate,
                quality_threshold=quality_threshold,
            )
            assets_to_generate.extend(bg_assets)

        # 3. Plan prop assets
        if "prop" in requested_types:
            prop_assets = await self._plan_prop_assets(
                project_id=project_id,
                episode_id=episode_id,
                scenes=scenes,
                force_regenerate=force_regenerate,
                quality_threshold=quality_threshold,
            )
            assets_to_generate.extend(prop_assets)

        return {
            "episode_id": str(episode_id),
            "assets_planned": len(assets_to_generate),
            "assets_reused": len(assets_reused),
            "asset_ids": [str(a.id) for a in assets_to_generate],
        }

    async def _plan_character_assets(
        self,
        project_id: UUID,
        episode_id: UUID,
        characters: list[dict[str, Any]],
        requested_types: set[str],
        force_regenerate: bool,
        quality_threshold: float,
    ) -> list[Asset]:
        new_assets: list[Asset] = []
        for char in characters:
            char_id_str = char.get("id")
            char_id = UUID(char_id_str) if char_id_str else None
            char_name = char.get("name", "Unknown Character")
            char_desc = char.get("description", "")
            consistency_fp = {
                "hair_color": char.get("hair_color", ""),
                "eye_color": char.get("eye_color", ""),
                "clothing": char.get("clothing", ""),
                "skin_tone": char.get("skin_tone", ""),
                "art_style": "2d_cartoon",
            }

            # check existing high-quality asset
            if not force_regenerate and char_id:
                existing = await self._asset_repo.get_by_character(char_id)
                good = [a for a in existing if a.quality_score >= quality_threshold and a.status == "completed"]
                if good and "character" not in requested_types:
                    continue

            # Create base character asset
            if "character" in requested_types:
                asset = Asset(
                    project_id=project_id,
                    episode_id=episode_id,
                    character_id=char_id,
                    name=f"{char_name} — Base",
                    description=char_desc,
                    asset_type="character",
                    status="pending",
                    quality_threshold=quality_threshold,
                    consistency_fingerprint=consistency_fp,
                    tags=["character", char_name.lower().replace(" ", "_")],
                )
                new_assets.append(asset)

            # Expression variants
            if "character_expression" in requested_types:
                for expr in ["happy", "sad", "surprised", "angry", "neutral"]:
                    asset = Asset(
                        project_id=project_id,
                        episode_id=episode_id,
                        character_id=char_id,
                        name=f"{char_name} — {expr.title()} expression",
                        description=f"{char_desc} — {expr} expression",
                        asset_type="character_expression",
                        status="pending",
                        quality_threshold=quality_threshold,
                        consistency_fingerprint=consistency_fp,
                        tags=["character", "expression", expr],
                        generation_params={"expression": expr},
                    )
                    new_assets.append(asset)

            # Pose variants
            if "character_pose" in requested_types:
                for pose in ["standing", "sitting", "walking"]:
                    asset = Asset(
                        project_id=project_id,
                        episode_id=episode_id,
                        character_id=char_id,
                        name=f"{char_name} — {pose.title()} pose",
                        description=f"{char_desc} — {pose} pose",
                        asset_type="character_pose",
                        status="pending",
                        quality_threshold=quality_threshold,
                        consistency_fingerprint=consistency_fp,
                        tags=["character", "pose", pose],
                        generation_params={"pose": pose},
                    )
                    new_assets.append(asset)

        return new_assets

    async def _plan_background_assets(
        self,
        project_id: UUID,
        episode_id: UUID,
        scenes: list[dict[str, Any]],
        requested_types: set[str],
        force_regenerate: bool,
        quality_threshold: float,
    ) -> list[Asset]:
        new_assets: list[Asset] = []
        seen_locations: set[str] = set()

        for scene in scenes:
            scene_id_str = scene.get("id")
            scene_id = UUID(scene_id_str) if scene_id_str else None
            location = scene.get("location", scene.get("setting", "generic location"))
            scene_desc = scene.get("description", location)
            time_of_day = scene.get("time_of_day", "day")
            weather = scene.get("weather", "clear")

            loc_key = f"{location}_{time_of_day}_{weather}"

            if "background" in requested_types and loc_key not in seen_locations:
                seen_locations.add(loc_key)
                asset = Asset(
                    project_id=project_id,
                    episode_id=episode_id,
                    scene_id=scene_id,
                    name=f"{location} — {time_of_day}",
                    description=f"{scene_desc}, {time_of_day}, {weather}",
                    asset_type="background",
                    status="pending",
                    quality_threshold=quality_threshold,
                    tags=["background", location.lower().replace(" ", "_"), time_of_day, weather],
                    generation_params={"location": location, "time_of_day": time_of_day, "weather": weather},
                )
                new_assets.append(asset)

            if "scene_layout" in requested_types:
                asset = Asset(
                    project_id=project_id,
                    episode_id=episode_id,
                    scene_id=scene_id,
                    name=f"Scene layout — {location}",
                    description=f"Scene composition layout for {scene_desc}",
                    asset_type="scene_layout",
                    status="pending",
                    quality_threshold=quality_threshold,
                    tags=["scene_layout", "composition"],
                    generation_params=scene,
                )
                new_assets.append(asset)

        return new_assets

    async def _plan_prop_assets(
        self,
        project_id: UUID,
        episode_id: UUID,
        scenes: list[dict[str, Any]],
        force_regenerate: bool,
        quality_threshold: float,
    ) -> list[Asset]:
        new_assets: list[Asset] = []
        seen_props: set[str] = set()

        for scene in scenes:
            props = scene.get("props", [])
            scene_id_str = scene.get("id")
            scene_id = UUID(scene_id_str) if scene_id_str else None

            for prop in props:
                prop_name = prop if isinstance(prop, str) else prop.get("name", "")
                if not prop_name or prop_name.lower() in seen_props:
                    continue
                seen_props.add(prop_name.lower())

                asset = Asset(
                    project_id=project_id,
                    episode_id=episode_id,
                    scene_id=scene_id,
                    name=f"Prop — {prop_name}",
                    description=f"{prop_name} prop asset",
                    asset_type="prop",
                    status="pending",
                    quality_threshold=quality_threshold,
                    tags=["prop", prop_name.lower().replace(" ", "_")],
                    generation_params={"prop_name": prop_name},
                )
                new_assets.append(asset)

        return new_assets

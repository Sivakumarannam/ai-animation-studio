"""
Phase 6 — Prompt Generation Service.

Automatically assembles full generation prompts from:
  - asset type and description
  - character/background consistency data
  - art style definition
  - lighting preset
  - pose / expression presets
  - negative prompt library
  - generation memory (best prompts learned over time)

No manual prompt writing required.
"""
from __future__ import annotations

import hashlib
from datetime import datetime, timezone
from typing import Any
from uuid import UUID

from database.models.asset_generation import Asset, AssetPrompt
from repositories.asset_generation_repository import (
    AssetMemoryRepository,
    AssetPromptRepository,
    NegativePromptRepository,
    PromptHistoryRepository,
    PromptTemplateRepository,
)


# ---------------------------------------------------------------------------
# Built-in prompt templates (fallback when no DB template exists)
# ---------------------------------------------------------------------------

_DEFAULT_POSITIVE: dict[str, str] = {
    "character": (
        "{style}, {description}, full body, clean lines, expressive face, "
        "{pose}, {expression}, vibrant colors, high quality animation character"
    ),
    "character_variant": (
        "{style}, {description}, character variant, different angle, "
        "same character design, consistent art style"
    ),
    "character_expression": (
        "{style}, {description}, face close-up, {expression} expression, "
        "detailed facial features, consistent character design"
    ),
    "character_pose": (
        "{style}, {description}, {pose} pose, full body, action pose, "
        "dynamic composition, consistent character"
    ),
    "character_turnaround": (
        "{style}, {description}, character turnaround sheet, "
        "front back side views, consistent design"
    ),
    "background": (
        "{style}, {description}, background scene, {lighting}, "
        "detailed environment, no characters, wide establishing shot"
    ),
    "environment_variant": (
        "{style}, {description}, environment variation, "
        "same location different {variation_type}, consistent art style"
    ),
    "prop": (
        "{style}, {description}, isolated prop, clean background, "
        "detailed object, game asset style, front view"
    ),
    "vehicle": (
        "{style}, {description}, vehicle, side view, detailed design, "
        "clean lines, isolated on white background"
    ),
    "building": (
        "{style}, {description}, building exterior, architectural detail, "
        "establishing shot, {lighting}"
    ),
    "nature": (
        "{style}, {description}, nature element, detailed, "
        "isolated or in natural setting, {lighting}"
    ),
    "icon": (
        "{style}, {description}, icon design, simple clean, "
        "flat design, vector style, white background"
    ),
    "scene_layout": (
        "{style}, {description}, scene composition, {shot_type}, "
        "{lighting}, {composition}, establishing shot"
    ),
    "thumbnail": (
        "{style}, {description}, YouTube thumbnail, "
        "eye-catching, bold colors, dynamic composition, no text"
    ),
    "reference": (
        "{style}, {description}, reference sheet, multiple views, "
        "character design reference, model sheet"
    ),
}

_DEFAULT_NEGATIVE = (
    "blurry, low quality, bad anatomy, extra limbs, missing limbs, "
    "deformed, ugly, watermark, signature, text, logo, cropped, "
    "out of frame, poorly drawn, amateur, draft"
)


class PromptGenerationService:
    """Assembles full generation prompts from asset metadata and presets."""

    def __init__(
        self,
        prompt_repo: AssetPromptRepository,
        template_repo: PromptTemplateRepository,
        negative_repo: NegativePromptRepository,
        history_repo: PromptHistoryRepository,
        memory_repo: AssetMemoryRepository,
    ) -> None:
        self._prompt_repo = prompt_repo
        self._template_repo = template_repo
        self._negative_repo = negative_repo
        self._history_repo = history_repo
        self._memory_repo = memory_repo

    async def generate_prompt(
        self,
        asset: Asset,
        style_data: dict[str, Any] | None = None,
        lighting_data: dict[str, Any] | None = None,
        pose_data: dict[str, Any] | None = None,
        expression_data: dict[str, Any] | None = None,
        composition_data: dict[str, Any] | None = None,
        shot_data: dict[str, Any] | None = None,
        extra_params: dict[str, Any] | None = None,
    ) -> AssetPrompt:
        """Generate and persist a full prompt for the given asset."""
        style_data = style_data or {}
        lighting_data = lighting_data or {}
        pose_data = pose_data or {}
        expression_data = expression_data or {}
        composition_data = composition_data or {}
        shot_data = shot_data or {}
        extra_params = extra_params or {}

        asset_type = asset.asset_type

        # 1. Build style prompt fragment
        style_prompt = style_data.get("style_prompt", "2d animation style")
        style_neg = style_data.get("negative_prompt", "")

        # 2. Build lighting prompt
        lighting_prompt = lighting_data.get("lighting_prompt", "natural lighting")

        # 3. Build pose prompt
        pose_prompt = pose_data.get("pose_prompt", "")

        # 4. Build expression prompt
        expression_prompt = expression_data.get("expression_prompt", "")

        # 5. Build composition prompt
        composition_prompt = composition_data.get("composition_prompt", "")

        # 6. Build camera prompt
        camera_prompt = shot_data.get("camera_prompt", "")

        # 7. Color / harmony
        color_palette = style_data.get("color_palette", [])
        color_prompt = ", ".join(color_palette) if color_palette else ""

        # 8. Consistency prompt (character fingerprint)
        consistency_prompt = self._build_consistency_prompt(asset)

        # 9. Assemble positive prompt from template
        template_vars = {
            "style": style_prompt,
            "description": asset.description or asset.name,
            "pose": pose_prompt or "standing",
            "expression": expression_prompt or "neutral",
            "lighting": lighting_prompt,
            "composition": composition_prompt or "balanced composition",
            "shot_type": shot_data.get("shot_type", "medium shot"),
            "variation_type": extra_params.get("variation_type", "time of day"),
        }
        base_template = _DEFAULT_POSITIVE.get(asset_type, _DEFAULT_POSITIVE["character"])
        positive_parts = [base_template.format_map(template_vars)]
        if consistency_prompt:
            positive_parts.append(consistency_prompt)
        if camera_prompt:
            positive_parts.append(camera_prompt)

        positive_prompt = ", ".join(filter(None, positive_parts))

        # 10. Assemble negative prompt
        neg_parts = [_DEFAULT_NEGATIVE]
        if style_neg:
            neg_parts.append(style_neg)
        # add asset-type-specific negatives from DB
        db_negatives = await self._negative_repo.get_active_by_category(asset_type)
        db_negatives += await self._negative_repo.get_universal()
        for neg in db_negatives:
            if neg.content not in neg_parts:
                neg_parts.append(neg.content)

        negative_prompt = ", ".join(filter(None, neg_parts))

        # 11. Full assembled prompts
        full_positive = positive_prompt
        full_negative = negative_prompt

        # 12. Cache key to avoid duplicate prompts
        cache_key = hashlib.sha256(f"{full_positive}|{full_negative}".encode()).hexdigest()

        prompt = AssetPrompt(
            asset_id=asset.id,
            positive_prompt=positive_prompt,
            negative_prompt=negative_prompt,
            style_prompt=style_prompt,
            camera_prompt=camera_prompt,
            composition_prompt=composition_prompt,
            lighting_prompt=lighting_prompt,
            color_prompt=color_prompt,
            consistency_prompt=consistency_prompt,
            full_prompt=full_positive,
            full_negative_prompt=full_negative,
            prompt_type=asset_type,
            generation_params={
                "cache_key": cache_key,
                "style_type": style_data.get("style_type", "2d_cartoon"),
                "template_vars": template_vars,
            },
        )
        return await self._prompt_repo.create(prompt)

    def _build_consistency_prompt(self, asset: Asset) -> str:
        """Build a prompt fragment to enforce character/background consistency."""
        fp = asset.consistency_fingerprint
        if not fp:
            return ""
        parts = []
        for key in ("hair_color", "eye_color", "clothing", "skin_tone", "art_style"):
            val = fp.get(key)
            if val:
                parts.append(str(val))
        return ", ".join(parts) if parts else ""

    async def mark_prompt_successful(self, prompt_id: UUID, quality_score: float) -> None:
        """Record that a prompt produced a high-quality result."""
        prompt = await self._prompt_repo.get_by_id(prompt_id)
        if prompt:
            prompt.was_successful = True
            prompt.quality_score = quality_score
            prompt.use_count += 1
            await self._prompt_repo.update(prompt)

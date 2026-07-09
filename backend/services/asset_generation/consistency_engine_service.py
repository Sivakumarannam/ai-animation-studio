"""
Phase 6 — Consistency Engine Service.

Maintains character and background consistency across episodes, seasons,
and the entire series by:
  - Building and updating consistency fingerprints
  - Injecting consistency prompts into generation
  - Storing and retrieving the best reference images per character
"""
from __future__ import annotations

from typing import Any
from uuid import UUID

from database.models.asset_generation import Asset
from repositories.asset_generation_repository import (
    AssetMemoryRepository,
    AssetRelationshipRepository,
    AssetRepository,
)


class ConsistencyEngineService:
    """Maintains visual consistency for characters and backgrounds."""

    def __init__(
        self,
        asset_repo: AssetRepository,
        relationship_repo: AssetRelationshipRepository,
        memory_repo: AssetMemoryRepository,
    ) -> None:
        self._asset_repo = asset_repo
        self._rel_repo = relationship_repo
        self._memory_repo = memory_repo

    async def get_character_consistency_data(
        self,
        project_id: UUID,
        character_id: UUID,
    ) -> dict[str, Any]:
        """
        Return the consistency fingerprint for a character, built from
        the best quality assets already generated for that character.
        """
        existing_assets = await self._asset_repo.get_by_character(character_id)
        best_assets = [
            a for a in existing_assets
            if a.quality_score >= 80.0 and a.status == "completed" and a.asset_type == "character"
        ]

        if not best_assets:
            # Check memory for stored fingerprint
            memories = await self._memory_repo.get_by_type(
                project_id, "character_fingerprint", scope=str(character_id)
            )
            if memories:
                return memories[0].value
            return {}

        # Use the highest quality asset's fingerprint
        best = max(best_assets, key=lambda a: a.quality_score)
        return dict(best.consistency_fingerprint)

    async def update_character_fingerprint(
        self,
        project_id: UUID,
        character_id: UUID,
        asset: Asset,
        quality_score: float,
    ) -> None:
        """Update stored consistency fingerprint after a successful generation."""
        if quality_score < 90.0:
            return

        fingerprint = dict(asset.consistency_fingerprint)
        if not fingerprint:
            return

        existing = await self._memory_repo.get_by_key(
            project_id, "character_fingerprint", str(character_id)
        )
        if existing:
            # merge: keep the higher-confidence values
            existing.value.update(fingerprint)
            existing.confidence = max(existing.confidence, quality_score / 100.0)
            existing.use_count += 1
            await self._memory_repo._session.flush()
        else:
            from database.models.asset_generation import AssetMemory
            mem = AssetMemory(
                project_id=project_id,
                memory_type="character_fingerprint",
                scope=str(character_id),
                key=str(character_id),
                value=fingerprint,
                confidence=quality_score / 100.0,
            )
            await self._memory_repo.create(mem)

    async def get_background_consistency_data(
        self,
        project_id: UUID,
        location_key: str,
    ) -> dict[str, Any]:
        """Return stored consistency data for a background location."""
        memories = await self._memory_repo.get_by_type(
            project_id, "background_style", scope=location_key
        )
        if memories:
            return memories[0].value
        return {}

    async def link_variant_assets(
        self,
        base_asset_id: UUID,
        variant_asset_id: UUID,
        relationship_type: str = "variant_of",
    ) -> None:
        """Record that variant_asset is a variant of base_asset."""
        from database.models.asset_generation import AssetRelationship
        existing = await self._rel_repo.get_by_source(base_asset_id, relationship_type)
        already_linked = any(r.target_asset_id == variant_asset_id for r in existing)
        if already_linked:
            return

        rel = AssetRelationship(
            source_asset_id=base_asset_id,
            target_asset_id=variant_asset_id,
            relationship_type=relationship_type,
        )
        await self._rel_repo.create(rel)

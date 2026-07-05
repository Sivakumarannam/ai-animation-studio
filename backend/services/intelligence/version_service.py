"""VersionService — snapshot and restore any SI entity."""
from __future__ import annotations

from typing import Any
from uuid import UUID

from database.models.intelligence import StoryVersion
from repositories.intelligence_repository import StoryVersionRepository


class VersionService:
    def __init__(self, repo: StoryVersionRepository) -> None:
        self._repo = repo

    async def create_snapshot(
        self,
        entity_type: str,
        entity_id: UUID,
        snapshot: dict[str, Any],
        change_summary: str = "",
        created_by: str = "system",
    ) -> StoryVersion:
        version_num = await self._repo.get_next_version_number(entity_type, entity_id)
        v = StoryVersion(
            entity_type=entity_type,
            entity_id=entity_id,
            version_number=version_num,
            snapshot=snapshot,
            change_summary=change_summary,
            created_by=created_by,
        )
        return await self._repo.create(v)

    async def list_versions(self, entity_type: str, entity_id: UUID) -> list[StoryVersion]:
        return await self._repo.get_for_entity(entity_type, entity_id)

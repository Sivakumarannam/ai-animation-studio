"""WorldService — CRUD + business logic for Story Intelligence worlds."""
from __future__ import annotations

from typing import Any
from uuid import UUID

from packages.core.exceptions import NotFoundError
from packages.utils.pagination import PaginatedResult, PaginationParams
from repositories.intelligence_repository import WorldRepository, StoryVersionRepository
from database.models.intelligence import World


class WorldService:
    def __init__(self, repo: WorldRepository, version_repo: StoryVersionRepository) -> None:
        self._repo = repo
        self._versions = version_repo

    async def create(self, project_id: UUID, data: dict[str, Any]) -> World:
        world = World(project_id=project_id, **data)
        return await self._repo.create(world)

    async def get_by_id(self, world_id: UUID) -> World:
        world = await self._repo.get_by_id(world_id)
        if world is None:
            raise NotFoundError(f"World {world_id} not found")
        return world

    async def list_by_project(
        self, project_id: UUID, pagination: PaginationParams
    ) -> PaginatedResult[World]:
        return await self._repo.get_by_project(project_id, pagination)

    async def update(self, world_id: UUID, data: dict[str, Any]) -> World:
        world = await self.get_by_id(world_id)
        # Snapshot before update
        await self._snapshot(world)
        return await self._repo.update(world, data)

    async def delete(self, world_id: UUID) -> None:
        world = await self.get_by_id(world_id)
        await self._repo.delete(world)

    async def _snapshot(self, world: World) -> None:
        version_num = await self._versions.get_next_version_number("world", world.id)
        from database.models.intelligence import StoryVersion
        v = StoryVersion(
            entity_type="world", entity_id=world.id,
            version_number=version_num,
            snapshot={
                "name": world.name, "description": world.description,
                "rules": world.rules, "locations": world.locations,
                "timeline_data": world.timeline_data, "factions": world.factions,
                "objects": world.objects, "lore": world.lore,
            },
            change_summary="pre-update snapshot",
        )
        await self._versions.create(v)

from datetime import datetime, timezone
from typing import Any
from uuid import UUID

from database.models.scene import Scene
from packages.core.exceptions import NotFoundError
from packages.utils.pagination import PaginatedResult, PaginationParams
from repositories.scene_repository import SceneRepository


class SceneService:
    def __init__(self, repo: SceneRepository) -> None:
        self._repo = repo

    async def create(
        self,
        story_id: UUID,
        scene_number: int,
        title: str,
        description: str,
        dialogue: str,
        action_notes: str,
        duration_seconds: float,
        background_id: UUID | None,
        ordering: int,
    ) -> Scene:
        scene = Scene(
            story_id=story_id,
            scene_number=scene_number,
            title=title,
            description=description,
            dialogue=dialogue,
            action_notes=action_notes,
            duration_seconds=duration_seconds,
            background_id=background_id,
            ordering=ordering,
        )
        return await self._repo.create(scene)

    async def get_by_story(
        self, story_id: UUID, pagination: PaginationParams
    ) -> PaginatedResult[Scene]:
        return await self._repo.get_by_story(story_id, pagination)

    async def get_by_id(self, scene_id: UUID, story_id: UUID) -> Scene:
        scene = await self._repo.get_by_id_and_story(scene_id, story_id)
        if scene is None:
            raise NotFoundError("Scene", scene_id)
        return scene

    async def update(self, scene_id: UUID, story_id: UUID, data: dict[str, Any]) -> Scene:
        scene = await self.get_by_id(scene_id, story_id)
        clean_data = {k: v for k, v in data.items() if v is not None}
        clean_data["updated_at"] = datetime.now(timezone.utc)
        return await self._repo.update(scene, clean_data)

    async def delete(self, scene_id: UUID, story_id: UUID) -> None:
        scene = await self.get_by_id(scene_id, story_id)
        await self._repo.delete(scene)

    async def reorder(self, scene_ids: list[UUID]) -> None:
        await self._repo.reorder(scene_ids)

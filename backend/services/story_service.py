from datetime import datetime, timezone
from typing import Any
from uuid import UUID

from database.models.story import Story
from packages.core.exceptions import NotFoundError
from packages.utils.pagination import PaginatedResult, PaginationParams
from repositories.story_repository import StoryRepository


class StoryService:
    def __init__(self, repo: StoryRepository) -> None:
        self._repo = repo

    async def create(
        self,
        project_id: UUID,
        title: str,
        premise: str,
        genre: str,
        tone: str,
        duration_target: int,
        language: str,
    ) -> Story:
        story = Story(
            project_id=project_id,
            title=title,
            premise=premise,
            genre=genre,
            tone=tone,
            duration_target=duration_target,
            language=language,
        )
        return await self._repo.create(story)

    async def get_by_project(
        self, project_id: UUID, pagination: PaginationParams
    ) -> PaginatedResult[Story]:
        return await self._repo.get_by_project(project_id, pagination)

    async def get_by_id(self, story_id: UUID, project_id: UUID) -> Story:
        story = await self._repo.get_by_id_and_project(story_id, project_id)
        if story is None:
            raise NotFoundError("Story", story_id)
        return story

    async def update(self, story_id: UUID, project_id: UUID, data: dict[str, Any]) -> Story:
        story = await self.get_by_id(story_id, project_id)
        clean_data = {k: v for k, v in data.items() if v is not None}
        clean_data["updated_at"] = datetime.now(timezone.utc)
        return await self._repo.update(story, clean_data)

    async def delete(self, story_id: UUID, project_id: UUID) -> None:
        story = await self.get_by_id(story_id, project_id)
        await self._repo.delete(story)

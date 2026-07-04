from datetime import datetime, timezone
from typing import Any
from uuid import UUID

from database.models.character import Character
from packages.core.exceptions import NotFoundError
from packages.utils.pagination import PaginatedResult, PaginationParams
from repositories.character_repository import CharacterRepository


class CharacterService:
    def __init__(self, repo: CharacterRepository) -> None:
        self._repo = repo

    async def create(
        self,
        project_id: UUID,
        name: str,
        description: str,
        personality: str,
        voice_profile: str,
        age_range: str,
        gender: str,
        asset_data: dict[str, Any],
    ) -> Character:
        character = Character(
            project_id=project_id,
            name=name,
            description=description,
            personality=personality,
            voice_profile=voice_profile,
            age_range=age_range,
            gender=gender,
            asset_data=asset_data,
        )
        return await self._repo.create(character)

    async def get_by_project(
        self, project_id: UUID, pagination: PaginationParams
    ) -> PaginatedResult[Character]:
        return await self._repo.get_by_project(project_id, pagination)

    async def get_library(self, pagination: PaginationParams) -> PaginatedResult[Character]:
        return await self._repo.get_library(pagination)

    async def get_by_id(self, character_id: UUID) -> Character:
        character = await self._repo.get_by_id(character_id)
        if character is None:
            raise NotFoundError("Character", character_id)
        return character

    async def update(self, character_id: UUID, data: dict[str, Any]) -> Character:
        character = await self.get_by_id(character_id)
        clean_data = {k: v for k, v in data.items() if v is not None}
        clean_data["updated_at"] = datetime.now(timezone.utc)
        return await self._repo.update(character, clean_data)

    async def delete(self, character_id: UUID) -> None:
        character = await self.get_by_id(character_id)
        await self._repo.delete(character)

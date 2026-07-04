from datetime import datetime, timezone
from typing import Any
from uuid import UUID

from database.models.project import Project
from packages.core.exceptions import AuthorizationError, NotFoundError
from packages.utils.pagination import PaginatedResult, PaginationParams
from repositories.project_repository import ProjectRepository


class ProjectService:
    def __init__(self, repo: ProjectRepository) -> None:
        self._repo = repo

    async def create(
        self,
        user_id: UUID,
        title: str,
        description: str,
        plugin_id: str,
        animation_style: str,
        metadata: dict[str, Any],
    ) -> Project:
        project = Project(
            user_id=user_id,
            title=title,
            description=description,
            plugin_id=plugin_id,
            animation_style=animation_style,
            metadata_=metadata,
        )
        return await self._repo.create(project)

    async def get_by_user(
        self, user_id: UUID, pagination: PaginationParams, status: str | None = None
    ) -> PaginatedResult[Project]:
        return await self._repo.get_by_user(user_id, pagination, status)

    async def get_by_id(self, project_id: UUID, user_id: UUID) -> Project:
        project = await self._repo.get_by_id_and_user(project_id, user_id)
        if project is None:
            raise NotFoundError("Project", project_id)
        return project

    async def update(
        self, project_id: UUID, user_id: UUID, data: dict[str, Any]
    ) -> Project:
        project = await self.get_by_id(project_id, user_id)
        clean_data = {k: v for k, v in data.items() if v is not None}
        if "metadata" in clean_data:
            clean_data["metadata_"] = clean_data.pop("metadata")
        clean_data["updated_at"] = datetime.now(timezone.utc)
        return await self._repo.update(project, clean_data)

    async def delete(self, project_id: UUID, user_id: UUID) -> None:
        project = await self.get_by_id(project_id, user_id)
        await self._repo.delete(project)

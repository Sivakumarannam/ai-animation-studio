from typing import Any, Generic, TypeVar
from uuid import UUID

from packages.core.exceptions import NotFoundError
from packages.utils.pagination import PaginatedResult, PaginationParams
from repositories.base import BaseRepository

ModelT = TypeVar("ModelT")


class BaseService(Generic[ModelT]):
    """Base service providing standard CRUD operations over a repository."""

    _resource_name: str = "Resource"

    def __init__(self, repository: BaseRepository) -> None:  # type: ignore[type-arg]
        self._repo = repository

    async def get_by_id(self, id: UUID) -> ModelT:
        item = await self._repo.get_by_id(id)
        if item is None:
            raise NotFoundError(self._resource_name, id)
        return item  # type: ignore[return-value]

    async def delete(self, id: UUID) -> None:
        item = await self._repo.get_by_id(id)
        if item is None:
            raise NotFoundError(self._resource_name, id)
        await self._repo.delete(item)

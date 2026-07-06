"""KnowledgeCollectionService — CRUD + lifecycle for KnowledgeCollection."""
from __future__ import annotations

from uuid import UUID

from agents.interfaces.vector_store_provider import VectorStoreProvider
from database.models.knowledge import KnowledgeCollection
from packages.core.exceptions import NotFoundError
from packages.utils.pagination import PaginatedResult, PaginationParams
from repositories.knowledge_repository import KnowledgeCollectionRepository


class KnowledgeCollectionService:
    def __init__(self, repo: KnowledgeCollectionRepository, vector_store: VectorStoreProvider) -> None:
        self._repo = repo
        self._vector_store = vector_store

    async def create(
        self,
        project_id: UUID,
        name: str,
        description: str = "",
        collection_type: str = "general",
        world_id: UUID | None = None,
        settings: dict | None = None,
    ) -> KnowledgeCollection:
        collection = KnowledgeCollection(
            project_id=project_id,
            world_id=world_id,
            name=name,
            description=description,
            collection_type=collection_type,
            settings=settings or {},
        )
        return await self._repo.create(collection)

    async def get(self, collection_id: UUID) -> KnowledgeCollection:
        collection = await self._repo.get_by_id(collection_id)
        if collection is None:
            raise NotFoundError(f"KnowledgeCollection {collection_id} not found")
        return collection

    async def list_by_project(
        self, project_id: UUID, pagination: PaginationParams, status: str | None = None
    ) -> PaginatedResult[KnowledgeCollection]:
        return await self._repo.get_by_project(project_id, pagination, status=status)

    async def list_by_world(self, world_id: UUID) -> list[KnowledgeCollection]:
        return await self._repo.get_by_world(world_id)

    async def update(self, collection_id: UUID, data: dict) -> KnowledgeCollection:
        collection = await self.get(collection_id)
        return await self._repo.update(collection, data)

    async def archive(self, collection_id: UUID) -> KnowledgeCollection:
        return await self.update(collection_id, {"status": "archived"})

    async def delete(self, collection_id: UUID) -> None:
        collection = await self.get(collection_id)
        await self._vector_store.delete_namespace(str(collection_id))
        await self._repo.delete(collection)

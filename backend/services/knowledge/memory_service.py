"""KnowledgeMemoryService — RAG-sourced, world-scoped distilled facts."""
from __future__ import annotations

from typing import Any
from uuid import UUID

from database.models.knowledge import KnowledgeMemory
from packages.core.exceptions import NotFoundError
from packages.utils.pagination import PaginatedResult, PaginationParams
from repositories.knowledge_repository import KnowledgeMemoryRepository

MEMORY_TYPES = frozenset(["fact", "rule", "lore", "entity", "summary"])


class KnowledgeMemoryService:
    def __init__(self, repo: KnowledgeMemoryRepository) -> None:
        self._repo = repo

    async def create(
        self,
        project_id: UUID,
        memory_type: str,
        key: str,
        value: dict[str, Any],
        world_id: UUID | None = None,
        collection_id: UUID | None = None,
        source_chunk_id: UUID | None = None,
        confidence: float = 1.0,
    ) -> KnowledgeMemory:
        memory = KnowledgeMemory(
            project_id=project_id,
            world_id=world_id,
            collection_id=collection_id,
            source_chunk_id=source_chunk_id,
            memory_type=memory_type if memory_type in MEMORY_TYPES else "fact",
            key=key,
            value=value,
            confidence=confidence,
        )
        return await self._repo.create(memory)

    async def get(self, memory_id: UUID) -> KnowledgeMemory:
        memory = await self._repo.get_by_id(memory_id)
        if memory is None:
            raise NotFoundError(f"KnowledgeMemory {memory_id} not found")
        return memory

    async def list_by_world(
        self, world_id: UUID, pagination: PaginationParams, memory_type: str | None = None
    ) -> PaginatedResult[KnowledgeMemory]:
        return await self._repo.get_by_world(world_id, pagination, memory_type=memory_type)

    async def list_by_project(
        self, project_id: UUID, pagination: PaginationParams, memory_type: str | None = None
    ) -> PaginatedResult[KnowledgeMemory]:
        return await self._repo.get_by_project(project_id, pagination, memory_type=memory_type)

    async def deactivate(self, memory_id: UUID) -> None:
        memory = await self.get(memory_id)
        await self._repo.update(memory, {"is_active": False})

    async def build_context_for_world(self, world_id: UUID, limit: int = 30) -> dict[str, list[Any]]:
        memories = await self._repo.get_active_by_world(world_id)
        context: dict[str, list[Any]] = {}
        for m in memories[:limit]:
            context.setdefault(m.memory_type, []).append({"key": m.key, "value": m.value})
        return context

"""Phase 4 — Knowledge Engine repositories. Mirrors intelligence_repository.py conventions."""
from __future__ import annotations

from uuid import UUID

from sqlalchemy import delete as sa_delete, func, select, update as sa_update
from sqlalchemy.ext.asyncio import AsyncSession

from database.models.knowledge import (
    EmbeddingJob,
    KnowledgeChunk,
    KnowledgeCollection,
    KnowledgeDocument,
    KnowledgeMemory,
    KnowledgeVersion,
    RetrievalHistory,
)
from packages.utils.pagination import PaginatedResult, PaginationParams
from repositories.base import BaseRepository


class KnowledgeCollectionRepository(BaseRepository[KnowledgeCollection]):
    model = KnowledgeCollection

    async def get_by_project(
        self, project_id: UUID, pagination: PaginationParams, status: str | None = None
    ) -> PaginatedResult[KnowledgeCollection]:
        return await self.get_all(pagination, filters={"project_id": project_id, "status": status})

    async def get_by_world(self, world_id: UUID) -> list[KnowledgeCollection]:
        stmt = select(KnowledgeCollection).where(KnowledgeCollection.world_id == world_id)
        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    async def increment_counts(self, collection_id: UUID, doc_delta: int = 0, chunk_delta: int = 0) -> None:
        stmt = (
            sa_update(KnowledgeCollection)
            .where(KnowledgeCollection.id == collection_id)
            .values(
                document_count=KnowledgeCollection.document_count + doc_delta,
                chunk_count=KnowledgeCollection.chunk_count + chunk_delta,
            )
        )
        await self._session.execute(stmt)
        await self._session.flush()


class KnowledgeDocumentRepository(BaseRepository[KnowledgeDocument]):
    model = KnowledgeDocument

    async def get_by_collection(
        self, collection_id: UUID, pagination: PaginationParams, status: str | None = None
    ) -> PaginatedResult[KnowledgeDocument]:
        return await self.get_all(pagination, filters={"collection_id": collection_id, "status": status})

    async def get_by_project(
        self, project_id: UUID, pagination: PaginationParams
    ) -> PaginatedResult[KnowledgeDocument]:
        return await self.get_all(pagination, filters={"project_id": project_id})

    async def get_by_hash(self, collection_id: UUID, content_hash: str) -> KnowledgeDocument | None:
        stmt = select(KnowledgeDocument).where(
            KnowledgeDocument.collection_id == collection_id,
            KnowledgeDocument.content_hash == content_hash,
        )
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()


class KnowledgeChunkRepository(BaseRepository[KnowledgeChunk]):
    model = KnowledgeChunk

    async def get_by_document(self, document_id: UUID) -> list[KnowledgeChunk]:
        stmt = (
            select(KnowledgeChunk)
            .where(KnowledgeChunk.document_id == document_id)
            .order_by(KnowledgeChunk.chunk_index)
        )
        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    async def get_by_collection(self, collection_id: UUID, embedded_only: bool = True) -> list[KnowledgeChunk]:
        stmt = select(KnowledgeChunk).where(KnowledgeChunk.collection_id == collection_id)
        if embedded_only:
            stmt = stmt.where(KnowledgeChunk.is_embedded.is_(True))
        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    async def bulk_create(self, chunks: list[KnowledgeChunk]) -> list[KnowledgeChunk]:
        self._session.add_all(chunks)
        await self._session.flush()
        for c in chunks:
            await self._session.refresh(c)
        return chunks

    async def delete_by_document(self, document_id: UUID) -> None:
        stmt = sa_delete(KnowledgeChunk).where(KnowledgeChunk.document_id == document_id)
        await self._session.execute(stmt)
        await self._session.flush()

    async def count_by_collection(self, collection_id: UUID) -> int:
        stmt = select(func.count()).select_from(KnowledgeChunk).where(
            KnowledgeChunk.collection_id == collection_id
        )
        result = await self._session.execute(stmt)
        return result.scalar_one()


class EmbeddingJobRepository(BaseRepository[EmbeddingJob]):
    model = EmbeddingJob

    async def get_by_project(
        self, project_id: UUID, pagination: PaginationParams, status: str | None = None
    ) -> PaginatedResult[EmbeddingJob]:
        return await self.get_all(pagination, filters={"project_id": project_id, "status": status})

    async def get_pending(self, limit: int = 50) -> list[EmbeddingJob]:
        stmt = (
            select(EmbeddingJob)
            .where(EmbeddingJob.status.in_(["pending", "failed"]))
            .where(EmbeddingJob.retry_count < EmbeddingJob.max_retries)
            .limit(limit)
        )
        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    async def count_by_status(self) -> dict[str, int]:
        stmt = select(EmbeddingJob.status, func.count(EmbeddingJob.id)).group_by(EmbeddingJob.status)
        result = await self._session.execute(stmt)
        return {row[0]: row[1] for row in result.all()}


class KnowledgeMemoryRepository(BaseRepository[KnowledgeMemory]):
    model = KnowledgeMemory

    async def get_by_world(
        self, world_id: UUID, pagination: PaginationParams, memory_type: str | None = None
    ) -> PaginatedResult[KnowledgeMemory]:
        return await self.get_all(pagination, filters={"world_id": world_id, "memory_type": memory_type})

    async def get_by_project(
        self, project_id: UUID, pagination: PaginationParams, memory_type: str | None = None
    ) -> PaginatedResult[KnowledgeMemory]:
        return await self.get_all(pagination, filters={"project_id": project_id, "memory_type": memory_type})

    async def get_active_by_world(self, world_id: UUID) -> list[KnowledgeMemory]:
        stmt = select(KnowledgeMemory).where(
            KnowledgeMemory.world_id == world_id, KnowledgeMemory.is_active.is_(True)
        )
        result = await self._session.execute(stmt)
        return list(result.scalars().all())


class RetrievalHistoryRepository(BaseRepository[RetrievalHistory]):
    model = RetrievalHistory

    async def get_by_project(
        self, project_id: UUID, pagination: PaginationParams
    ) -> PaginatedResult[RetrievalHistory]:
        return await self.get_all(pagination, filters={"project_id": project_id})


class KnowledgeVersionRepository(BaseRepository[KnowledgeVersion]):
    model = KnowledgeVersion

    async def list_versions(self, entity_type: str, entity_id: UUID) -> list[KnowledgeVersion]:
        stmt = (
            select(KnowledgeVersion)
            .where(KnowledgeVersion.entity_type == entity_type, KnowledgeVersion.entity_id == entity_id)
            .order_by(KnowledgeVersion.version_number.desc())
        )
        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    async def get_next_version_number(self, entity_type: str, entity_id: UUID) -> int:
        stmt = select(func.max(KnowledgeVersion.version_number)).where(
            KnowledgeVersion.entity_type == entity_type, KnowledgeVersion.entity_id == entity_id
        )
        result = await self._session.execute(stmt)
        current = result.scalar_one_or_none()
        return (current or 0) + 1

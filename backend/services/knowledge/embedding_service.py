"""
EmbeddingService — thin orchestration layer over the EmbeddingProvider and
VectorStoreProvider abstractions. Business logic depends only on this
service, never directly on a concrete provider implementation.
"""
from __future__ import annotations

from uuid import UUID

from agents.interfaces.embedding_provider import EmbeddingProvider
from agents.interfaces.vector_store_provider import VectorRecord, VectorStoreProvider
from database.models.knowledge import KnowledgeChunk
from repositories.knowledge_repository import KnowledgeChunkRepository


class EmbeddingService:
    def __init__(
        self,
        embedding_provider: EmbeddingProvider,
        vector_store: VectorStoreProvider,
        chunk_repo: KnowledgeChunkRepository,
    ) -> None:
        self._embedder = embedding_provider
        self._vector_store = vector_store
        self._chunks = chunk_repo

    async def embed_chunks(self, chunks: list[KnowledgeChunk]) -> list[KnowledgeChunk]:
        """Embed a batch of chunks, persist the vectors, and upsert into the vector store."""
        if not chunks:
            return []

        texts = [c.content for c in chunks]
        result = await self._embedder.embed(texts)

        records: list[VectorRecord] = []
        for chunk, vector in zip(chunks, result.vectors):
            await self._chunks.update(chunk, {
                "embedding": vector,
                "embedding_model": result.model,
                "embedding_dims": result.dims,
                "is_embedded": True,
            })
            records.append(VectorRecord(
                id=str(chunk.id),
                vector=vector,
                metadata={"document_id": str(chunk.document_id), "chunk_index": chunk.chunk_index},
            ))

        namespace = str(chunks[0].collection_id)
        await self._vector_store.upsert(namespace, records)
        return chunks

    async def rehydrate_collection(self, collection_id: UUID) -> int:
        """
        Rebuild the vector store's in-memory index for a collection from
        already-embedded chunks in Postgres. Needed because the default
        InMemoryVectorStore is process-local and non-persistent.
        """
        chunks = await self._chunks.get_by_collection(collection_id, embedded_only=True)
        if not chunks:
            return 0

        records = [
            VectorRecord(
                id=str(c.id), vector=c.embedding,
                metadata={"document_id": str(c.document_id), "chunk_index": c.chunk_index},
            )
            for c in chunks
        ]
        await self._vector_store.upsert(str(collection_id), records)
        return len(records)

    async def embed_query(self, query: str) -> list[float]:
        return await self._embedder.embed_one(query)

    async def query_similar(self, collection_id: UUID, vector: list[float], top_k: int = 5):
        return await self._vector_store.query(str(collection_id), vector, top_k=top_k)

    @property
    def provider_name(self) -> str:
        return self._embedder.provider_name

    @property
    def vector_store_name(self) -> str:
        return self._vector_store.provider_name

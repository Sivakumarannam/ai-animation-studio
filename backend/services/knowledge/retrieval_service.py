"""
RetrievalService — semantic search over a collection's embedded chunks, and
context-building for downstream consumers (REST API, Story Intelligence).

Always degrades gracefully: if the collection has no embedded chunks, or the
active embedding/vector-store providers are unavailable, returns an empty
result set rather than raising — callers (especially the SI generation
pipeline) must be able to proceed with an empty RAG context.
"""
from __future__ import annotations

import time
from dataclasses import dataclass
from uuid import UUID

from apps.api.config import get_settings
from database.models.knowledge import KnowledgeChunk
from repositories.knowledge_repository import (
    KnowledgeChunkRepository,
    RetrievalHistoryRepository,
)
from services.knowledge.embedding_service import EmbeddingService


@dataclass
class RetrievedChunk:
    chunk_id: UUID
    document_id: UUID
    content: str
    score: float


class RetrievalService:
    def __init__(
        self,
        embedder: EmbeddingService,
        chunk_repo: KnowledgeChunkRepository,
        history_repo: RetrievalHistoryRepository,
    ) -> None:
        self._embedder = embedder
        self._chunks = chunk_repo
        self._history = history_repo
        self._cfg = get_settings()

    async def search(
        self,
        project_id: UUID,
        collection_id: UUID,
        query: str,
        top_k: int | None = None,
        min_score: float | None = None,
        query_source: str = "manual",
    ) -> list[RetrievedChunk]:
        top_k = top_k or self._cfg.KN_DEFAULT_TOP_K
        min_score = min_score if min_score is not None else self._cfg.KN_MIN_SIMILARITY_SCORE
        start = time.monotonic()

        try:
            await self._embedder.rehydrate_collection(collection_id)
            query_vector = await self._embedder.embed_query(query)
            matches = await self._embedder.query_similar(collection_id, query_vector, top_k=top_k)
        except Exception:
            matches = []

        results: list[RetrievedChunk] = []
        if matches:
            chunk_ids = {UUID(m.id) for m in matches}
            chunks_by_id: dict[UUID, KnowledgeChunk] = {}
            for chunk_id in chunk_ids:
                chunk = await self._chunks.get_by_id(chunk_id)
                if chunk is not None:
                    chunks_by_id[chunk_id] = chunk

            for match in matches:
                if match.score < min_score:
                    continue
                chunk = chunks_by_id.get(UUID(match.id))
                if chunk is None:
                    continue
                results.append(RetrievedChunk(
                    chunk_id=chunk.id, document_id=chunk.document_id,
                    content=chunk.content, score=match.score,
                ))

        duration_ms = int((time.monotonic() - start) * 1000)
        await self._history.create(self._history.model(
            project_id=project_id,
            collection_id=collection_id,
            query_text=query,
            query_source=query_source,
            result_count=len(results),
            top_score=results[0].score if results else 0.0,
            results=[{"chunk_id": str(r.chunk_id), "score": r.score} for r in results],
            duration_ms=duration_ms,
        ))

        return results

    async def build_context_text(
        self,
        project_id: UUID,
        collection_id: UUID,
        query: str,
        top_k: int | None = None,
        query_source: str = "manual",
    ) -> str:
        """
        Convenience helper: run a search and join the resulting chunk
        contents into a single context string ready to inject into an LLM
        prompt. Returns "" (empty context) on any failure or empty result —
        callers must treat empty context as a valid, expected case.
        """
        results = await self.search(
            project_id, collection_id, query, top_k=top_k, query_source=query_source
        )
        if not results:
            return ""
        return "\n\n---\n\n".join(r.content for r in results)

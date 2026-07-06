# Phase 4 — RAG & Knowledge Intelligence Engine service package
from services.knowledge.parser_service import DocumentParserService
from services.knowledge.chunking_service import ChunkingService
from services.knowledge.embedding_service import EmbeddingService
from services.knowledge.collection_service import KnowledgeCollectionService
from services.knowledge.document_service import KnowledgeDocumentService
from services.knowledge.retrieval_service import RetrievalService
from services.knowledge.memory_service import KnowledgeMemoryService
from services.knowledge.job_service import EmbeddingJobService
from services.knowledge.version_service import KnowledgeVersionService

__all__ = [
    "DocumentParserService", "ChunkingService", "EmbeddingService",
    "KnowledgeCollectionService", "KnowledgeDocumentService", "RetrievalService",
    "KnowledgeMemoryService", "EmbeddingJobService", "KnowledgeVersionService",
    "build_retrieval_service",
]


def build_retrieval_service(session) -> RetrievalService | None:
    """
    Best-effort construction of a RetrievalService for a given DB session.
    Used to wire Phase 4 RAG retrieval into the Story Intelligence pipeline
    (orchestrator + Celery tasks). Returns None if providers fail to
    initialize for any reason — callers must treat that as "no knowledge
    base available" and proceed without RAG context.
    """
    try:
        from agents.registry import get_embedding_provider, get_vector_store_provider
        from repositories.knowledge_repository import (
            KnowledgeChunkRepository,
            RetrievalHistoryRepository,
        )

        embedding_provider = get_embedding_provider()
        vector_store = get_vector_store_provider()
        chunk_repo = KnowledgeChunkRepository(session)
        embedder = EmbeddingService(embedding_provider, vector_store, chunk_repo)
        return RetrievalService(embedder, chunk_repo, RetrievalHistoryRepository(session))
    except Exception:
        return None

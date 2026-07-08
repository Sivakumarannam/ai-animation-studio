"""
Knowledge integration service — feeds verified research into Phase 4 RAG engine.
"""
from __future__ import annotations

from typing import Any

import structlog

from packages.utils.pagination import PaginationParams
from repositories.research_repository import (
    ResearchFactRepository,
    ResearchArticleRepository,
    ResearchTopicRepository,
)

logger = structlog.get_logger()


class KnowledgeIntegrationService:
    """
    Pushes verified research into Phase 4 KnowledgeCollection so that
    Story Intelligence can retrieve it via RAG.
    """

    def __init__(
        self,
        topic_repo: ResearchTopicRepository,
        article_repo: ResearchArticleRepository,
        fact_repo: ResearchFactRepository,
        session,
    ) -> None:
        self._topic_repo = topic_repo
        self._article_repo = article_repo
        self._fact_repo = fact_repo
        self._session = session

    async def integrate_topic(self, topic_id, project_id=None) -> dict[str, Any]:
        """
        Create a KnowledgeDocument for a researched topic so it becomes
        searchable via the Phase 4 RAG pipeline.
        """
        from uuid import UUID
        from repositories.knowledge_repository import (
            KnowledgeCollectionRepository,
            KnowledgeDocumentRepository,
            KnowledgeChunkRepository,
        )
        from services.knowledge.collection_service import KnowledgeCollectionService
        from services.knowledge.document_service import KnowledgeDocumentService
        from services.knowledge.chunking_service import ChunkingService
        from services.knowledge.embedding_service import EmbeddingService
        from services.knowledge.parser_service import DocumentParserService
        from agents.registry import get_embedding_provider, get_vector_store_provider
        from apps.api.config import get_settings

        topic = await self._topic_repo.get_by_id(UUID(str(topic_id)))
        if topic is None:
            return {"error": "topic_not_found"}

        # Build a consolidated text document
        articles_result = await self._article_repo.get_by_topic(
            topic.id, PaginationParams(page=1, page_size=5), status="processed"
        )
        facts_result = await self._fact_repo.get_by_topic(
            topic.id, PaginationParams(page=1, page_size=20), verified_only=True
        )

        doc_text_parts = [
            f"# {topic.canonical_name}\n\n",
            f"{topic.description}\n\n",
            "## Key Facts\n",
        ]
        for fact in facts_result.items:
            doc_text_parts.append(f"- {fact.statement}\n")

        for art in articles_result.items:
            doc_text_parts.append(f"\n## {art.title}\n")
            doc_text_parts.append(art.summary or art.content[:500])
            doc_text_parts.append("\n")

        full_text = "".join(doc_text_parts)

        # Find or create a "Research" collection for the project
        cfg = get_settings()
        collection_repo = KnowledgeCollectionRepository(self._session)
        vector_store = get_vector_store_provider()

        collection_svc = KnowledgeCollectionService(collection_repo, vector_store)
        # Try to find an existing research collection for this project.
        # `project_id` is a nullable FK — for global (project-less) research
        # collections we must use NULL, not a fabricated UUID, or the FK
        # constraint on kn_collections.project_id rejects the insert.
        pid = UUID(str(project_id)) if project_id else None

        # Create or reuse collection
        from sqlalchemy import select
        from database.models.knowledge import KnowledgeCollection
        stmt = select(KnowledgeCollection).where(
            KnowledgeCollection.project_id.is_(pid) if pid is None else KnowledgeCollection.project_id == pid,
            KnowledgeCollection.collection_type == "research",
        ).limit(1)
        result = await self._session.execute(stmt)
        collection = result.scalars().first()

        if collection is None:
            collection = await collection_svc.create(
                project_id=pid,
                name="Research Intelligence",
                description="Auto-generated research from Phase 5 trend discovery",
                collection_type="research",
            )

        # Create the document
        chunk_repo = KnowledgeChunkRepository(self._session)
        embedder = EmbeddingService(
            embedding_provider=get_embedding_provider(),
            vector_store=vector_store,
            chunk_repo=chunk_repo,
        )
        doc_svc = KnowledgeDocumentService(
            doc_repo=KnowledgeDocumentRepository(self._session),
            chunk_repo=chunk_repo,
            collection_repo=collection_repo,
            parser=DocumentParserService(),
            chunker=ChunkingService(cfg.KN_CHUNK_SIZE_TOKENS, cfg.KN_CHUNK_OVERLAP_TOKENS),
            embedder=embedder,
        )

        document = await doc_svc.create_document(
            collection_id=collection.id,
            project_id=pid,
            title=f"Research: {topic.canonical_name}",
            source_type="text",
            raw_text=full_text,
        )

        # Process inline (embed)
        await doc_svc.process_document(document.id)

        # Update topic to mark as queued
        await self._topic_repo.update(topic, {"status": "queued"})

        logger.info(
            "knowledge_integration_done",
            topic=topic.canonical_name,
            document_id=str(document.id),
        )
        return {
            "topic_id": str(topic.id),
            "document_id": str(document.id),
            "collection_id": str(collection.id),
            "chunk_count": document.chunk_count,
        }

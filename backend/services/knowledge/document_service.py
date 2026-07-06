"""
KnowledgeDocumentService — orchestrates the parse -> chunk -> embed pipeline
for a single document. Kept as pure business logic; Celery tasks and REST
routes both call into this service so the pipeline logic lives in one place.
"""
from __future__ import annotations

import hashlib
from uuid import UUID

from apps.api.config import get_settings
from database.models.knowledge import KnowledgeChunk, KnowledgeDocument
from packages.core.exceptions import NotFoundError, ValidationError
from packages.utils.pagination import PaginatedResult, PaginationParams
from repositories.knowledge_repository import (
    KnowledgeChunkRepository,
    KnowledgeCollectionRepository,
    KnowledgeDocumentRepository,
)
from services.knowledge.chunking_service import ChunkingService
from services.knowledge.embedding_service import EmbeddingService
from services.knowledge.parser_service import DocumentParserService


class KnowledgeDocumentService:
    def __init__(
        self,
        doc_repo: KnowledgeDocumentRepository,
        chunk_repo: KnowledgeChunkRepository,
        collection_repo: KnowledgeCollectionRepository,
        parser: DocumentParserService,
        chunker: ChunkingService,
        embedder: EmbeddingService,
    ) -> None:
        self._docs = doc_repo
        self._chunks = chunk_repo
        self._collections = collection_repo
        self._parser = parser
        self._chunker = chunker
        self._embedder = embedder
        self._cfg = get_settings()

    async def create_document(
        self,
        collection_id: UUID,
        project_id: UUID,
        title: str,
        source_type: str = "text",
        raw_text: str | None = None,
        raw_bytes: bytes | None = None,
        original_filename: str = "",
    ) -> KnowledgeDocument:
        collection = await self._collections.get_by_id(collection_id)
        if collection is None:
            raise NotFoundError(f"KnowledgeCollection {collection_id} not found")

        content_source = raw_bytes if raw_bytes is not None else (raw_text or "").encode("utf-8")
        size_mb = len(content_source) / (1024 * 1024)
        if size_mb > self._cfg.KN_MAX_DOCUMENT_SIZE_MB:
            raise ValidationError(
                f"Document exceeds max size of {self._cfg.KN_MAX_DOCUMENT_SIZE_MB}MB"
            )

        content_hash = hashlib.sha256(content_source).hexdigest()
        existing = await self._docs.get_by_hash(collection_id, content_hash)
        if existing is not None:
            return existing

        document = KnowledgeDocument(
            collection_id=collection_id,
            project_id=project_id,
            title=title,
            source_type=source_type,
            original_filename=original_filename,
            raw_content=raw_text or "",
            content_hash=content_hash,
            size_bytes=len(content_source),
            status="pending",
        )
        document = await self._docs.create(document)
        await self._collections.increment_counts(collection_id, doc_delta=1)
        return document

    async def get_document(self, document_id: UUID) -> KnowledgeDocument:
        doc = await self._docs.get_by_id(document_id)
        if doc is None:
            raise NotFoundError(f"KnowledgeDocument {document_id} not found")
        return doc

    async def list_by_collection(
        self, collection_id: UUID, pagination: PaginationParams, status: str | None = None
    ) -> PaginatedResult[KnowledgeDocument]:
        return await self._docs.get_by_collection(collection_id, pagination, status=status)

    async def list_by_project(
        self, project_id: UUID, pagination: PaginationParams
    ) -> PaginatedResult[KnowledgeDocument]:
        return await self._docs.get_by_project(project_id, pagination)

    async def delete_document(self, document_id: UUID) -> None:
        document = await self.get_document(document_id)
        await self._chunks.delete_by_document(document_id)
        await self._collections.increment_counts(
            document.collection_id, doc_delta=-1, chunk_delta=-document.chunk_count
        )
        await self._docs.delete(document)

    async def process_document(self, document_id: UUID, raw_bytes: bytes | None = None) -> KnowledgeDocument:
        """
        Full synchronous pipeline: parse -> chunk -> embed. Used both by the
        Celery task and by the synchronous TaskDispatcher fallback so
        behavior is identical regardless of execution mode.
        """
        document = await self.get_document(document_id)

        try:
            await self._docs.update(document, {"status": "parsing"})
            parsed = self._parser.parse(document.source_type, raw_bytes, document.raw_content)
            await self._docs.update(document, {"parsed_content": parsed, "status": "chunking"})

            text_chunks = self._chunker.chunk_text(parsed)
            if not text_chunks:
                await self._docs.update(document, {"status": "ready", "chunk_count": 0})
                return document

            chunk_models = [
                KnowledgeChunk(
                    document_id=document.id,
                    collection_id=document.collection_id,
                    chunk_index=tc.index,
                    content=tc.content,
                    token_count=tc.token_count,
                )
                for tc in text_chunks
            ]
            chunk_models = await self._chunks.bulk_create(chunk_models)

            await self._docs.update(document, {"status": "embedding"})
            await self._embedder.embed_chunks(chunk_models)

            await self._docs.update(document, {"status": "ready", "chunk_count": len(chunk_models)})
            await self._collections.increment_counts(document.collection_id, chunk_delta=len(chunk_models))
            return document
        except Exception as exc:
            await self._docs.update(document, {"status": "failed", "error_message": str(exc)})
            raise

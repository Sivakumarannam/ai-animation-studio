"""
Phase 4 — RAG & Knowledge Intelligence Engine Celery tasks.

Follows the exact Phase 3 pattern (see intelligence_tasks.py):
  - A @celery_app.task decorator wrapping a thin sync shell
  - _run_async() to bridge sync Celery ↔ async business logic
  - DLQ routing on max retries exhaustion
  - All actual logic delegates to KnowledgeDocumentService (no logic here)

TaskDispatcher calls these via apply_async() when Redis is available,
or calls the underlying async core function directly in sync fallback mode.
"""
from __future__ import annotations


import base64
from typing import Any

from celery import Task
from celery.utils.log import get_task_logger
from apps.worker.async_utils import run_async as _run_async
from apps.worker.main import celery_app
from apps.worker.tasks.dead_letter import dead_letter_task


logger = get_task_logger(__name__)




def _make_document_service(session):
    from agents.registry import get_embedding_provider, get_vector_store_provider
    from repositories.knowledge_repository import (
        KnowledgeChunkRepository,
        KnowledgeCollectionRepository,
        KnowledgeDocumentRepository,
    )
    from services.knowledge.chunking_service import ChunkingService
    from services.knowledge.document_service import KnowledgeDocumentService
    from services.knowledge.embedding_service import EmbeddingService
    from services.knowledge.parser_service import DocumentParserService
    from apps.api.config import get_settings

    cfg = get_settings()
    chunk_repo = KnowledgeChunkRepository(session)
    embedder = EmbeddingService(
        embedding_provider=get_embedding_provider(),
        vector_store=get_vector_store_provider(),
        chunk_repo=chunk_repo,
    )
    return KnowledgeDocumentService(
        doc_repo=KnowledgeDocumentRepository(session),
        chunk_repo=chunk_repo,
        collection_repo=KnowledgeCollectionRepository(session),
        parser=DocumentParserService(),
        chunker=ChunkingService(cfg.KN_CHUNK_SIZE_TOKENS, cfg.KN_CHUNK_OVERLAP_TOKENS),
        embedder=embedder,
    )


# ---------------------------------------------------------------------------
# Async core functions — called directly by dispatcher in sync fallback mode
# ---------------------------------------------------------------------------

async def _process_document_core(
    document_id: str,
    job_id: str,
    raw_bytes_b64: str | None = None,
) -> dict[str, Any]:
    from database.connection import get_session
    from repositories.knowledge_repository import EmbeddingJobRepository
    from services.knowledge.job_service import EmbeddingJobService
    from uuid import UUID

    raw_bytes = base64.b64decode(raw_bytes_b64) if raw_bytes_b64 else None

    async for session in get_session():
        doc_svc = _make_document_service(session)
        job_svc = EmbeddingJobService(EmbeddingJobRepository(session))

        job = None
        try:
            job = await job_svc.get_job(UUID(job_id))
            await job_svc.start_job(job.id, mode="sync")
        except Exception:
            job = None

        try:
            document = await doc_svc.process_document(UUID(document_id), raw_bytes=raw_bytes)
            result = {
                "document_id": str(document.id),
                "status": document.status,
                "chunk_count": document.chunk_count,
            }
            if job:
                await job_svc.complete_job(job.id, result)
            return result
        except Exception as exc:
            if job:
                await job_svc.fail_job(job.id, str(exc))
            raise
    return {}


async def _reembed_collection_core(
    collection_id: str,
    job_id: str,
) -> dict[str, Any]:
    from database.connection import get_session
    from repositories.knowledge_repository import (
        EmbeddingJobRepository,
        KnowledgeDocumentRepository,
    )
    from services.knowledge.job_service import EmbeddingJobService
    from packages.utils.pagination import PaginationParams
    from uuid import UUID

    async for session in get_session():
        doc_svc = _make_document_service(session)
        job_svc = EmbeddingJobService(EmbeddingJobRepository(session))
        doc_repo = KnowledgeDocumentRepository(session)

        job = None
        try:
            job = await job_svc.get_job(UUID(job_id))
            await job_svc.start_job(job.id, mode="sync")
        except Exception:
            job = None

        processed = 0
        try:
            page = 1
            while True:
                result_page = await doc_repo.get_by_collection(
                    UUID(collection_id), PaginationParams(page=page, page_size=50)
                )
                if not result_page.items:
                    break
                for document in result_page.items:
                    await doc_svc.process_document(document.id, raw_bytes=None)
                    processed += 1
                if page * 50 >= result_page.total:
                    break
                page += 1

            result = {"collection_id": collection_id, "documents_reembedded": processed}
            if job:
                await job_svc.complete_job(job.id, result)
            return result
        except Exception as exc:
            if job:
                await job_svc.fail_job(job.id, str(exc))
            raise
    return {}


# ---------------------------------------------------------------------------
# Celery Task wrappers
# ---------------------------------------------------------------------------

@celery_app.task(
    bind=True,
    name="knowledge.process_document",
    queue="ai",
    max_retries=3,
    default_retry_delay=60,
    acks_late=True,
)
def kn_process_document(
    self: Task,
    document_id: str,
    job_id: str,
    raw_bytes_b64: str | None = None,
) -> dict[str, Any]:
    logger.info(f"kn_process_document start job_id={job_id}")
    try:
        return _run_async(_process_document_core(
            document_id=document_id, job_id=job_id, raw_bytes_b64=raw_bytes_b64,
        ))
    except Exception as exc:
        logger.error(f"kn_process_document failed job_id={job_id} error={exc}")
        try:
            raise self.retry(exc=exc, countdown=60)
        except self.MaxRetriesExceededError:
            dead_letter_task.apply_async(
                kwargs={
                    "task_name": "knowledge.process_document",
                    "task_args": {"job_id": job_id, "document_id": document_id},
                    "error": str(exc),
                },
                queue="dlq",
            )
            raise


@celery_app.task(
    bind=True,
    name="knowledge.reembed_collection",
    queue="ai",
    max_retries=3,
    default_retry_delay=90,
    acks_late=True,
)
def kn_reembed_collection(
    self: Task,
    collection_id: str,
    job_id: str,
) -> dict[str, Any]:
    logger.info(f"kn_reembed_collection start job_id={job_id}")
    try:
        return _run_async(_reembed_collection_core(collection_id=collection_id, job_id=job_id))
    except Exception as exc:
        logger.error(f"kn_reembed_collection failed job_id={job_id} error={exc}")
        try:
            raise self.retry(exc=exc, countdown=90)
        except self.MaxRetriesExceededError:
            dead_letter_task.apply_async(
                kwargs={
                    "task_name": "knowledge.reembed_collection",
                    "task_args": {"job_id": job_id, "collection_id": collection_id},
                    "error": str(exc),
                },
                queue="dlq",
            )
            raise
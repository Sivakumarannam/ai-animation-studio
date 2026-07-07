"""
Phase 4 — RAG & Knowledge Intelligence Engine API router.
Prefix: /kn  (avoids collision with existing /si and library routes)
"""
from __future__ import annotations

import base64
from typing import Annotated
from uuid import UUID

import structlog
from fastapi import APIRouter, Depends, File, Query, UploadFile, status

from apps.api.dependencies import CurrentUser, SessionDep
from apps.api.schemas.intelligence import PaginationMeta
from apps.api.schemas.knowledge import (
    DispatchResponse,
    EmbeddingJobListResponse,
    EmbeddingJobResponse,
    KnowledgeCollectionCreate,
    KnowledgeCollectionListResponse,
    KnowledgeCollectionResponse,
    KnowledgeCollectionUpdate,
    KnowledgeChunkResponse,
    KnowledgeDocumentCreate,
    KnowledgeDocumentListResponse,
    KnowledgeDocumentResponse,
    KnowledgeMemoryCreate,
    KnowledgeMemoryListResponse,
    KnowledgeMemoryResponse,
    KnowledgeStats,
    KnowledgeVersionResponse,
    SearchRequest,
    SearchResponse,
    SearchResultItem,
)
from packages.utils.pagination import PaginationParams

logger = structlog.get_logger()

router = APIRouter(prefix="/kn", tags=["knowledge"])


# ─────────────────────────────────────────────────────────────────────────────
# DI helpers — built per-request from session
# ─────────────────────────────────────────────────────────────────────────────

def _make_services(session):
    """Instantiate all Phase 4 services from a single session."""
    from agents.registry import get_embedding_provider, get_vector_store_provider
    from apps.api.config import get_settings
    from repositories.knowledge_repository import (
        EmbeddingJobRepository,
        KnowledgeChunkRepository,
        KnowledgeCollectionRepository,
        KnowledgeDocumentRepository,
        KnowledgeMemoryRepository,
        KnowledgeVersionRepository,
        RetrievalHistoryRepository,
    )
    from services.knowledge.chunking_service import ChunkingService
    from services.knowledge.collection_service import KnowledgeCollectionService
    from services.knowledge.document_service import KnowledgeDocumentService
    from services.knowledge.embedding_service import EmbeddingService
    from services.knowledge.job_service import EmbeddingJobService
    from services.knowledge.memory_service import KnowledgeMemoryService
    from services.knowledge.parser_service import DocumentParserService
    from services.knowledge.retrieval_service import RetrievalService
    from services.knowledge.version_service import KnowledgeVersionService

    cfg = get_settings()
    embedding_provider = get_embedding_provider()
    vector_store = get_vector_store_provider()

    collection_repo = KnowledgeCollectionRepository(session)
    document_repo = KnowledgeDocumentRepository(session)
    chunk_repo = KnowledgeChunkRepository(session)
    job_repo = EmbeddingJobRepository(session)
    memory_repo = KnowledgeMemoryRepository(session)
    history_repo = RetrievalHistoryRepository(session)
    version_repo = KnowledgeVersionRepository(session)

    embedder = EmbeddingService(embedding_provider, vector_store, chunk_repo)
    parser = DocumentParserService()
    chunker = ChunkingService(cfg.KN_CHUNK_SIZE_TOKENS, cfg.KN_CHUNK_OVERLAP_TOKENS)

    return {
        "collection": KnowledgeCollectionService(collection_repo, vector_store),
        "document": KnowledgeDocumentService(document_repo, chunk_repo, collection_repo, parser, chunker, embedder),
        "chunk_repo": chunk_repo,
        "embedder": embedder,
        "retrieval": RetrievalService(embedder, chunk_repo, history_repo),
        "memory": KnowledgeMemoryService(memory_repo),
        "jobs": EmbeddingJobService(job_repo),
        "version": KnowledgeVersionService(version_repo),
    }


def _pagination(page: int = Query(1, ge=1), page_size: int = Query(20, ge=1, le=100)) -> PaginationParams:
    return PaginationParams(page=page, page_size=page_size)


def _meta(result) -> PaginationMeta:
    total_pages = max(1, -(-result.total // result.page_size))
    return PaginationMeta(page=result.page, page_size=result.page_size, total=result.total, total_pages=total_pages)


# ─────────────────────────────────────────────────────────────────────────────
# Collections
# ─────────────────────────────────────────────────────────────────────────────

@router.post("/projects/{project_id}/collections", response_model=KnowledgeCollectionResponse, status_code=201)
async def create_collection(
    project_id: UUID, body: KnowledgeCollectionCreate, current_user: CurrentUser, session: SessionDep,
) -> KnowledgeCollectionResponse:
    svc = _make_services(session)
    collection = await svc["collection"].create(project_id, **body.model_dump())
    return KnowledgeCollectionResponse.model_validate(collection)


@router.get("/projects/{project_id}/collections", response_model=KnowledgeCollectionListResponse)
async def list_collections(
    project_id: UUID, current_user: CurrentUser, session: SessionDep,
    pagination: Annotated[PaginationParams, Depends(_pagination)],
    status_filter: str | None = Query(None, alias="status"),
) -> KnowledgeCollectionListResponse:
    svc = _make_services(session)
    result = await svc["collection"].list_by_project(project_id, pagination, status=status_filter)
    return KnowledgeCollectionListResponse(
        items=[KnowledgeCollectionResponse.model_validate(c) for c in result.items], meta=_meta(result)
    )


@router.get("/collections/{collection_id}", response_model=KnowledgeCollectionResponse)
async def get_collection(collection_id: UUID, current_user: CurrentUser, session: SessionDep) -> KnowledgeCollectionResponse:
    svc = _make_services(session)
    return KnowledgeCollectionResponse.model_validate(await svc["collection"].get(collection_id))


@router.patch("/collections/{collection_id}", response_model=KnowledgeCollectionResponse)
async def update_collection(
    collection_id: UUID, body: KnowledgeCollectionUpdate, current_user: CurrentUser, session: SessionDep,
) -> KnowledgeCollectionResponse:
    svc = _make_services(session)
    collection = await svc["collection"].update(collection_id, body.model_dump(exclude_none=True))
    return KnowledgeCollectionResponse.model_validate(collection)


@router.delete("/collections/{collection_id}", status_code=204, response_model=None)
async def delete_collection(collection_id: UUID, current_user: CurrentUser, session: SessionDep) -> None:
    svc = _make_services(session)
    await svc["collection"].delete(collection_id)


# ─────────────────────────────────────────────────────────────────────────────
# Documents
# ─────────────────────────────────────────────────────────────────────────────

@router.post("/collections/{collection_id}/documents", response_model=KnowledgeDocumentResponse, status_code=201)
async def create_text_document(
    collection_id: UUID, body: KnowledgeDocumentCreate, current_user: CurrentUser, session: SessionDep,
) -> KnowledgeDocumentResponse:
    svc = _make_services(session)
    collection = await svc["collection"].get(collection_id)
    document = await svc["document"].create_document(
        collection_id=collection_id, project_id=collection.project_id, title=body.title,
        source_type=body.source_type, raw_text=body.raw_text,
    )
    return KnowledgeDocumentResponse.model_validate(document)


@router.post("/collections/{collection_id}/documents/upload", response_model=DispatchResponse, status_code=202)
async def upload_document(
    collection_id: UUID, current_user: CurrentUser, session: SessionDep,
    file: UploadFile = File(...),
) -> DispatchResponse:
    from apps.worker.dispatcher import get_dispatcher
    from apps.worker.tasks.knowledge_tasks import _process_document_core, kn_process_document

    svc = _make_services(session)
    collection = await svc["collection"].get(collection_id)
    raw_bytes = await file.read()
    ext = (file.filename or "").rsplit(".", 1)[-1].lower() if "." in (file.filename or "") else "txt"
    source_type = ext if ext in ("txt", "md", "csv", "json", "pdf", "docx") else "txt"

    document = await svc["document"].create_document(
        collection_id=collection_id, project_id=collection.project_id, title=file.filename or "Untitled",
        source_type=source_type, raw_bytes=raw_bytes, original_filename=file.filename or "",
    )
    job = await svc["jobs"].create_job("ingest_document", project_id=collection.project_id,
                                        collection_id=collection_id, document_id=document.id)
    await session.commit()

    raw_bytes_b64 = base64.b64encode(raw_bytes).decode("ascii")
    dispatcher = get_dispatcher()
    result = await dispatcher.dispatch(
        celery_task=kn_process_document,
        core_coro_factory=lambda: _process_document_core(
            document_id=str(document.id), job_id=str(job.id), raw_bytes_b64=raw_bytes_b64,
        ),
        job_id=str(job.id),
        queue="ai",
        task_kwargs={"document_id": str(document.id), "raw_bytes_b64": raw_bytes_b64},
    )
    return DispatchResponse(**result)


@router.get("/collections/{collection_id}/documents", response_model=KnowledgeDocumentListResponse)
async def list_documents(
    collection_id: UUID, current_user: CurrentUser, session: SessionDep,
    pagination: Annotated[PaginationParams, Depends(_pagination)],
    status_filter: str | None = Query(None, alias="status"),
) -> KnowledgeDocumentListResponse:
    svc = _make_services(session)
    result = await svc["document"].list_by_collection(collection_id, pagination, status=status_filter)
    return KnowledgeDocumentListResponse(
        items=[KnowledgeDocumentResponse.model_validate(d) for d in result.items], meta=_meta(result)
    )


@router.get("/documents/{document_id}", response_model=KnowledgeDocumentResponse)
async def get_document(document_id: UUID, current_user: CurrentUser, session: SessionDep) -> KnowledgeDocumentResponse:
    svc = _make_services(session)
    return KnowledgeDocumentResponse.model_validate(await svc["document"].get_document(document_id))


@router.get("/documents/{document_id}/chunks", response_model=list[KnowledgeChunkResponse])
async def get_document_chunks(document_id: UUID, current_user: CurrentUser, session: SessionDep) -> list[KnowledgeChunkResponse]:
    svc = _make_services(session)
    chunks = await svc["chunk_repo"].get_by_document(document_id)
    return [KnowledgeChunkResponse.model_validate(c) for c in chunks]


@router.post("/documents/{document_id}/process", response_model=DispatchResponse)
async def process_document(document_id: UUID, current_user: CurrentUser, session: SessionDep) -> DispatchResponse:
    from apps.worker.dispatcher import get_dispatcher
    from apps.worker.tasks.knowledge_tasks import _process_document_core, kn_process_document

    svc = _make_services(session)
    document = await svc["document"].get_document(document_id)
    job = await svc["jobs"].create_job("embed_document", project_id=document.project_id,
                                        collection_id=document.collection_id, document_id=document.id)
    await session.commit()

    dispatcher = get_dispatcher()
    result = await dispatcher.dispatch(
        celery_task=kn_process_document,
        core_coro_factory=lambda: _process_document_core(document_id=str(document.id), job_id=str(job.id)),
        job_id=str(job.id),
        queue="ai",
        task_kwargs={"document_id": str(document.id)},
    )
    return DispatchResponse(**result)


@router.delete("/documents/{document_id}", status_code=204, response_model=None)
async def delete_document(document_id: UUID, current_user: CurrentUser, session: SessionDep) -> None:
    svc = _make_services(session)
    await svc["document"].delete_document(document_id)


# ─────────────────────────────────────────────────────────────────────────────
# Retrieval / Search
# ─────────────────────────────────────────────────────────────────────────────

@router.post("/collections/{collection_id}/search", response_model=SearchResponse)
async def search_collection(
    collection_id: UUID, body: SearchRequest, current_user: CurrentUser, session: SessionDep,
) -> SearchResponse:
    svc = _make_services(session)
    collection = await svc["collection"].get(collection_id)
    results = await svc["retrieval"].search(
        project_id=collection.project_id, collection_id=collection_id, query=body.query,
        top_k=body.top_k, min_score=body.min_score, query_source="api",
    )
    await session.commit()
    return SearchResponse(
        query=body.query,
        results=[SearchResultItem(chunk_id=r.chunk_id, document_id=r.document_id, content=r.content, score=r.score) for r in results],
        result_count=len(results),
    )


# ─────────────────────────────────────────────────────────────────────────────
# Embedding Jobs
# ─────────────────────────────────────────────────────────────────────────────

@router.get("/projects/{project_id}/jobs", response_model=EmbeddingJobListResponse)
async def list_jobs(
    project_id: UUID, current_user: CurrentUser, session: SessionDep,
    pagination: Annotated[PaginationParams, Depends(_pagination)],
    status_filter: str | None = Query(None, alias="status"),
) -> EmbeddingJobListResponse:
    svc = _make_services(session)
    result = await svc["jobs"].list_jobs(project_id, pagination, status=status_filter)
    return EmbeddingJobListResponse(items=[EmbeddingJobResponse.model_validate(j) for j in result.items], meta=_meta(result))


@router.get("/jobs/retry-queue", response_model=list[EmbeddingJobResponse])
async def get_retry_queue(current_user: CurrentUser, session: SessionDep) -> list[EmbeddingJobResponse]:
    svc = _make_services(session)
    jobs = await svc["jobs"].get_pending_retries()
    return [EmbeddingJobResponse.model_validate(j) for j in jobs]


@router.get("/jobs/{job_id}", response_model=EmbeddingJobResponse)
async def get_job(job_id: UUID, current_user: CurrentUser, session: SessionDep) -> EmbeddingJobResponse:
    svc = _make_services(session)
    return EmbeddingJobResponse.model_validate(await svc["jobs"].get_job(job_id))


# ─────────────────────────────────────────────────────────────────────────────
# Memory
# ─────────────────────────────────────────────────────────────────────────────

@router.post("/projects/{project_id}/memory", response_model=KnowledgeMemoryResponse, status_code=201)
async def create_memory(
    project_id: UUID, body: KnowledgeMemoryCreate, current_user: CurrentUser, session: SessionDep,
) -> KnowledgeMemoryResponse:
    svc = _make_services(session)
    memory = await svc["memory"].create(project_id=project_id, **body.model_dump())
    return KnowledgeMemoryResponse.model_validate(memory)


@router.get("/projects/{project_id}/memory", response_model=KnowledgeMemoryListResponse)
async def list_memory_by_project(
    project_id: UUID, current_user: CurrentUser, session: SessionDep,
    pagination: Annotated[PaginationParams, Depends(_pagination)],
    memory_type: str | None = None,
) -> KnowledgeMemoryListResponse:
    svc = _make_services(session)
    result = await svc["memory"].list_by_project(project_id, pagination, memory_type=memory_type)
    return KnowledgeMemoryListResponse(items=[KnowledgeMemoryResponse.model_validate(m) for m in result.items], meta=_meta(result))


@router.get("/worlds/{world_id}/memory", response_model=KnowledgeMemoryListResponse)
async def list_memory_by_world(
    world_id: UUID, current_user: CurrentUser, session: SessionDep,
    pagination: Annotated[PaginationParams, Depends(_pagination)],
    memory_type: str | None = None,
) -> KnowledgeMemoryListResponse:
    svc = _make_services(session)
    result = await svc["memory"].list_by_world(world_id, pagination, memory_type=memory_type)
    return KnowledgeMemoryListResponse(items=[KnowledgeMemoryResponse.model_validate(m) for m in result.items], meta=_meta(result))


@router.delete("/memory/{memory_id}", status_code=204, response_model=None)
async def deactivate_memory(memory_id: UUID, current_user: CurrentUser, session: SessionDep) -> None:
    svc = _make_services(session)
    await svc["memory"].deactivate(memory_id)


# ─────────────────────────────────────────────────────────────────────────────
# Versions
# ─────────────────────────────────────────────────────────────────────────────

@router.get("/{entity_type}/{entity_id}/versions", response_model=list[KnowledgeVersionResponse])
async def list_versions(entity_type: str, entity_id: UUID, current_user: CurrentUser, session: SessionDep) -> list[KnowledgeVersionResponse]:
    svc = _make_services(session)
    versions = await svc["version"].list_versions(entity_type, entity_id)
    return [KnowledgeVersionResponse.model_validate(v) for v in versions]


# ─────────────────────────────────────────────────────────────────────────────
# Stats
# ─────────────────────────────────────────────────────────────────────────────

@router.get("/projects/{project_id}/stats", response_model=KnowledgeStats)
async def get_stats(project_id: UUID, current_user: CurrentUser, session: SessionDep) -> KnowledgeStats:
    from packages.utils.pagination import PaginationParams as PP

    svc = _make_services(session)
    collections = await svc["collection"].list_by_project(project_id, PP(page=1, page_size=1))
    documents = await svc["document"].list_by_project(project_id, PP(page=1, page_size=1))
    memories = await svc["memory"].list_by_project(project_id, PP(page=1, page_size=1))
    jobs_by_status = await svc["jobs"].status_counts()

    chunk_count = 0
    embedded_count = 0
    for c in (await svc["collection"].list_by_project(project_id, PP(page=1, page_size=100))).items:
        chunk_count += c.chunk_count
        embedded_chunks = await svc["chunk_repo"].get_by_collection(c.id, embedded_only=True)
        embedded_count += len(embedded_chunks)

    return KnowledgeStats(
        collections=collections.total,
        documents=documents.total,
        chunks=chunk_count,
        embedded_chunks=embedded_count,
        memories=memories.total,
        jobs_by_status=jobs_by_status,
        embedding_provider=svc["embedder"].provider_name,
        vector_store_provider=svc["embedder"].vector_store_name,
    )

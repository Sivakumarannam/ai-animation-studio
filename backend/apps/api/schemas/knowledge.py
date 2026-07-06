"""
Phase 4 — RAG & Knowledge Intelligence Engine Pydantic schemas.
All request/response models for the /kn (knowledge) API.
"""
from __future__ import annotations

from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, Field

from apps.api.schemas.intelligence import PaginationMeta


# ─────────────────────────────────────────────────────────────────────────────
# Collection
# ─────────────────────────────────────────────────────────────────────────────

class KnowledgeCollectionCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=500)
    description: str = ""
    collection_type: str = "general"
    world_id: UUID | None = None
    settings: dict[str, Any] = {}


class KnowledgeCollectionUpdate(BaseModel):
    name: str | None = None
    description: str | None = None
    collection_type: str | None = None
    status: str | None = None
    settings: dict[str, Any] | None = None


class KnowledgeCollectionResponse(BaseModel):
    id: UUID
    project_id: UUID
    world_id: UUID | None
    name: str
    description: str
    collection_type: str
    status: str
    document_count: int
    chunk_count: int
    settings: dict[str, Any]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class KnowledgeCollectionListResponse(BaseModel):
    items: list[KnowledgeCollectionResponse]
    meta: PaginationMeta


# ─────────────────────────────────────────────────────────────────────────────
# Document
# ─────────────────────────────────────────────────────────────────────────────

class KnowledgeDocumentCreate(BaseModel):
    title: str = Field(..., min_length=1, max_length=500)
    source_type: str = "text"
    raw_text: str | None = None


class KnowledgeDocumentResponse(BaseModel):
    id: UUID
    collection_id: UUID
    project_id: UUID
    title: str
    source_type: str
    original_filename: str
    size_bytes: int
    status: str
    error_message: str
    chunk_count: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class KnowledgeDocumentListResponse(BaseModel):
    items: list[KnowledgeDocumentResponse]
    meta: PaginationMeta


# ─────────────────────────────────────────────────────────────────────────────
# Chunk (read-only, for inspection)
# ─────────────────────────────────────────────────────────────────────────────

class KnowledgeChunkResponse(BaseModel):
    id: UUID
    document_id: UUID
    chunk_index: int
    content: str
    token_count: int
    embedding_model: str
    embedding_dims: int
    is_embedded: bool

    class Config:
        from_attributes = True


# ─────────────────────────────────────────────────────────────────────────────
# Embedding jobs
# ─────────────────────────────────────────────────────────────────────────────

class EmbeddingJobResponse(BaseModel):
    id: UUID
    project_id: UUID | None
    collection_id: UUID | None
    document_id: UUID | None
    job_type: str
    status: str
    execution_mode: str
    progress_percent: int
    current_step: str
    chunks_processed: int
    chunks_total: int
    result: dict[str, Any]
    error_message: str
    retry_count: int
    created_at: datetime

    class Config:
        from_attributes = True


class EmbeddingJobListResponse(BaseModel):
    items: list[EmbeddingJobResponse]
    meta: PaginationMeta


class DispatchResponse(BaseModel):
    job_id: str
    task_id: str
    mode: str
    status: str
    result: dict[str, Any] | None = None


# ─────────────────────────────────────────────────────────────────────────────
# Retrieval / Search
# ─────────────────────────────────────────────────────────────────────────────

class SearchRequest(BaseModel):
    query: str = Field(..., min_length=1)
    top_k: int | None = None
    min_score: float | None = None


class SearchResultItem(BaseModel):
    chunk_id: UUID
    document_id: UUID
    content: str
    score: float


class SearchResponse(BaseModel):
    query: str
    results: list[SearchResultItem]
    result_count: int


# ─────────────────────────────────────────────────────────────────────────────
# Memory
# ─────────────────────────────────────────────────────────────────────────────

class KnowledgeMemoryCreate(BaseModel):
    memory_type: str = "fact"
    key: str = Field(..., min_length=1, max_length=500)
    value: dict[str, Any] = {}
    world_id: UUID | None = None
    collection_id: UUID | None = None
    confidence: float = 1.0


class KnowledgeMemoryResponse(BaseModel):
    id: UUID
    project_id: UUID
    world_id: UUID | None
    collection_id: UUID | None
    source_chunk_id: UUID | None
    memory_type: str
    key: str
    value: dict[str, Any]
    confidence: float
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True


class KnowledgeMemoryListResponse(BaseModel):
    items: list[KnowledgeMemoryResponse]
    meta: PaginationMeta


# ─────────────────────────────────────────────────────────────────────────────
# Versions
# ─────────────────────────────────────────────────────────────────────────────

class KnowledgeVersionResponse(BaseModel):
    id: UUID
    entity_type: str
    entity_id: UUID
    version_number: int
    snapshot: dict[str, Any]
    change_summary: str
    created_by: str
    created_at: datetime

    class Config:
        from_attributes = True


# ─────────────────────────────────────────────────────────────────────────────
# Stats
# ─────────────────────────────────────────────────────────────────────────────

class KnowledgeStats(BaseModel):
    collections: int
    documents: int
    chunks: int
    embedded_chunks: int
    memories: int
    jobs_by_status: dict[str, int]
    embedding_provider: str
    vector_store_provider: str

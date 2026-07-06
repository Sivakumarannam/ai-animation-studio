"""
Phase 4 — RAG & Knowledge Intelligence Engine database models.

All tables are prefixed with `kn_` (Knowledge) to avoid collisions with
Phase 1/2/3 tables. Tables are intentionally consolidated (extra structured
data lives in JSON metadata columns) rather than proliferated, per the
Phase 4 spec.

Hierarchy:
  Project
    └─ KnowledgeCollection (kn_collections)
         └─ KnowledgeDocument (kn_documents)
              └─ KnowledgeChunk (kn_chunks)   [stores embedding as JSON float array]

Cross-cutting:
  EmbeddingJob      — tracks async embedding generation (mirrors si_generation_jobs)
  KnowledgeMemory   — world-scoped long-term knowledge distilled from documents
  RetrievalHistory  — every retrieval/search call, for observability + debugging
  KnowledgeVersion  — polymorphic snapshot store (mirrors si_story_versions)
"""
from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any

from sqlalchemy import (
    Boolean,
    DateTime,
    Float,
    ForeignKey,
    Index,
    Integer,
    JSON,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from database.base import Base, TimestampMixin, UUIDMixin


# ---------------------------------------------------------------------------
# KnowledgeCollection
# ---------------------------------------------------------------------------

class KnowledgeCollection(UUIDMixin, TimestampMixin, Base):
    """
    A named group of documents (e.g. "Season 1 Lore", "Writer's Bible").
    Optionally scoped to a Story Intelligence World for cross-referencing.
    """
    __tablename__ = "kn_collections"

    project_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("projects.id", ondelete="CASCADE"),
        nullable=False, index=True
    )
    world_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("si_worlds.id", ondelete="SET NULL"),
        nullable=True, index=True
    )
    name: Mapped[str] = mapped_column(String(500), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False, default="")
    collection_type: Mapped[str] = mapped_column(String(100), nullable=False, default="general")
    # "general" | "lore" | "character_bible" | "research" | "reference"
    status: Mapped[str] = mapped_column(String(50), nullable=False, default="active", index=True)
    document_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    chunk_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    settings: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False, default=dict)
    metadata_: Mapped[dict[str, Any]] = mapped_column("kn_metadata", JSON, nullable=False, default=dict)

    documents: Mapped[list["KnowledgeDocument"]] = relationship(
        "KnowledgeDocument", back_populates="collection", lazy="select",
        order_by="KnowledgeDocument.created_at"
    )

    __table_args__ = (
        Index("ix_kn_collections_project_status", "project_id", "status"),
    )


# ---------------------------------------------------------------------------
# KnowledgeDocument
# ---------------------------------------------------------------------------

class KnowledgeDocument(UUIDMixin, TimestampMixin, Base):
    """
    A single ingested source document (uploaded file or manual text entry).
    Parsed content + chunking/embedding status live here.
    """
    __tablename__ = "kn_documents"

    collection_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("kn_collections.id", ondelete="CASCADE"),
        nullable=False, index=True
    )
    project_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("projects.id", ondelete="CASCADE"),
        nullable=False, index=True
    )
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    source_type: Mapped[str] = mapped_column(String(50), nullable=False, default="text")
    # "txt" | "md" | "csv" | "json" | "pdf" | "docx" | "text" (manual entry)
    original_filename: Mapped[str] = mapped_column(String(500), nullable=False, default="")
    storage_key: Mapped[str] = mapped_column(String(1000), nullable=False, default="")
    raw_content: Mapped[str] = mapped_column(Text, nullable=False, default="")
    parsed_content: Mapped[str] = mapped_column(Text, nullable=False, default="")
    content_hash: Mapped[str] = mapped_column(String(64), nullable=False, default="", index=True)
    size_bytes: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    status: Mapped[str] = mapped_column(String(50), nullable=False, default="pending", index=True)
    # "pending" | "parsing" | "parsed" | "chunking" | "embedding" | "ready" | "failed"
    error_message: Mapped[str] = mapped_column(Text, nullable=False, default="")
    chunk_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    metadata_: Mapped[dict[str, Any]] = mapped_column("kn_metadata", JSON, nullable=False, default=dict)

    collection: Mapped["KnowledgeCollection"] = relationship("KnowledgeCollection", back_populates="documents")
    chunks: Mapped[list["KnowledgeChunk"]] = relationship(
        "KnowledgeChunk", back_populates="document", lazy="select",
        order_by="KnowledgeChunk.chunk_index"
    )

    __table_args__ = (
        Index("ix_kn_documents_collection_status", "collection_id", "status"),
    )


# ---------------------------------------------------------------------------
# KnowledgeChunk
# ---------------------------------------------------------------------------

class KnowledgeChunk(UUIDMixin, TimestampMixin, Base):
    """
    A chunk of a document's text plus its embedding vector (stored as a JSON
    float array — no pgvector dependency). Similarity search is performed in
    pure Python via cosine similarity over these vectors.
    """
    __tablename__ = "kn_chunks"

    document_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("kn_documents.id", ondelete="CASCADE"),
        nullable=False, index=True
    )
    collection_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("kn_collections.id", ondelete="CASCADE"),
        nullable=False, index=True
    )
    chunk_index: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    content: Mapped[str] = mapped_column(Text, nullable=False, default="")
    token_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    embedding: Mapped[list[float]] = mapped_column(JSON, nullable=False, default=list)
    embedding_model: Mapped[str] = mapped_column(String(200), nullable=False, default="")
    embedding_dims: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    is_embedded: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False, index=True)
    metadata_: Mapped[dict[str, Any]] = mapped_column("kn_metadata", JSON, nullable=False, default=dict)

    document: Mapped["KnowledgeDocument"] = relationship("KnowledgeDocument", back_populates="chunks")

    __table_args__ = (
        Index("ix_kn_chunks_collection_embedded", "collection_id", "is_embedded"),
        UniqueConstraint("document_id", "chunk_index", name="uq_kn_chunk_document_index"),
    )


# ---------------------------------------------------------------------------
# EmbeddingJob
# ---------------------------------------------------------------------------

class EmbeddingJob(UUIDMixin, TimestampMixin, Base):
    """Tracks one async embedding/ingestion request (mirrors si_generation_jobs)."""
    __tablename__ = "kn_embedding_jobs"

    project_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("projects.id", ondelete="SET NULL"),
        nullable=True, index=True
    )
    collection_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("kn_collections.id", ondelete="SET NULL"),
        nullable=True, index=True
    )
    document_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("kn_documents.id", ondelete="SET NULL"),
        nullable=True, index=True
    )
    job_type: Mapped[str] = mapped_column(String(100), nullable=False, default="embed_document", index=True)
    # "ingest_document" | "embed_document" | "reembed_collection"
    status: Mapped[str] = mapped_column(String(50), nullable=False, default="pending", index=True)
    # "pending" | "running" | "completed" | "failed"
    celery_task_id: Mapped[str] = mapped_column(String(255), nullable=False, default="")
    execution_mode: Mapped[str] = mapped_column(String(20), nullable=False, default="sync")
    progress_percent: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    current_step: Mapped[str] = mapped_column(String(200), nullable=False, default="")
    chunks_processed: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    chunks_total: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    result: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False, default=dict)
    error_message: Mapped[str] = mapped_column(Text, nullable=False, default="")
    retry_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    max_retries: Mapped[int] = mapped_column(Integer, nullable=False, default=3)
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    __table_args__ = (
        Index("ix_kn_embedding_jobs_project_status", "project_id", "status"),
    )


# ---------------------------------------------------------------------------
# KnowledgeMemory
# ---------------------------------------------------------------------------

class KnowledgeMemory(UUIDMixin, TimestampMixin, Base):
    """
    World-scoped, long-term distilled knowledge (facts extracted from
    documents). Separate from si_story_memory — this table specifically
    holds RAG-sourced facts with provenance back to the source chunk.
    """
    __tablename__ = "kn_memory"

    world_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("si_worlds.id", ondelete="CASCADE"),
        nullable=True, index=True
    )
    project_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("projects.id", ondelete="CASCADE"),
        nullable=False, index=True
    )
    collection_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("kn_collections.id", ondelete="SET NULL"),
        nullable=True, index=True
    )
    source_chunk_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("kn_chunks.id", ondelete="SET NULL"),
        nullable=True
    )
    memory_type: Mapped[str] = mapped_column(String(100), nullable=False, default="fact", index=True)
    # "fact" | "rule" | "lore" | "entity" | "summary"
    key: Mapped[str] = mapped_column(String(500), nullable=False)
    value: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False, default=dict)
    confidence: Mapped[float] = mapped_column(Float, nullable=False, default=1.0)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)

    __table_args__ = (
        Index("ix_kn_memory_world_type", "world_id", "memory_type"),
        Index("ix_kn_memory_project_type", "project_id", "memory_type"),
    )


# ---------------------------------------------------------------------------
# RetrievalHistory
# ---------------------------------------------------------------------------

class RetrievalHistory(UUIDMixin, TimestampMixin, Base):
    """Every semantic search / context-retrieval call, for observability."""
    __tablename__ = "kn_retrieval_history"

    project_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("projects.id", ondelete="CASCADE"),
        nullable=False, index=True
    )
    collection_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("kn_collections.id", ondelete="SET NULL"),
        nullable=True, index=True
    )
    query_text: Mapped[str] = mapped_column(Text, nullable=False, default="")
    query_source: Mapped[str] = mapped_column(String(100), nullable=False, default="manual")
    # "manual" | "story_intelligence" | "api"
    result_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    top_score: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    results: Mapped[list[Any]] = mapped_column(JSON, nullable=False, default=list)
    duration_ms: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    __table_args__ = (
        Index("ix_kn_retrieval_history_project", "project_id", "created_at"),
    )


# ---------------------------------------------------------------------------
# KnowledgeVersion (polymorphic snapshot store — mirrors StoryVersion)
# ---------------------------------------------------------------------------

class KnowledgeVersion(UUIDMixin, TimestampMixin, Base):
    """Full JSON snapshot of any Knowledge entity at a point in time."""
    __tablename__ = "kn_versions"

    entity_type: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    entity_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False, index=True)
    version_number: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    snapshot: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False, default=dict)
    change_summary: Mapped[str] = mapped_column(Text, nullable=False, default="")
    created_by: Mapped[str] = mapped_column(String(100), nullable=False, default="system")

    __table_args__ = (
        Index("ix_kn_versions_entity", "entity_type", "entity_id"),
    )

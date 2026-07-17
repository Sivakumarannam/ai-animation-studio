"""
Phase 10 — Video Assembly Engine SQLAlchemy models.
Table prefix: va_*  (mirrors an_* / vo_* / mu_* from Phases 7-9)

Tables:
  va_jobs          — one row per assembly job (episode or short-form cut)
  va_outputs       — finished video files produced by an assembly job
  va_retry_queue   — failed jobs awaiting retry
"""
from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import (
    JSON,
    BigInteger,
    Boolean,
    DateTime,
    Float,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    func,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from database.base import Base


# ---------------------------------------------------------------------------
# VideoAssemblyJob
# ---------------------------------------------------------------------------

class VideoAssemblyJob(Base):
    """Tracks one video assembly run — episode-level or short-form cut."""

    __tablename__ = "va_jobs"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    project_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    episode_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), nullable=True)

    # "assemble_episode" | "assemble_short_form" | "process_retry_queue"
    job_type: Mapped[str] = mapped_column(String(50), nullable=False, default="assemble_episode")
    # "pending" | "running" | "completed" | "failed"
    status: Mapped[str] = mapped_column(String(50), nullable=False, default="pending")
    # "sync" | "async" | "celery"
    mode: Mapped[str] = mapped_column(String(20), nullable=False, default="sync")

    triggered_by: Mapped[str] = mapped_column(String(100), nullable=False, default="api")
    params: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)
    result: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)

    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    duration_seconds: Mapped[float | None] = mapped_column(Float, nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now()
    )

    __table_args__ = (
        Index("ix_va_jobs_project_id", "project_id"),
        Index("ix_va_jobs_status", "status"),
        Index("ix_va_jobs_episode_id", "episode_id"),
        Index("ix_va_jobs_project_status", "project_id", "status"),
    )


# ---------------------------------------------------------------------------
# VideoOutput
# ---------------------------------------------------------------------------

class VideoOutput(Base):
    """A finished video file produced by an assembly job."""

    __tablename__ = "va_outputs"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    job_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("va_jobs.id", ondelete="CASCADE"),
        nullable=False,
    )
    project_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    episode_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), nullable=True)

    # "episode_cut" | "short_form_cut" | "preview"
    output_type: Mapped[str] = mapped_column(String(100), nullable=False, default="episode_cut")
    # "pending" | "processing" | "completed" | "failed"
    status: Mapped[str] = mapped_column(String(50), nullable=False, default="completed")

    storage_key: Mapped[str] = mapped_column(String(2000), nullable=False, default="")
    storage_bucket: Mapped[str] = mapped_column(String(500), nullable=False, default="videos")
    file_size_bytes: Mapped[int] = mapped_column(BigInteger, nullable=False, default=0)
    duration_seconds: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)

    width: Mapped[int] = mapped_column(Integer, nullable=False, default=1920)
    height: Mapped[int] = mapped_column(Integer, nullable=False, default=1080)
    fps: Mapped[int] = mapped_column(Integer, nullable=False, default=24)
    # "mp4" | "webm"
    format: Mapped[str] = mapped_column(String(20), nullable=False, default="mp4")
    # "mock" | "ffmpeg"
    provider: Mapped[str] = mapped_column(String(100), nullable=False, default="mock")

    # Number of source tracks composited
    scene_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    has_voice: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    has_music: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    has_subtitles: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)

    # Quality gate: did assembled duration match expected within tolerance?
    quality_passed: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    quality_score: Mapped[float] = mapped_column(Float, nullable=False, default=100.0)

    output_metadata: Mapped[dict] = mapped_column("va_output_meta", JSON, nullable=False, default=dict)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )

    __table_args__ = (
        Index("ix_va_outputs_project_id", "project_id"),
        Index("ix_va_outputs_job_id", "job_id"),
        Index("ix_va_outputs_episode_id", "episode_id"),
        Index("ix_va_outputs_output_type", "output_type"),
    )


# ---------------------------------------------------------------------------
# VideoAssemblyRetryQueue
# ---------------------------------------------------------------------------

class VideoAssemblyRetryQueue(Base):
    """Tracks failed assembly jobs pending retry."""

    __tablename__ = "va_retry_queue"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    project_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    episode_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), nullable=True)
    original_job_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), nullable=True)

    # "pending" | "retrying" | "resolved" | "exhausted"
    status: Mapped[str] = mapped_column(String(50), nullable=False, default="pending")
    retry_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    max_retries: Mapped[int] = mapped_column(Integer, nullable=False, default=3)

    reason: Mapped[str] = mapped_column(Text, nullable=False, default="")
    params: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)

    next_retry_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    resolved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now()
    )

    __table_args__ = (
        Index("ix_va_retry_queue_project_id", "project_id"),
        Index("ix_va_retry_queue_status", "status"),
        Index("ix_va_retry_queue_project_status", "project_id", "status"),
    )

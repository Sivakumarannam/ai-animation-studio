"""
Phase 7 — Animation Engine database models.

All tables are prefixed with `an_` (Animation) to avoid collisions.

Hierarchy:
  AnimationJob         (an_jobs)          — async render job tracking
  AnimationRenderOutput (an_render_outputs) — video clip outputs
  AnimationRetryQueue  (an_retry_queue)   — retry queue for failed renders
"""
from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any

from sqlalchemy import (
    BigInteger,
    Boolean,
    DateTime,
    Float,
    ForeignKey,
    Index,
    Integer,
    JSON,
    String,
    Text,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from database.base import Base, TimestampMixin, UUIDMixin


# ---------------------------------------------------------------------------
# AnimationJob
# ---------------------------------------------------------------------------

class AnimationJob(UUIDMixin, TimestampMixin, Base):
    """Async job record for animation render/composite operations."""
    __tablename__ = "an_jobs"

    project_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("projects.id", ondelete="CASCADE"),
        nullable=False, index=True,
    )
    scene_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), nullable=True, index=True,
    )
    episode_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), nullable=True, index=True,
    )
    # "render_scene" | "render_episode" | "composite_scene" | "render_retry_queue"
    job_type: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    # "pending" | "running" | "completed" | "failed"
    status: Mapped[str] = mapped_column(String(50), nullable=False, default="pending", index=True)
    # "sync" | "async" | "celery"
    mode: Mapped[str] = mapped_column(String(20), nullable=False, default="sync")
    triggered_by: Mapped[str] = mapped_column(String(100), nullable=False, default="api")

    params: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False, default=dict)
    result: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False, default=dict)
    error_message: Mapped[str] = mapped_column(Text, nullable=False, default="")

    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    duration_seconds: Mapped[float | None] = mapped_column(Float, nullable=True)

    __table_args__ = (
        Index("ix_an_jobs_project_status", "project_id", "status"),
        Index("ix_an_jobs_project_type", "project_id", "job_type"),
    )


# ---------------------------------------------------------------------------
# AnimationRenderOutput
# ---------------------------------------------------------------------------

class AnimationRenderOutput(UUIDMixin, TimestampMixin, Base):
    """Video clip produced by a render job."""
    __tablename__ = "an_render_outputs"

    job_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("an_jobs.id", ondelete="CASCADE"),
        nullable=False, index=True,
    )
    project_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("projects.id", ondelete="CASCADE"),
        nullable=False, index=True,
    )
    scene_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), nullable=True, index=True,
    )
    episode_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), nullable=True, index=True,
    )

    # "scene_clip" | "episode_video" | "preview"
    output_type: Mapped[str] = mapped_column(String(100), nullable=False, default="scene_clip", index=True)
    # "pending" | "processing" | "completed" | "failed"
    status: Mapped[str] = mapped_column(String(50), nullable=False, default="pending", index=True)

    storage_key: Mapped[str] = mapped_column(String(2000), nullable=False, default="")
    storage_bucket: Mapped[str] = mapped_column(String(500), nullable=False, default="animations")
    file_size_bytes: Mapped[int] = mapped_column(BigInteger, nullable=False, default=0)
    duration_seconds: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    width: Mapped[int] = mapped_column(Integer, nullable=False, default=1920)
    height: Mapped[int] = mapped_column(Integer, nullable=False, default=1080)
    fps: Mapped[int] = mapped_column(Integer, nullable=False, default=24)
    # "mp4" | "webm" | "gif"
    format: Mapped[str] = mapped_column(String(20), nullable=False, default="mp4")
    # "mock" | "ffmpeg"
    provider: Mapped[str] = mapped_column(String(100), nullable=False, default="mock")

    render_params: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False, default=dict)
    metadata_: Mapped[dict[str, Any]] = mapped_column("an_render_output_meta", JSON, nullable=False, default=dict)

    job: Mapped["AnimationJob"] = relationship("AnimationJob")

    __table_args__ = (
        Index("ix_an_render_outputs_project_type", "project_id", "output_type"),
    )


# ---------------------------------------------------------------------------
# AnimationRetryQueue
# ---------------------------------------------------------------------------

class AnimationRetryQueue(UUIDMixin, TimestampMixin, Base):
    """Queue of failed renders awaiting retry."""
    __tablename__ = "an_retry_queue"

    project_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("projects.id", ondelete="CASCADE"),
        nullable=False, index=True,
    )
    scene_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), nullable=True, index=True,
    )
    episode_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), nullable=True, index=True,
    )
    original_job_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("an_jobs.id", ondelete="SET NULL"),
        nullable=True,
    )
    retry_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    max_retries: Mapped[int] = mapped_column(Integer, nullable=False, default=3)
    # "pending" | "retrying" | "resolved" | "exhausted"
    status: Mapped[str] = mapped_column(String(50), nullable=False, default="pending", index=True)
    reason: Mapped[str] = mapped_column(Text, nullable=False, default="")
    next_retry_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    resolved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    params: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False, default=dict)

    __table_args__ = (
        Index("ix_an_retry_queue_project_status", "project_id", "status"),
    )

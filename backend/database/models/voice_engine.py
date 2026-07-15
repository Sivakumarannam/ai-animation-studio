"""
Phase 8 — Voice Engine SQLAlchemy models.
Table prefix: vo_*  (mirrors an_* from Phase 7)

Tables:
  vo_jobs           — one row per voice generation job (single line or full scene)
  vo_outputs        — one row per generated audio clip
  vo_retry_queue    — tracks failed jobs pending retry
"""
from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import (
    JSON,
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


class VoiceGenerationJob(Base):
    """Tracks a voice generation run — single dialogue line or full scene."""

    __tablename__ = "vo_jobs"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    project_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    scene_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), nullable=True)
    episode_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), nullable=True)
    character_id: Mapped[str | None] = mapped_column(String(255), nullable=True)

    job_type: Mapped[str] = mapped_column(
        String(50), nullable=False, default="generate_line"
    )  # generate_line | generate_scene | process_retry_queue
    status: Mapped[str] = mapped_column(
        String(50), nullable=False, default="pending"
    )  # pending | running | completed | failed

    triggered_by: Mapped[str] = mapped_column(String(100), nullable=False, default="api")
    params: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)
    result: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)

    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now()
    )

    __table_args__ = (
        Index("ix_vo_jobs_project_id", "project_id"),
        Index("ix_vo_jobs_status", "status"),
        Index("ix_vo_jobs_scene_id", "scene_id"),
        Index("ix_vo_jobs_episode_id", "episode_id"),
    )


class VoiceOutput(Base):
    """A single generated audio clip — one per dialogue line."""

    __tablename__ = "vo_outputs"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    job_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("vo_jobs.id", ondelete="CASCADE"),
        nullable=False,
    )
    project_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    scene_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), nullable=True)

    character_id: Mapped[str | None] = mapped_column(String(255), nullable=True)
    character_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    dialogue_line: Mapped[str] = mapped_column(Text, nullable=False, default="")
    language: Mapped[str] = mapped_column(String(20), nullable=False, default="en")
    emotion: Mapped[str] = mapped_column(String(50), nullable=False, default="neutral")
    voice_id: Mapped[str | None] = mapped_column(String(255), nullable=True)

    storage_key: Mapped[str] = mapped_column(String(1024), nullable=False, default="")
    duration_seconds: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    sample_rate: Mapped[int] = mapped_column(Integer, nullable=False, default=22050)
    format: Mapped[str] = mapped_column(String(20), nullable=False, default="wav")
    file_size_bytes: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    provider: Mapped[str] = mapped_column(String(100), nullable=False, default="mock")

    status: Mapped[str] = mapped_column(
        String(50), nullable=False, default="completed"
    )  # completed | failed
    output_metadata: Mapped[dict] = mapped_column("vo_output_meta", JSON, nullable=False, default=dict)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )

    __table_args__ = (
        Index("ix_vo_outputs_project_id", "project_id"),
        Index("ix_vo_outputs_job_id", "job_id"),
        Index("ix_vo_outputs_scene_id", "scene_id"),
        Index("ix_vo_outputs_character_id", "character_id"),
    )


class VoiceRetryQueue(Base):
    """Tracks failed voice generation lines pending retry."""

    __tablename__ = "vo_retry_queue"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    project_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    scene_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), nullable=True)
    episode_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), nullable=True)
    original_job_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), nullable=True)

    status: Mapped[str] = mapped_column(
        String(50), nullable=False, default="pending"
    )  # pending | retrying | resolved | exhausted
    retry_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    max_retries: Mapped[int] = mapped_column(Integer, nullable=False, default=3)

    reason: Mapped[str] = mapped_column(Text, nullable=False, default="")
    params: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)

    next_retry_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now()
    )

    __table_args__ = (
        Index("ix_vo_retry_queue_project_id", "project_id"),
        Index("ix_vo_retry_queue_status", "status"),
    )

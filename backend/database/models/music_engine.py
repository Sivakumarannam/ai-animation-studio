"""
Phase 9 — Music & Sound Engine SQLAlchemy models.
Table prefix: mu_*  (mirrors an_* / vo_* from Phases 7-8)

Tables:
  mu_jobs          — one row per music/SFX generation job
  mu_outputs       — generated audio tracks (music or SFX rendered output)
  mu_sfx_assets    — pre-seeded SFX library entries (footsteps, doors, etc.)
  mu_retry_queue   — failed jobs awaiting retry
"""
from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import (
    JSON,
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
# MusicGenerationJob
# ---------------------------------------------------------------------------

class MusicGenerationJob(Base):
    """Tracks a music or SFX generation run."""

    __tablename__ = "mu_jobs"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    project_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    scene_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), nullable=True)
    episode_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), nullable=True)

    # "generate_track" | "generate_scene_audio" | "process_retry_queue"
    job_type: Mapped[str] = mapped_column(String(50), nullable=False, default="generate_track")
    # "pending" | "running" | "completed" | "failed"
    status: Mapped[str] = mapped_column(String(50), nullable=False, default="pending")

    # Music mood: comedy | adventure | sad | happy | tension | victory | neutral
    mood: Mapped[str] = mapped_column(String(50), nullable=False, default="neutral")

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
        Index("ix_mu_jobs_project_id", "project_id"),
        Index("ix_mu_jobs_status", "status"),
        Index("ix_mu_jobs_scene_id", "scene_id"),
        Index("ix_mu_jobs_episode_id", "episode_id"),
        Index("ix_mu_jobs_project_status", "project_id", "status"),
    )


# ---------------------------------------------------------------------------
# MusicOutput
# ---------------------------------------------------------------------------

class MusicOutput(Base):
    """A single generated audio track — background music or SFX mix."""

    __tablename__ = "mu_outputs"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    job_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("mu_jobs.id", ondelete="CASCADE"),
        nullable=False,
    )
    project_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    scene_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), nullable=True)
    episode_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), nullable=True)

    # "background_music" | "sfx_mix" | "scene_audio"
    output_type: Mapped[str] = mapped_column(String(100), nullable=False, default="background_music")
    mood: Mapped[str] = mapped_column(String(50), nullable=False, default="neutral")
    # "looping" | "one_shot"
    loop_type: Mapped[str] = mapped_column(String(50), nullable=False, default="looping")

    storage_key: Mapped[str] = mapped_column(String(1024), nullable=False, default="")
    duration_seconds: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    sample_rate: Mapped[int] = mapped_column(Integer, nullable=False, default=44100)
    # "wav" | "mp3" | "ogg"
    format: Mapped[str] = mapped_column(String(20), nullable=False, default="wav")
    file_size_bytes: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    # "mock" | "suno" | "udio" | "musicgen"
    provider: Mapped[str] = mapped_column(String(100), nullable=False, default="mock")
    copyright_safe: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)

    # "completed" | "failed"
    status: Mapped[str] = mapped_column(String(50), nullable=False, default="completed")
    output_metadata: Mapped[dict] = mapped_column("mu_output_meta", JSON, nullable=False, default=dict)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )

    __table_args__ = (
        Index("ix_mu_outputs_project_id", "project_id"),
        Index("ix_mu_outputs_job_id", "job_id"),
        Index("ix_mu_outputs_scene_id", "scene_id"),
        Index("ix_mu_outputs_episode_id", "episode_id"),
        Index("ix_mu_outputs_mood", "mood"),
    )


# ---------------------------------------------------------------------------
# SoundEffectAsset  (pre-seeded SFX library)
# ---------------------------------------------------------------------------

class SoundEffectAsset(Base):
    """
    Preset sound-effect library entries.

    Seeded at migration time with a default SFX set suitable for
    family-comedy content: footsteps, doors, notification sounds, etc.
    Browse and select via SFXLibraryService.
    """

    __tablename__ = "mu_sfx_assets"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    # e.g. "footsteps_wood", "door_creak", "notification_chime"
    sfx_key: Mapped[str] = mapped_column(String(200), nullable=False, unique=True)
    name: Mapped[str] = mapped_column(String(500), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False, default="")

    # Category: "ambience" | "foley" | "notification" | "transition" | "comedy"
    category: Mapped[str] = mapped_column(String(100), nullable=False, default="foley")
    # Tags for search: ["indoor", "footstep", "loop"]
    tags: Mapped[list] = mapped_column(JSON, nullable=False, default=list)

    # Where the real file lives (empty for mock/built-in)
    storage_key: Mapped[str] = mapped_column(String(1024), nullable=False, default="")
    duration_seconds: Mapped[float] = mapped_column(Float, nullable=False, default=1.0)
    format: Mapped[str] = mapped_column(String(20), nullable=False, default="wav")
    sample_rate: Mapped[int] = mapped_column(Integer, nullable=False, default=44100)

    is_builtin: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )

    __table_args__ = (
        Index("ix_mu_sfx_assets_category", "category"),
        Index("ix_mu_sfx_assets_active", "is_active"),
    )


# ---------------------------------------------------------------------------
# MusicRetryQueue
# ---------------------------------------------------------------------------

class MusicRetryQueue(Base):
    """Tracks failed music generation jobs pending retry."""

    __tablename__ = "mu_retry_queue"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    project_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    scene_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), nullable=True)
    episode_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), nullable=True)
    original_job_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), nullable=True)

    # "pending" | "retrying" | "resolved" | "exhausted"
    status: Mapped[str] = mapped_column(String(50), nullable=False, default="pending")
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
        Index("ix_mu_retry_queue_project_id", "project_id"),
        Index("ix_mu_retry_queue_status", "status"),
        Index("ix_mu_retry_queue_project_status", "project_id", "status"),
    )

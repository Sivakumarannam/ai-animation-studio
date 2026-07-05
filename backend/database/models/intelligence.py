"""
Phase 3 — Story Intelligence Engine database models.

All tables are prefixed with `si_` (Story Intelligence) to avoid collisions
with the existing Phase 1/2 tables.

Hierarchy:
  Project
    └─ World (si_worlds)
         ├─ Season (si_seasons)
         │    └─ Episode (si_episodes)
         │         └─ StoryScene (si_story_scenes)
         ├─ StoryIdea (si_story_ideas)
         └─ StoryMemory (si_story_memory)

Cross-cutting:
  GenerationJob  → GenerationLog (per step)
  GenerationJob  → RetryQueue
  StoryEvaluation → Episode
  StoryVersion    → any entity (polymorphic by entity_type + entity_id)
"""
from __future__ import annotations

import uuid
from datetime import datetime, timezone
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
# World
# ---------------------------------------------------------------------------

class World(UUIDMixin, TimestampMixin, Base):
    """
    A self-contained fiction universe that one or more seasons live in.
    Characters, episodes, and scenes reference the world for consistency.
    """
    __tablename__ = "si_worlds"

    project_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("projects.id", ondelete="CASCADE"),
        nullable=False, index=True
    )
    name: Mapped[str] = mapped_column(String(500), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False, default="")
    rules: Mapped[list[Any]] = mapped_column(JSON, nullable=False, default=list)
    locations: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False, default=dict)
    timeline_data: Mapped[list[Any]] = mapped_column(JSON, nullable=False, default=list)
    factions: Mapped[list[Any]] = mapped_column(JSON, nullable=False, default=list)
    objects: Mapped[list[Any]] = mapped_column(JSON, nullable=False, default=list)
    lore: Mapped[str] = mapped_column(Text, nullable=False, default="")
    status: Mapped[str] = mapped_column(String(50), nullable=False, default="active", index=True)

    seasons: Mapped[list["Season"]] = relationship(
        "Season", back_populates="world", lazy="select",
        order_by="Season.season_number"
    )
    story_ideas: Mapped[list["StoryIdea"]] = relationship(
        "StoryIdea", back_populates="world", lazy="select"
    )
    memories: Mapped[list["StoryMemory"]] = relationship(
        "StoryMemory", back_populates="world", lazy="select"
    )


# ---------------------------------------------------------------------------
# Season
# ---------------------------------------------------------------------------

class Season(UUIDMixin, TimestampMixin, Base):
    __tablename__ = "si_seasons"
    __table_args__ = (
        UniqueConstraint("world_id", "season_number", name="uq_season_world_number"),
    )

    world_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("si_worlds.id", ondelete="CASCADE"),
        nullable=False, index=True
    )
    project_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("projects.id", ondelete="CASCADE"),
        nullable=False, index=True
    )
    season_number: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False, default="")
    story_arc: Mapped[str] = mapped_column(Text, nullable=False, default="")
    status: Mapped[str] = mapped_column(String(50), nullable=False, default="draft", index=True)
    episode_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    world: Mapped["World"] = relationship("World", back_populates="seasons")
    episodes: Mapped[list["Episode"]] = relationship(
        "Episode", back_populates="season", lazy="select",
        order_by="Episode.episode_number"
    )


# ---------------------------------------------------------------------------
# Episode
# ---------------------------------------------------------------------------

class Episode(UUIDMixin, TimestampMixin, Base):
    __tablename__ = "si_episodes"
    __table_args__ = (
        UniqueConstraint("season_id", "episode_number", name="uq_episode_season_number"),
    )

    season_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("si_seasons.id", ondelete="CASCADE"),
        nullable=False, index=True
    )
    world_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("si_worlds.id", ondelete="CASCADE"),
        nullable=False, index=True
    )
    project_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("projects.id", ondelete="CASCADE"),
        nullable=False, index=True
    )
    episode_number: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    summary: Mapped[str] = mapped_column(Text, nullable=False, default="")
    opening: Mapped[str] = mapped_column(Text, nullable=False, default="")
    middle: Mapped[str] = mapped_column(Text, nullable=False, default="")
    ending: Mapped[str] = mapped_column(Text, nullable=False, default="")
    moral: Mapped[str] = mapped_column(Text, nullable=False, default="")
    duration_target_seconds: Mapped[int] = mapped_column(Integer, nullable=False, default=300)
    story_score: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    status: Mapped[str] = mapped_column(String(50), nullable=False, default="draft", index=True)
    generation_metadata: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False, default=dict)

    season: Mapped["Season"] = relationship("Season", back_populates="episodes")
    story_scenes: Mapped[list["StoryScene"]] = relationship(
        "StoryScene", back_populates="episode", lazy="select",
        order_by="StoryScene.scene_number"
    )
    evaluations: Mapped[list["StoryEvaluation"]] = relationship(
        "StoryEvaluation", back_populates="episode", lazy="select"
    )


# ---------------------------------------------------------------------------
# StoryScene (Phase 3 AI scene — separate from animation scenes)
# ---------------------------------------------------------------------------

class StoryScene(UUIDMixin, TimestampMixin, Base):
    """
    A story beat inside an Episode. Do NOT confuse with the Phase 1 `Scene`
    model (animation timeline scene). This is the AI story planning scene.
    """
    __tablename__ = "si_story_scenes"

    episode_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("si_episodes.id", ondelete="CASCADE"),
        nullable=False, index=True
    )
    scene_number: Mapped[int] = mapped_column(Integer, nullable=False)
    scene_goal: Mapped[str] = mapped_column(Text, nullable=False, default="")
    location: Mapped[str] = mapped_column(String(500), nullable=False, default="")
    character_names: Mapped[list[str]] = mapped_column(JSON, nullable=False, default=list)
    dialogue: Mapped[list[Any]] = mapped_column(JSON, nullable=False, default=list)
    narration: Mapped[str] = mapped_column(Text, nullable=False, default="")
    image_prompt: Mapped[str] = mapped_column(Text, nullable=False, default="")
    animation_prompt: Mapped[str] = mapped_column(Text, nullable=False, default="")
    camera_direction: Mapped[str] = mapped_column(Text, nullable=False, default="")
    duration_seconds: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    status: Mapped[str] = mapped_column(String(50), nullable=False, default="draft")

    episode: Mapped["Episode"] = relationship("Episode", back_populates="story_scenes")


# ---------------------------------------------------------------------------
# StoryIdea
# ---------------------------------------------------------------------------

class StoryIdea(UUIDMixin, TimestampMixin, Base):
    """A generated story concept before full planning begins."""
    __tablename__ = "si_story_ideas"

    project_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("projects.id", ondelete="CASCADE"),
        nullable=False, index=True
    )
    world_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("si_worlds.id", ondelete="SET NULL"),
        nullable=True, index=True
    )
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    premise: Mapped[str] = mapped_column(Text, nullable=False, default="")
    genre: Mapped[str] = mapped_column(String(100), nullable=False, default="comedy")
    tone: Mapped[str] = mapped_column(String(100), nullable=False, default="light")
    story_type: Mapped[str] = mapped_column(String(100), nullable=False, default="comedy")
    target_audience: Mapped[str] = mapped_column(String(200), nullable=False, default="general")
    estimated_episodes: Mapped[int] = mapped_column(Integer, nullable=False, default=10)
    status: Mapped[str] = mapped_column(String(50), nullable=False, default="idea", index=True)
    metadata_: Mapped[dict[str, Any]] = mapped_column("idea_metadata", JSON, nullable=False, default=dict)

    world: Mapped["World | None"] = relationship("World", back_populates="story_ideas")

    __table_args__ = (
        Index("ix_si_story_ideas_project_status", "project_id", "status"),
    )


# ---------------------------------------------------------------------------
# StoryMemory
# ---------------------------------------------------------------------------

class StoryMemory(UUIDMixin, TimestampMixin, Base):
    """
    Persistent memory for the Story Intelligence Engine.
    Queryable by world + memory_type + key.
    Includes a JSON placeholder for Phase 4 RAG embedding vectors.
    """
    __tablename__ = "si_story_memory"

    world_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("si_worlds.id", ondelete="CASCADE"),
        nullable=False, index=True
    )
    memory_type: Mapped[str] = mapped_column(
        String(100), nullable=False, index=True
        # "character" | "location" | "event" | "relationship" | "joke" | "lesson" | "object"
    )
    key: Mapped[str] = mapped_column(String(500), nullable=False)
    value: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False, default=dict)
    episode_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), nullable=True  # episode where this memory was established
    )
    embedding_vector: Mapped[list[float]] = mapped_column(
        JSON, nullable=False, default=list  # Phase 4 placeholder — store embedding here
    )
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)

    world: Mapped["World"] = relationship("World", back_populates="memories")

    __table_args__ = (
        Index("ix_si_story_memory_world_type", "world_id", "memory_type"),
        Index("ix_si_story_memory_world_key", "world_id", "key"),
    )


# ---------------------------------------------------------------------------
# StoryEvaluation
# ---------------------------------------------------------------------------

class StoryEvaluation(UUIDMixin, TimestampMixin, Base):
    """Quality scores (0–100) for a generated episode, produced by StoryEvaluator."""
    __tablename__ = "si_story_evaluations"

    episode_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("si_episodes.id", ondelete="CASCADE"),
        nullable=False, index=True
    )
    evaluator_version: Mapped[str] = mapped_column(String(20), nullable=False, default="1.0")
    originality_score: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    consistency_score: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    creativity_score: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    grammar_score: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    flow_score: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    entertainment_score: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    educational_value_score: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    story_arc_score: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    dialogue_score: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    overall_score: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    feedback: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False, default=dict)
    approved: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    evaluated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc)
    )

    episode: Mapped["Episode"] = relationship("Episode", back_populates="evaluations")


# ---------------------------------------------------------------------------
# GenerationJob
# ---------------------------------------------------------------------------

class GenerationJob(UUIDMixin, TimestampMixin, Base):
    """
    Tracks one async generation request (story, episode, scene, evaluation, retry).
    The dispatcher updates progress_percent + current_step as work proceeds.
    """
    __tablename__ = "si_generation_jobs"

    project_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("projects.id", ondelete="SET NULL"),
        nullable=True, index=True
    )
    job_type: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    # "generate_world" | "generate_idea" | "generate_season" | "generate_episode"
    # | "generate_scene" | "evaluate_episode" | "retry_episode" | "save_memory"

    entity_type: Mapped[str] = mapped_column(String(100), nullable=False, default="")
    entity_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), nullable=True)

    status: Mapped[str] = mapped_column(
        String(50), nullable=False, default="pending", index=True
        # "pending" | "running" | "completed" | "failed" | "retrying" | "cancelled"
    )
    celery_task_id: Mapped[str] = mapped_column(String(255), nullable=False, default="")
    execution_mode: Mapped[str] = mapped_column(String(20), nullable=False, default="sync")
    # "async" (Celery) | "sync" (fallback)

    progress_percent: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    current_step: Mapped[str] = mapped_column(String(200), nullable=False, default="")
    result: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False, default=dict)
    error_message: Mapped[str] = mapped_column(Text, nullable=False, default="")
    retry_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    max_retries: Mapped[int] = mapped_column(Integer, nullable=False, default=3)

    scheduled_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    logs: Mapped[list["GenerationLog"]] = relationship(
        "GenerationLog", back_populates="job", lazy="select",
        order_by="GenerationLog.created_at"
    )
    retry_entries: Mapped[list["RetryQueue"]] = relationship(
        "RetryQueue", back_populates="job", lazy="select"
    )

    __table_args__ = (
        Index("ix_si_gen_jobs_project_status", "project_id", "status"),
    )


# ---------------------------------------------------------------------------
# GenerationLog
# ---------------------------------------------------------------------------

class GenerationLog(UUIDMixin, TimestampMixin, Base):
    """One log entry per AI generation step within a GenerationJob."""
    __tablename__ = "si_generation_logs"

    job_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("si_generation_jobs.id", ondelete="CASCADE"),
        nullable=False, index=True
    )
    step_name: Mapped[str] = mapped_column(String(200), nullable=False)
    prompt: Mapped[str] = mapped_column(Text, nullable=False, default="")
    response: Mapped[str] = mapped_column(Text, nullable=False, default="")
    duration_ms: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    tokens_used: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    model_name: Mapped[str] = mapped_column(String(200), nullable=False, default="")
    score: Mapped[float | None] = mapped_column(Float, nullable=True)
    retry_number: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    is_error: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    error_message: Mapped[str] = mapped_column(Text, nullable=False, default="")

    job: Mapped["GenerationJob"] = relationship("GenerationJob", back_populates="logs")


# ---------------------------------------------------------------------------
# RetryQueue
# ---------------------------------------------------------------------------

class RetryQueue(UUIDMixin, TimestampMixin, Base):
    """Pending retry entries for failed GenerationJobs."""
    __tablename__ = "si_retry_queue"

    job_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("si_generation_jobs.id", ondelete="CASCADE"),
        nullable=False, index=True
    )
    scheduled_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False,
        default=lambda: datetime.now(timezone.utc)
    )
    attempt_number: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    reason: Mapped[str] = mapped_column(Text, nullable=False, default="")
    status: Mapped[str] = mapped_column(
        String(50), nullable=False, default="pending", index=True
        # "pending" | "processing" | "done" | "abandoned"
    )

    job: Mapped["GenerationJob"] = relationship("GenerationJob", back_populates="retry_entries")


# ---------------------------------------------------------------------------
# StoryVersion (polymorphic snapshot store)
# ---------------------------------------------------------------------------

class StoryVersion(UUIDMixin, TimestampMixin, Base):
    """
    Full JSON snapshot of any SI entity at a point in time.
    entity_type: "world" | "season" | "episode" | "story_scene"
    entity_id: UUID of the snapshotted entity
    """
    __tablename__ = "si_story_versions"

    entity_type: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    entity_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False, index=True)
    version_number: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    snapshot: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False, default=dict)
    change_summary: Mapped[str] = mapped_column(Text, nullable=False, default="")
    created_by: Mapped[str] = mapped_column(String(100), nullable=False, default="system")

    __table_args__ = (
        Index("ix_si_story_versions_entity", "entity_type", "entity_id"),
    )

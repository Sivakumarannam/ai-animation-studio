"""
Phase 6 — AI Asset Generation Engine database models.

All tables are prefixed with `ag_` (Asset Generation) to avoid collisions
with Phase 1–5 tables.

Hierarchy:
  AssetProject      (ag_projects)           — per-project asset config
  AssetStyle        (ag_styles)             — art style definitions
  AssetCollection   (ag_collections)        — named asset groups
  Asset             (ag_assets)             — individual asset entity
  AssetVersion      (ag_versions)           — versioned renders of an asset
  AssetPrompt       (ag_prompts)            — generated prompts
  PromptTemplate    (ag_prompt_templates)   — reusable prompt templates
  PromptHistory     (ag_prompt_history)     — prompt execution log
  NegativePrompt    (ag_negative_prompts)   — negative prompt library
  GeneratedImage    (ag_generated_images)   — raw image records from provider
  AssetEvaluation   (ag_evaluations)        — quality evaluation per image
  AssetTag          (ag_tags)               — tag definitions
  AssetEmbedding    (ag_embeddings)         — semantic embedding vectors
  AssetMemory       (ag_memory)             — generation memory / learning
  SceneComposition  (ag_compositions)       — scene composition plans
  CameraShot        (ag_camera_shots)       — planned camera shots
  LightingPreset    (ag_lighting_presets)   — reusable lighting configs
  PosePreset        (ag_pose_presets)       — character pose library
  ExpressionPreset  (ag_expression_presets) — character expression library
  RetryQueue        (ag_retry_queue)        — assets queued for retry
  GenerationJob     (ag_generation_jobs)    — async job tracking
  GenerationHistory (ag_generation_history) — job run history
  AssetCache        (ag_cache)              — asset dedup / cache entries
  AssetRelationship (ag_relationships)      — asset-to-asset links
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
# AssetProject
# ---------------------------------------------------------------------------

class AssetProject(UUIDMixin, TimestampMixin, Base):
    """Asset generation configuration bound to a project."""
    __tablename__ = "ag_projects"

    project_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("projects.id", ondelete="CASCADE"),
        nullable=False, unique=True, index=True,
    )
    name: Mapped[str] = mapped_column(String(500), nullable=False, default="")
    description: Mapped[str] = mapped_column(Text, nullable=False, default="")
    # overall art style slug / foreign key
    default_style_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("ag_styles.id", ondelete="SET NULL"),
        nullable=True,
    )
    # generation settings
    quality_threshold: Mapped[float] = mapped_column(Float, nullable=False, default=90.0)
    max_retries: Mapped[int] = mapped_column(Integer, nullable=False, default=3)
    target_resolution: Mapped[str] = mapped_column(String(50), nullable=False, default="1024x1024")
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True, index=True)
    total_assets_generated: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    total_retries: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    avg_quality_score: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    storage_bytes_used: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    config: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False, default=dict)
    metadata_: Mapped[dict[str, Any]] = mapped_column("ag_project_meta", JSON, nullable=False, default=dict)


# ---------------------------------------------------------------------------
# AssetStyle
# ---------------------------------------------------------------------------

class AssetStyle(UUIDMixin, TimestampMixin, Base):
    """Art style definition — shared across projects."""
    __tablename__ = "ag_styles"

    name: Mapped[str] = mapped_column(String(200), nullable=False, index=True)
    slug: Mapped[str] = mapped_column(String(200), nullable=False, unique=True, index=True)
    description: Mapped[str] = mapped_column(Text, nullable=False, default="")
    # positive style prompt fragment
    style_prompt: Mapped[str] = mapped_column(Text, nullable=False, default="")
    # negative style prompt fragment
    negative_prompt: Mapped[str] = mapped_column(Text, nullable=False, default="")
    # comma-separated keywords
    keywords: Mapped[list[str]] = mapped_column(JSON, nullable=False, default=list)
    color_palette: Mapped[list[str]] = mapped_column(JSON, nullable=False, default=list)
    reference_artists: Mapped[list[str]] = mapped_column(JSON, nullable=False, default=list)
    # "2d_cartoon" | "3d_animation" | "anime" | "realistic" | "pixel_art" | "watercolor"
    style_type: Mapped[str] = mapped_column(String(100), nullable=False, default="2d_cartoon", index=True)
    is_default: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False, index=True)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    usage_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    avg_quality_score: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    extra: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False, default=dict)


# ---------------------------------------------------------------------------
# AssetCollection
# ---------------------------------------------------------------------------

class AssetCollection(UUIDMixin, TimestampMixin, Base):
    """Named group of related assets (e.g., "Season 1 backgrounds")."""
    __tablename__ = "ag_collections"

    project_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("projects.id", ondelete="CASCADE"),
        nullable=False, index=True,
    )
    name: Mapped[str] = mapped_column(String(500), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False, default="")
    # "character" | "background" | "prop" | "mixed" | "thumbnail" | "icon"
    collection_type: Mapped[str] = mapped_column(String(100), nullable=False, default="mixed", index=True)
    asset_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    cover_asset_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), nullable=True,
    )
    tags: Mapped[list[str]] = mapped_column(JSON, nullable=False, default=list)
    metadata_: Mapped[dict[str, Any]] = mapped_column("ag_collection_meta", JSON, nullable=False, default=dict)

    __table_args__ = (
        Index("ix_ag_collections_project_type", "project_id", "collection_type"),
    )


# ---------------------------------------------------------------------------
# Asset
# ---------------------------------------------------------------------------

class GeneratedAsset(UUIDMixin, TimestampMixin, Base):
    """A single production asset (character, background, prop, icon, etc.)."""
    __tablename__ = "ag_assets"

    project_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("projects.id", ondelete="CASCADE"),
        nullable=False, index=True,
    )
    collection_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("ag_collections.id", ondelete="SET NULL"),
        nullable=True, index=True,
    )
    style_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("ag_styles.id", ondelete="SET NULL"),
        nullable=True,
    )
    # links to Phase 2 characters
    character_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), nullable=True, index=True,
    )
    # links to Phase 3 scenes
    episode_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), nullable=True, index=True,
    )
    scene_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), nullable=True, index=True,
    )

    name: Mapped[str] = mapped_column(String(500), nullable=False, index=True)
    description: Mapped[str] = mapped_column(Text, nullable=False, default="")
    # "character" | "character_variant" | "character_expression" | "character_pose"
    # "character_turnaround" | "background" | "environment_variant" | "prop"
    # "vehicle" | "weapon" | "building" | "nature" | "icon" | "logo"
    # "scene_layout" | "thumbnail" | "reference"
    asset_type: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    # "pending" | "planning" | "generating" | "evaluating" | "retrying"
    # "completed" | "failed" | "rejected"
    status: Mapped[str] = mapped_column(String(50), nullable=False, default="pending", index=True)
    current_version_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), nullable=True,
    )
    best_version_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), nullable=True,
    )
    version_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    retry_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    max_retries: Mapped[int] = mapped_column(Integer, nullable=False, default=3)
    quality_score: Mapped[float] = mapped_column(Float, nullable=False, default=0.0, index=True)
    quality_threshold: Mapped[float] = mapped_column(Float, nullable=False, default=90.0)
    # MinIO object key for the best/latest image
    storage_key: Mapped[str] = mapped_column(String(2000), nullable=False, default="")
    storage_bucket: Mapped[str] = mapped_column(String(500), nullable=False, default="assets")
    width: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    height: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    file_size_bytes: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    mime_type: Mapped[str] = mapped_column(String(100), nullable=False, default="image/png")
    tags: Mapped[list[str]] = mapped_column(JSON, nullable=False, default=list)
    # character consistency fingerprint
    consistency_fingerprint: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False, default=dict)
    generation_params: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False, default=dict)
    metadata_: Mapped[dict[str, Any]] = mapped_column("ag_asset_meta", JSON, nullable=False, default=dict)
    generated_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    is_deleted: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False, index=True)

    __table_args__ = (
        Index("ix_ag_assets_project_type_status", "project_id", "asset_type", "status"),
        Index("ix_ag_assets_character_type", "character_id", "asset_type"),
        Index("ix_ag_assets_episode", "episode_id", "asset_type"),
    )


# ---------------------------------------------------------------------------
# AssetVersion
# ---------------------------------------------------------------------------

class GeneratedAssetVersion(UUIDMixin, TimestampMixin, Base):
    """A single rendered version of an asset (original, revision 1, 2, …)."""
    __tablename__ = "ag_versions"

    asset_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("ag_assets.id", ondelete="CASCADE"),
        nullable=False, index=True,
    )
    prompt_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("ag_prompts.id", ondelete="SET NULL"),
        nullable=True,
    )
    version_number: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    # "original" | "revision" | "best" | "latest"
    version_label: Mapped[str] = mapped_column(String(50), nullable=False, default="original")
    storage_key: Mapped[str] = mapped_column(String(2000), nullable=False, default="")
    storage_bucket: Mapped[str] = mapped_column(String(500), nullable=False, default="assets")
    width: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    height: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    file_size_bytes: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    quality_score: Mapped[float] = mapped_column(Float, nullable=False, default=0.0, index=True)
    is_approved: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False, index=True)
    is_rejected: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    rejection_reason: Mapped[str] = mapped_column(Text, nullable=False, default="")
    generation_seed: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    generation_steps: Mapped[int] = mapped_column(Integer, nullable=False, default=20)
    cfg_scale: Mapped[float] = mapped_column(Float, nullable=False, default=7.0)
    sampler: Mapped[str] = mapped_column(String(100), nullable=False, default="euler_a")
    generation_params: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False, default=dict)
    evaluation_scores: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False, default=dict)
    metadata_: Mapped[dict[str, Any]] = mapped_column("ag_version_meta", JSON, nullable=False, default=dict)

    __table_args__ = (
        Index("ix_ag_versions_asset_number", "asset_id", "version_number"),
        UniqueConstraint("asset_id", "version_number", name="uq_ag_versions_asset_version"),
    )


# ---------------------------------------------------------------------------
# AssetPrompt
# ---------------------------------------------------------------------------

class AssetPrompt(UUIDMixin, TimestampMixin, Base):
    """Fully assembled prompt for a generation request."""
    __tablename__ = "ag_prompts"

    asset_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("ag_assets.id", ondelete="SET NULL"),
        nullable=True, index=True,
    )
    template_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("ag_prompt_templates.id", ondelete="SET NULL"),
        nullable=True,
    )
    positive_prompt: Mapped[str] = mapped_column(Text, nullable=False, default="")
    negative_prompt: Mapped[str] = mapped_column(Text, nullable=False, default="")
    style_prompt: Mapped[str] = mapped_column(Text, nullable=False, default="")
    camera_prompt: Mapped[str] = mapped_column(Text, nullable=False, default="")
    composition_prompt: Mapped[str] = mapped_column(Text, nullable=False, default="")
    lighting_prompt: Mapped[str] = mapped_column(Text, nullable=False, default="")
    color_prompt: Mapped[str] = mapped_column(Text, nullable=False, default="")
    consistency_prompt: Mapped[str] = mapped_column(Text, nullable=False, default="")
    # assembled full prompt sent to the provider
    full_prompt: Mapped[str] = mapped_column(Text, nullable=False, default="")
    full_negative_prompt: Mapped[str] = mapped_column(Text, nullable=False, default="")
    # "character" | "background" | "prop" | "scene" | "thumbnail"
    prompt_type: Mapped[str] = mapped_column(String(100), nullable=False, default="character", index=True)
    quality_score: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    was_successful: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False, index=True)
    use_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    generation_params: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False, default=dict)
    metadata_: Mapped[dict[str, Any]] = mapped_column("ag_prompt_meta", JSON, nullable=False, default=dict)


# ---------------------------------------------------------------------------
# PromptTemplate
# ---------------------------------------------------------------------------

class PromptTemplate(UUIDMixin, TimestampMixin, Base):
    """Reusable prompt template for a given asset type."""
    __tablename__ = "ag_prompt_templates"

    name: Mapped[str] = mapped_column(String(500), nullable=False, index=True)
    # "character" | "background" | "prop" | "scene" | "thumbnail"
    asset_type: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    style_type: Mapped[str] = mapped_column(String(100), nullable=False, default="2d_cartoon")
    positive_template: Mapped[str] = mapped_column(Text, nullable=False, default="")
    negative_template: Mapped[str] = mapped_column(Text, nullable=False, default="")
    style_template: Mapped[str] = mapped_column(Text, nullable=False, default="")
    camera_template: Mapped[str] = mapped_column(Text, nullable=False, default="")
    lighting_template: Mapped[str] = mapped_column(Text, nullable=False, default="")
    variables: Mapped[list[str]] = mapped_column(JSON, nullable=False, default=list)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    is_default: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    use_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    avg_quality_score: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    extra: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False, default=dict)

    __table_args__ = (
        Index("ix_ag_prompt_templates_type_style", "asset_type", "style_type"),
    )


# ---------------------------------------------------------------------------
# PromptHistory
# ---------------------------------------------------------------------------

class PromptHistory(UUIDMixin, TimestampMixin, Base):
    """Log of every prompt execution and its outcome."""
    __tablename__ = "ag_prompt_history"

    prompt_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("ag_prompts.id", ondelete="SET NULL"),
        nullable=True, index=True,
    )
    asset_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("ag_assets.id", ondelete="SET NULL"),
        nullable=True, index=True,
    )
    full_prompt: Mapped[str] = mapped_column(Text, nullable=False, default="")
    full_negative_prompt: Mapped[str] = mapped_column(Text, nullable=False, default="")
    quality_score: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    was_accepted: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    rejection_reasons: Mapped[list[str]] = mapped_column(JSON, nullable=False, default=list)
    generation_params: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False, default=dict)
    executed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


# ---------------------------------------------------------------------------
# NegativePrompt
# ---------------------------------------------------------------------------

class NegativePrompt(UUIDMixin, TimestampMixin, Base):
    """Reusable negative prompt fragment library."""
    __tablename__ = "ag_negative_prompts"

    name: Mapped[str] = mapped_column(String(200), nullable=False, index=True)
    content: Mapped[str] = mapped_column(Text, nullable=False, default="")
    # "universal" | "character" | "background" | "prop" | "face" | "hands"
    category: Mapped[str] = mapped_column(String(100), nullable=False, default="universal", index=True)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    priority: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    use_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)


# ---------------------------------------------------------------------------
# GeneratedImage
# ---------------------------------------------------------------------------

class GeneratedImage(UUIDMixin, TimestampMixin, Base):
    """Raw image record returned by the image generation provider."""
    __tablename__ = "ag_generated_images"

    asset_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("ag_assets.id", ondelete="SET NULL"),
        nullable=True, index=True,
    )
    version_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("ag_versions.id", ondelete="SET NULL"),
        nullable=True, index=True,
    )
    prompt_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("ag_prompts.id", ondelete="SET NULL"),
        nullable=True,
    )
    storage_key: Mapped[str] = mapped_column(String(2000), nullable=False, default="")
    storage_bucket: Mapped[str] = mapped_column(String(500), nullable=False, default="assets")
    width: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    height: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    file_size_bytes: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    mime_type: Mapped[str] = mapped_column(String(100), nullable=False, default="image/png")
    # "pending" | "accepted" | "rejected" | "superseded"
    status: Mapped[str] = mapped_column(String(50), nullable=False, default="pending", index=True)
    generation_time_ms: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    provider: Mapped[str] = mapped_column(String(100), nullable=False, default="mock")
    provider_job_id: Mapped[str] = mapped_column(String(500), nullable=False, default="")
    generation_params: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False, default=dict)
    raw_metadata: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False, default=dict)


# ---------------------------------------------------------------------------
# AssetEvaluation
# ---------------------------------------------------------------------------

class AssetEvaluation(UUIDMixin, TimestampMixin, Base):
    """Quality evaluation result for a generated image."""
    __tablename__ = "ag_evaluations"

    asset_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("ag_assets.id", ondelete="CASCADE"),
        nullable=False, index=True,
    )
    version_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("ag_versions.id", ondelete="SET NULL"),
        nullable=True, index=True,
    )
    image_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("ag_generated_images.id", ondelete="SET NULL"),
        nullable=True,
    )
    overall_score: Mapped[float] = mapped_column(Float, nullable=False, default=0.0, index=True)
    # dimension scores (0-100 each)
    prompt_quality: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    image_quality: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    character_consistency: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    background_consistency: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    composition_score: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    lighting_score: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    style_match: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    scene_match: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    resolution_score: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    artifact_score: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    hands_score: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    face_score: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    text_error_score: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    passed_threshold: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False, index=True)
    failure_reasons: Mapped[list[str]] = mapped_column(JSON, nullable=False, default=list)
    notes: Mapped[str] = mapped_column(Text, nullable=False, default="")
    evaluated_by: Mapped[str] = mapped_column(String(100), nullable=False, default="mock")
    raw_scores: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False, default=dict)


# ---------------------------------------------------------------------------
# AssetTag
# ---------------------------------------------------------------------------

class AssetTag(UUIDMixin, TimestampMixin, Base):
    """Tag definition for asset categorization."""
    __tablename__ = "ag_tags"

    name: Mapped[str] = mapped_column(String(200), nullable=False, unique=True, index=True)
    slug: Mapped[str] = mapped_column(String(200), nullable=False, unique=True, index=True)
    # "type" | "mood" | "setting" | "character" | "style" | "color"
    category: Mapped[str] = mapped_column(String(100), nullable=False, default="type")
    usage_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    color: Mapped[str] = mapped_column(String(20), nullable=False, default="#6366f1")
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)


# ---------------------------------------------------------------------------
# AssetEmbedding
# ---------------------------------------------------------------------------

class AssetEmbedding(UUIDMixin, TimestampMixin, Base):
    """Semantic embedding vector for an asset (for similarity search)."""
    __tablename__ = "ag_embeddings"

    asset_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("ag_assets.id", ondelete="CASCADE"),
        nullable=False, unique=True, index=True,
    )
    # embedding stored as JSON float list
    vector: Mapped[list[float]] = mapped_column(JSON, nullable=False, default=list)
    vector_dim: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    # text that was embedded (prompt summary)
    source_text: Mapped[str] = mapped_column(Text, nullable=False, default="")
    embedding_model: Mapped[str] = mapped_column(String(200), nullable=False, default="mock")
    embedded_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    metadata_: Mapped[dict[str, Any]] = mapped_column("ag_embedding_meta", JSON, nullable=False, default=dict)


# ---------------------------------------------------------------------------
# AssetMemory
# ---------------------------------------------------------------------------

class AssetMemory(UUIDMixin, TimestampMixin, Base):
    """Persistent generation memory — learns from successes and failures."""
    __tablename__ = "ag_memory"

    project_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("projects.id", ondelete="CASCADE"),
        nullable=False, index=True,
    )
    # "best_prompt" | "rejected_prompt" | "successful_style" | "failed_style"
    # "preferred_lighting" | "preferred_composition" | "successful_camera"
    memory_type: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    # "character" | "background" | "prop" | "global"
    scope: Mapped[str] = mapped_column(String(100), nullable=False, default="global")
    key: Mapped[str] = mapped_column(String(500), nullable=False, index=True)
    value: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False, default=dict)
    confidence: Mapped[float] = mapped_column(Float, nullable=False, default=1.0)
    use_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    last_used_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    __table_args__ = (
        Index("ix_ag_memory_project_type_scope", "project_id", "memory_type", "scope"),
    )


# ---------------------------------------------------------------------------
# SceneComposition
# ---------------------------------------------------------------------------

class AgSceneComposition(UUIDMixin, TimestampMixin, Base):
    """Composition plan for a scene — guides asset placement and framing."""
    __tablename__ = "ag_compositions"

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
    name: Mapped[str] = mapped_column(String(500), nullable=False, default="")
    description: Mapped[str] = mapped_column(Text, nullable=False, default="")
    # "rule_of_thirds" | "centered" | "leading_lines" | "frame_in_frame"
    composition_type: Mapped[str] = mapped_column(String(100), nullable=False, default="rule_of_thirds")
    foreground_elements: Mapped[list[str]] = mapped_column(JSON, nullable=False, default=list)
    midground_elements: Mapped[list[str]] = mapped_column(JSON, nullable=False, default=list)
    background_elements: Mapped[list[str]] = mapped_column(JSON, nullable=False, default=list)
    focus_point: Mapped[str] = mapped_column(String(200), nullable=False, default="")
    lighting_direction: Mapped[str] = mapped_column(String(100), nullable=False, default="natural")
    color_harmony: Mapped[str] = mapped_column(String(100), nullable=False, default="complementary")
    negative_space: Mapped[float] = mapped_column(Float, nullable=False, default=0.3)
    composition_prompt: Mapped[str] = mapped_column(Text, nullable=False, default="")
    layout_data: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False, default=dict)


# ---------------------------------------------------------------------------
# CameraShot
# ---------------------------------------------------------------------------

class CameraShot(UUIDMixin, TimestampMixin, Base):
    """Planned camera shot for a scene."""
    __tablename__ = "ag_camera_shots"

    composition_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("ag_compositions.id", ondelete="SET NULL"),
        nullable=True, index=True,
    )
    scene_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), nullable=True, index=True,
    )
    episode_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), nullable=True, index=True,
    )
    # "wide" | "medium" | "close_up" | "extreme_close_up" | "over_shoulder"
    # "tracking" | "top_view" | "side_view" | "low_angle" | "high_angle"
    shot_type: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    shot_order: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    description: Mapped[str] = mapped_column(Text, nullable=False, default="")
    camera_movement: Mapped[str] = mapped_column(String(200), nullable=False, default="static")
    focal_length: Mapped[str] = mapped_column(String(50), nullable=False, default="50mm")
    depth_of_field: Mapped[str] = mapped_column(String(100), nullable=False, default="normal")
    camera_prompt: Mapped[str] = mapped_column(Text, nullable=False, default="")
    asset_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("ag_assets.id", ondelete="SET NULL"),
        nullable=True,
    )
    quality_score: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    shot_data: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False, default=dict)


# ---------------------------------------------------------------------------
# LightingPreset
# ---------------------------------------------------------------------------

class LightingPreset(UUIDMixin, TimestampMixin, Base):
    """Reusable lighting configuration."""
    __tablename__ = "ag_lighting_presets"

    name: Mapped[str] = mapped_column(String(200), nullable=False, index=True)
    slug: Mapped[str] = mapped_column(String(200), nullable=False, unique=True, index=True)
    description: Mapped[str] = mapped_column(Text, nullable=False, default="")
    # "natural_day" | "natural_night" | "golden_hour" | "studio" | "dramatic"
    # "soft_box" | "backlit" | "rim_lit" | "ambient"
    lighting_type: Mapped[str] = mapped_column(String(100), nullable=False, default="natural_day", index=True)
    lighting_prompt: Mapped[str] = mapped_column(Text, nullable=False, default="")
    time_of_day: Mapped[str] = mapped_column(String(50), nullable=False, default="day")
    weather: Mapped[str] = mapped_column(String(50), nullable=False, default="clear")
    intensity: Mapped[float] = mapped_column(Float, nullable=False, default=0.8)
    color_temperature: Mapped[str] = mapped_column(String(50), nullable=False, default="neutral")
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    use_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    avg_quality_score: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    preset_data: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False, default=dict)


# ---------------------------------------------------------------------------
# PosePreset
# ---------------------------------------------------------------------------

class PosePreset(UUIDMixin, TimestampMixin, Base):
    """Character pose library."""
    __tablename__ = "ag_pose_presets"

    name: Mapped[str] = mapped_column(String(200), nullable=False, index=True)
    slug: Mapped[str] = mapped_column(String(200), nullable=False, unique=True, index=True)
    description: Mapped[str] = mapped_column(Text, nullable=False, default="")
    # "standing" | "sitting" | "walking" | "running" | "fighting" | "idle" | "action"
    pose_type: Mapped[str] = mapped_column(String(100), nullable=False, default="standing", index=True)
    pose_prompt: Mapped[str] = mapped_column(Text, nullable=False, default="")
    body_orientation: Mapped[str] = mapped_column(String(100), nullable=False, default="front")
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    use_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    avg_quality_score: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    pose_data: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False, default=dict)


# ---------------------------------------------------------------------------
# ExpressionPreset
# ---------------------------------------------------------------------------

class ExpressionPreset(UUIDMixin, TimestampMixin, Base):
    """Character expression library."""
    __tablename__ = "ag_expression_presets"

    name: Mapped[str] = mapped_column(String(200), nullable=False, index=True)
    slug: Mapped[str] = mapped_column(String(200), nullable=False, unique=True, index=True)
    description: Mapped[str] = mapped_column(Text, nullable=False, default="")
    # "neutral" | "happy" | "sad" | "angry" | "surprised" | "scared" | "disgusted"
    # "excited" | "thoughtful" | "confident" | "embarrassed"
    expression_type: Mapped[str] = mapped_column(String(100), nullable=False, default="neutral", index=True)
    expression_prompt: Mapped[str] = mapped_column(Text, nullable=False, default="")
    intensity: Mapped[float] = mapped_column(Float, nullable=False, default=0.7)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    use_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    avg_quality_score: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    expression_data: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False, default=dict)


# ---------------------------------------------------------------------------
# RetryQueue
# ---------------------------------------------------------------------------

class AgRetryQueue(UUIDMixin, TimestampMixin, Base):
    """Assets queued for automatic retry due to low quality or failure."""
    __tablename__ = "ag_retry_queue"

    asset_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("ag_assets.id", ondelete="CASCADE"),
        nullable=False, index=True,
    )
    project_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("projects.id", ondelete="CASCADE"),
        nullable=False, index=True,
    )
    # "low_quality" | "wrong_character" | "wrong_background" | "artifacts"
    # "wrong_pose" | "wrong_style" | "wrong_camera" | "generation_error"
    failure_reason: Mapped[str] = mapped_column(String(200), nullable=False, index=True)
    failure_details: Mapped[str] = mapped_column(Text, nullable=False, default="")
    quality_score: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    retry_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    max_retries: Mapped[int] = mapped_column(Integer, nullable=False, default=3)
    # "pending" | "retrying" | "resolved" | "exhausted"
    status: Mapped[str] = mapped_column(String(50), nullable=False, default="pending", index=True)
    priority: Mapped[int] = mapped_column(Integer, nullable=False, default=5, index=True)
    last_retry_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    resolved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    retry_params: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False, default=dict)

    __table_args__ = (
        Index("ix_ag_retry_queue_status_priority", "status", "priority"),
    )


# ---------------------------------------------------------------------------
# GenerationJob
# ---------------------------------------------------------------------------

class AgGenerationJob(UUIDMixin, TimestampMixin, Base):
    """Async job for asset generation pipeline stages."""
    __tablename__ = "ag_generation_jobs"

    project_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("projects.id", ondelete="SET NULL"),
        nullable=True, index=True,
    )
    asset_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("ag_assets.id", ondelete="SET NULL"),
        nullable=True, index=True,
    )
    episode_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), nullable=True, index=True,
    )
    # "plan_assets" | "generate_prompt" | "generate_image" | "evaluate_image"
    # "retry_generation" | "update_embeddings" | "generate_episode_assets"
    # "generate_character_assets" | "cleanup"
    job_type: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    # "pending" | "running" | "completed" | "failed" | "retrying"
    status: Mapped[str] = mapped_column(String(50), nullable=False, default="pending", index=True)
    # "sync" | "celery"
    dispatch_mode: Mapped[str] = mapped_column(String(50), nullable=False, default="sync")
    celery_task_id: Mapped[str] = mapped_column(String(500), nullable=False, default="")
    result: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False, default=dict)
    error_message: Mapped[str] = mapped_column(Text, nullable=False, default="")
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    duration_ms: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    retry_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    max_retries: Mapped[int] = mapped_column(Integer, nullable=False, default=3)
    params: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False, default=dict)
    metadata_: Mapped[dict[str, Any]] = mapped_column("ag_job_meta", JSON, nullable=False, default=dict)

    __table_args__ = (
        Index("ix_ag_generation_jobs_type_status", "job_type", "status"),
        Index("ix_ag_generation_jobs_project_status", "project_id", "status"),
    )


# ---------------------------------------------------------------------------
# GenerationHistory
# ---------------------------------------------------------------------------

class GenerationHistory(UUIDMixin, TimestampMixin, Base):
    """Summary log of completed generation pipeline runs."""
    __tablename__ = "ag_generation_history"

    project_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("projects.id", ondelete="CASCADE"),
        nullable=False, index=True,
    )
    episode_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), nullable=True, index=True,
    )
    # "episode" | "character" | "background" | "prop" | "manual"
    run_type: Mapped[str] = mapped_column(String(100), nullable=False, default="episode", index=True)
    triggered_by: Mapped[str] = mapped_column(String(100), nullable=False, default="system")
    assets_planned: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    assets_generated: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    assets_accepted: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    assets_rejected: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    retries_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    avg_quality_score: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    duration_seconds: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    # "completed" | "failed" | "partial"
    run_status: Mapped[str] = mapped_column(String(50), nullable=False, default="completed", index=True)
    error_summary: Mapped[str] = mapped_column(Text, nullable=False, default="")
    run_data: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False, default=dict)
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    finished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


# ---------------------------------------------------------------------------
# AssetCache
# ---------------------------------------------------------------------------

class AssetCache(UUIDMixin, TimestampMixin, Base):
    """Asset deduplication cache — avoids regenerating identical assets."""
    __tablename__ = "ag_cache"

    project_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("projects.id", ondelete="CASCADE"),
        nullable=False, index=True,
    )
    asset_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("ag_assets.id", ondelete="CASCADE"),
        nullable=False, index=True,
    )
    # SHA-256 of the full_prompt + generation_params
    cache_key: Mapped[str] = mapped_column(String(64), nullable=False, unique=True, index=True)
    asset_type: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    quality_score: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    hit_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    last_hit_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    is_valid: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True, index=True)


# ---------------------------------------------------------------------------
# AssetRelationship
# ---------------------------------------------------------------------------

class AssetRelationship(UUIDMixin, TimestampMixin, Base):
    """Asset-to-asset relationship (e.g., background ↔ prop, character ↔ expression)."""
    __tablename__ = "ag_relationships"

    source_asset_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("ag_assets.id", ondelete="CASCADE"),
        nullable=False, index=True,
    )
    target_asset_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("ag_assets.id", ondelete="CASCADE"),
        nullable=False, index=True,
    )
    # "variant_of" | "expression_of" | "pose_of" | "prop_in" | "background_for"
    # "character_in" | "turnaround_of" | "thumbnail_for"
    relationship_type: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    strength: Mapped[float] = mapped_column(Float, nullable=False, default=1.0)
    metadata_: Mapped[dict[str, Any]] = mapped_column("ag_rel_meta", JSON, nullable=False, default=dict)

    __table_args__ = (
        UniqueConstraint("source_asset_id", "target_asset_id", "relationship_type",
                         name="uq_ag_relationships_src_tgt_type"),
        Index("ix_ag_relationships_source_type", "source_asset_id", "relationship_type"),
    )

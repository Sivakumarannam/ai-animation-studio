"""
Module 2 — Animation Engine DB models.

New tables (DO NOT duplicate existing): Expression, Pose, CharacterTemplate,
SceneComposition, Timeline, AssetVersion.
Existing: Asset, Background, Prop, VoiceProfile, AnimationPreset are in asset.py.
"""
from __future__ import annotations

import uuid
from typing import Any

from sqlalchemy import BigInteger, Boolean, Float, ForeignKey, Integer, JSON, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from database.base import Base, TimestampMixin, UUIDMixin


# ---------------------------------------------------------------------------
# Expression Library
# ---------------------------------------------------------------------------

class Expression(UUIDMixin, TimestampMixin, Base):
    """
    A reusable facial expression.
    Expressions are global library items — shared across all characters.
    """
    __tablename__ = "expressions"

    name: Mapped[str] = mapped_column(String(100), nullable=False, unique=True)
    # e.g. "happy", "sad", "angry", "laugh", "smile", "shock", "fear",
    #      "cry", "thinking", "confused", "sleeping", "excited", "embarrassed"
    slug: Mapped[str] = mapped_column(String(100), nullable=False, unique=True, index=True)
    description: Mapped[str] = mapped_column(Text, nullable=False, default="")
    category: Mapped[str] = mapped_column(String(100), nullable=False, default="basic")
    # Blend-shape weights / rig parameters stored as JSON
    rig_data: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False, default=dict)
    thumbnail_url: Mapped[str] = mapped_column(String(500), nullable=False, default="")
    preview_url: Mapped[str] = mapped_column(String(500), nullable=False, default="")
    tags: Mapped[list[str]] = mapped_column(JSON, nullable=False, default=list)
    intensity: Mapped[float] = mapped_column(Float, nullable=False, default=1.0)
    is_library: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    sort_order: Mapped[int] = mapped_column(Integer, nullable=False, default=0)


# ---------------------------------------------------------------------------
# Pose Library
# ---------------------------------------------------------------------------

class Pose(UUIDMixin, TimestampMixin, Base):
    """
    A reusable body pose.
    Poses are global library items — shared across all characters.
    """
    __tablename__ = "poses"

    name: Mapped[str] = mapped_column(String(100), nullable=False, unique=True)
    # e.g. "idle", "walk", "run", "sit", "stand", "jump", "point",
    #      "wave", "eat", "drink", "read", "phone", "dance", "drive"
    slug: Mapped[str] = mapped_column(String(100), nullable=False, unique=True, index=True)
    description: Mapped[str] = mapped_column(Text, nullable=False, default="")
    category: Mapped[str] = mapped_column(String(100), nullable=False, default="basic")
    # Bone transforms / IK targets stored as JSON
    rig_data: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False, default=dict)
    thumbnail_url: Mapped[str] = mapped_column(String(500), nullable=False, default="")
    preview_url: Mapped[str] = mapped_column(String(500), nullable=False, default="")
    tags: Mapped[list[str]] = mapped_column(JSON, nullable=False, default=list)
    duration_frames: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    is_loopable: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    is_library: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    sort_order: Mapped[int] = mapped_column(Integer, nullable=False, default=0)


# ---------------------------------------------------------------------------
# Character Template
# ---------------------------------------------------------------------------

class CharacterTemplate(UUIDMixin, TimestampMixin, Base):
    """
    Reusable character template (library item).
    Projects create Character records that optionally reference a template;
    project-level overrides are stored in the Character.asset_data JSON.
    """
    __tablename__ = "character_templates"

    name: Mapped[str] = mapped_column(String(255), nullable=False)
    name_local: Mapped[str] = mapped_column(String(255), nullable=False, default="")
    slug: Mapped[str] = mapped_column(String(255), nullable=False, unique=True, index=True)
    archetype: Mapped[str] = mapped_column(String(100), nullable=False, default="")
    # Which plugin this template belongs to (empty = universal)
    plugin_id: Mapped[str] = mapped_column(String(100), nullable=False, default="", index=True)
    description: Mapped[str] = mapped_column(Text, nullable=False, default="")
    personality: Mapped[str] = mapped_column(Text, nullable=False, default="")
    age_range: Mapped[str] = mapped_column(String(50), nullable=False, default="")
    gender: Mapped[str] = mapped_column(String(50), nullable=False, default="")
    language: Mapped[str] = mapped_column(String(10), nullable=False, default="")
    # Voice profile JSON: {provider, voice_id, speed, pitch, style}
    voice_profile: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False, default=dict)
    # Animation rig: {rig_type, skeleton_url, mesh_url, ...}
    animation_rig: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False, default=dict)
    # Expression overrides: {expression_slug: custom_rig_data}
    expression_overrides: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False, default=dict)
    # Pose overrides: {pose_slug: custom_rig_data}
    pose_overrides: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False, default=dict)
    # Clothing variants: [{id, name, thumbnail_url, file_url}]
    clothing_variants: Mapped[list[dict[str, Any]]] = mapped_column(JSON, nullable=False, default=list)
    # Accessories: [{id, name, thumbnail_url, file_url, attach_point}]
    accessories: Mapped[list[dict[str, Any]]] = mapped_column(JSON, nullable=False, default=list)
    thumbnail_url: Mapped[str] = mapped_column(String(500), nullable=False, default="")
    preview_url: Mapped[str] = mapped_column(String(500), nullable=False, default="")
    tags: Mapped[list[str]] = mapped_column(JSON, nullable=False, default=list)
    typical_expressions: Mapped[list[str]] = mapped_column(JSON, nullable=False, default=list)
    # Extra plugin-specific metadata
    metadata_: Mapped[dict[str, Any]] = mapped_column("metadata", JSON, nullable=False, default=dict)
    is_library: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    is_deleted: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    version: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    sort_order: Mapped[int] = mapped_column(Integer, nullable=False, default=0)


# ---------------------------------------------------------------------------
# Scene Composition
# ---------------------------------------------------------------------------

class SceneComposition(UUIDMixin, TimestampMixin, Base):
    """
    Full visual composition for a scene.
    One-to-one with a Scene; stores all layer/object data as structured JSON.
    """
    __tablename__ = "scene_compositions"

    scene_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("scenes.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
        index=True,
    )
    # Background reference
    background_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), nullable=True)
    background_override: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False, default=dict)
    # Camera: {x, y, zoom, rotation, motion_type}
    camera: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False, default=dict)
    # Lighting: {ambient, key_light, fill_light, rim_light, time_of_day}
    lighting: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False, default=dict)
    # Ordered array of layer objects
    # Each layer: {id, type, name, visible, locked, z_index, ...type-specific data}
    layers: Mapped[list[dict[str, Any]]] = mapped_column(JSON, nullable=False, default=list)
    # Characters placed in scene: [{character_id, template_id, position, scale, rotation, expression, pose, clothing, accessories}]
    characters: Mapped[list[dict[str, Any]]] = mapped_column(JSON, nullable=False, default=list)
    # Props placed in scene: [{prop_id, position, scale, rotation, z_index}]
    props: Mapped[list[dict[str, Any]]] = mapped_column(JSON, nullable=False, default=list)
    # Canvas dimensions
    canvas_width: Mapped[int] = mapped_column(Integer, nullable=False, default=1920)
    canvas_height: Mapped[int] = mapped_column(Integer, nullable=False, default=1080)
    # Status: draft | ready | rendering | done
    status: Mapped[str] = mapped_column(String(50), nullable=False, default="draft")
    version: Mapped[int] = mapped_column(Integer, nullable=False, default=1)

    scene: Mapped["Scene"] = relationship("Scene")  # type: ignore[name-defined]  # noqa: F821


# ---------------------------------------------------------------------------
# Timeline
# ---------------------------------------------------------------------------

class Timeline(UUIDMixin, TimestampMixin, Base):
    """
    Animation timeline for a scene composition.
    One-to-one with a SceneComposition.
    """
    __tablename__ = "timelines"

    composition_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("scene_compositions.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
        index=True,
    )
    fps: Mapped[int] = mapped_column(Integer, nullable=False, default=24)
    total_frames: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    duration_seconds: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)

    # Keyframes: [{frame, layer_id, property, value, easing}]
    keyframes: Mapped[list[dict[str, Any]]] = mapped_column(JSON, nullable=False, default=list)

    # Animation clips: [{id, layer_id, type, start_frame, end_frame, data}]
    # type: "pose" | "expression" | "motion" | "custom"
    clips: Mapped[list[dict[str, Any]]] = mapped_column(JSON, nullable=False, default=list)

    # Transitions between clips: [{from_frame, to_frame, type, duration_frames}]
    transitions: Mapped[list[dict[str, Any]]] = mapped_column(JSON, nullable=False, default=list)

    # Camera events: [{frame, type, data}]
    camera_events: Mapped[list[dict[str, Any]]] = mapped_column(JSON, nullable=False, default=list)

    # Audio events: [{frame, asset_id, volume, fade_in, fade_out}]
    audio_events: Mapped[list[dict[str, Any]]] = mapped_column(JSON, nullable=False, default=list)

    # Subtitle events: [{frame, end_frame, text, character, style}]
    subtitle_events: Mapped[list[dict[str, Any]]] = mapped_column(JSON, nullable=False, default=list)

    # Playhead position for editor state
    playhead_frame: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    composition: Mapped["SceneComposition"] = relationship("SceneComposition")


# ---------------------------------------------------------------------------
# Asset Version
# ---------------------------------------------------------------------------

class AssetVersion(UUIDMixin, TimestampMixin, Base):
    """
    Version record for any versioned asset (background, prop, character, etc.).
    Links to the parent asset via asset_type + asset_id.
    """
    __tablename__ = "asset_versions"

    asset_type: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    # e.g. "background", "prop", "character_template", "expression", "pose"
    asset_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False, index=True)
    version_number: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    # What changed in this version
    change_summary: Mapped[str] = mapped_column(Text, nullable=False, default="")
    # Snapshot of the asset data at this version
    snapshot: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False, default=dict)
    file_url: Mapped[str] = mapped_column(String(500), nullable=False, default="")
    file_size_bytes: Mapped[int] = mapped_column(BigInteger, nullable=False, default=0)
    created_by: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), nullable=True)
    is_published: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)

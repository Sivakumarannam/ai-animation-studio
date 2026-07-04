import uuid
from typing import Any

from sqlalchemy import BigInteger, Boolean, Float, ForeignKey, JSON, String, Text, ARRAY
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from database.base import Base, TimestampMixin, UUIDMixin


class Asset(UUIDMixin, TimestampMixin, Base):
    __tablename__ = "assets"

    scene_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("scenes.id", ondelete="CASCADE"), nullable=True, index=True
    )
    asset_type: Mapped[str] = mapped_column(String(100), nullable=False)
    file_url: Mapped[str] = mapped_column(String(500), nullable=False, default="")
    storage_bucket: Mapped[str] = mapped_column(String(255), nullable=False, default="")
    storage_key: Mapped[str] = mapped_column(String(500), nullable=False, default="")
    file_size_bytes: Mapped[int] = mapped_column(BigInteger, nullable=False, default=0)
    duration_seconds: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    metadata_: Mapped[dict[str, Any]] = mapped_column("metadata", JSON, nullable=False, default=dict)
    status: Mapped[str] = mapped_column(String(50), nullable=False, default="pending")

    scene: Mapped["Scene | None"] = relationship("Scene", back_populates="assets")  # type: ignore[name-defined]  # noqa: F821


class Background(UUIDMixin, Base):
    __tablename__ = "backgrounds"

    name: Mapped[str] = mapped_column(String(255), nullable=False)
    category: Mapped[str] = mapped_column(String(100), nullable=False, default="")
    tags: Mapped[list[str]] = mapped_column(JSON, nullable=False, default=list)
    file_url: Mapped[str] = mapped_column(String(500), nullable=False, default="")
    thumbnail_url: Mapped[str] = mapped_column(String(500), nullable=False, default="")
    is_library: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    project_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), nullable=True)
    created_at: Mapped[str] = mapped_column(String(50), nullable=False, default="")
    is_deleted: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    metadata_: Mapped[dict[str, Any]] = mapped_column("metadata", JSON, nullable=False, default=dict)


class Prop(UUIDMixin, Base):
    __tablename__ = "props"

    name: Mapped[str] = mapped_column(String(255), nullable=False)
    category: Mapped[str] = mapped_column(String(100), nullable=False, default="")
    tags: Mapped[list[str]] = mapped_column(JSON, nullable=False, default=list)
    file_url: Mapped[str] = mapped_column(String(500), nullable=False, default="")
    thumbnail_url: Mapped[str] = mapped_column(String(500), nullable=False, default="")
    is_library: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    project_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), nullable=True)
    created_at: Mapped[str] = mapped_column(String(50), nullable=False, default="")
    is_deleted: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    metadata_: Mapped[dict[str, Any]] = mapped_column("metadata", JSON, nullable=False, default=dict)


class VoiceProfile(UUIDMixin, Base):
    __tablename__ = "voice_profiles"

    name: Mapped[str] = mapped_column(String(255), nullable=False)
    provider: Mapped[str] = mapped_column(String(100), nullable=False, default="")
    provider_voice_id: Mapped[str] = mapped_column(String(255), nullable=False, default="")
    language: Mapped[str] = mapped_column(String(10), nullable=False, default="en")
    gender: Mapped[str] = mapped_column(String(50), nullable=False, default="")
    age_range: Mapped[str] = mapped_column(String(50), nullable=False, default="")
    sample_url: Mapped[str] = mapped_column(String(500), nullable=False, default="")
    is_library: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    created_at: Mapped[str] = mapped_column(String(50), nullable=False, default="")


class AnimationPreset(UUIDMixin, Base):
    __tablename__ = "animation_presets"

    name: Mapped[str] = mapped_column(String(255), nullable=False)
    category: Mapped[str] = mapped_column(String(100), nullable=False, default="")
    data: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False, default=dict)
    preview_url: Mapped[str] = mapped_column(String(500), nullable=False, default="")
    is_library: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    created_at: Mapped[str] = mapped_column(String(50), nullable=False, default="")
    is_deleted: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    tags: Mapped[list[str]] = mapped_column(JSON, nullable=False, default=list)
    metadata_: Mapped[dict[str, Any]] = mapped_column("metadata", JSON, nullable=False, default=dict)


class Audio(UUIDMixin, TimestampMixin, Base):
    __tablename__ = "audio"

    name: Mapped[str] = mapped_column(String(255), nullable=False)
    category: Mapped[str] = mapped_column(String(100), nullable=False, default="")
    tags: Mapped[list[str]] = mapped_column(JSON, nullable=False, default=list)
    file_url: Mapped[str] = mapped_column(String(500), nullable=False, default="")
    preview_url: Mapped[str] = mapped_column(String(500), nullable=False, default="")
    duration_seconds: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    is_library: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    project_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), nullable=True)
    is_deleted: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    metadata_: Mapped[dict[str, Any]] = mapped_column("metadata", JSON, nullable=False, default=dict)


class Music(UUIDMixin, TimestampMixin, Base):
    __tablename__ = "music"

    name: Mapped[str] = mapped_column(String(255), nullable=False)
    category: Mapped[str] = mapped_column(String(100), nullable=False, default="")
    tags: Mapped[list[str]] = mapped_column(JSON, nullable=False, default=list)
    file_url: Mapped[str] = mapped_column(String(500), nullable=False, default="")
    preview_url: Mapped[str] = mapped_column(String(500), nullable=False, default="")
    duration_seconds: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    is_library: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    project_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), nullable=True)
    is_deleted: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    metadata_: Mapped[dict[str, Any]] = mapped_column("metadata", JSON, nullable=False, default=dict)


class SoundEffect(UUIDMixin, TimestampMixin, Base):
    __tablename__ = "sound_effects"

    name: Mapped[str] = mapped_column(String(255), nullable=False)
    category: Mapped[str] = mapped_column(String(100), nullable=False, default="")
    tags: Mapped[list[str]] = mapped_column(JSON, nullable=False, default=list)
    file_url: Mapped[str] = mapped_column(String(500), nullable=False, default="")
    preview_url: Mapped[str] = mapped_column(String(500), nullable=False, default="")
    duration_seconds: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    is_library: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    project_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), nullable=True)
    is_deleted: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    metadata_: Mapped[dict[str, Any]] = mapped_column("metadata", JSON, nullable=False, default=dict)

import uuid
from typing import Any

from sqlalchemy import Boolean, ForeignKey, JSON, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from database.base import Base, TimestampMixin, UUIDMixin


class Character(UUIDMixin, TimestampMixin, Base):
    __tablename__ = "characters"

    project_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("projects.id", ondelete="CASCADE"), nullable=False, index=True
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False, default="")
    personality: Mapped[str] = mapped_column(Text, nullable=False, default="")
    voice_profile: Mapped[str] = mapped_column(String(255), nullable=False, default="")
    age_range: Mapped[str] = mapped_column(String(50), nullable=False, default="")
    gender: Mapped[str] = mapped_column(String(50), nullable=False, default="")
    is_library: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    thumbnail_url: Mapped[str] = mapped_column(String(500), nullable=False, default="")
    asset_data: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False, default=dict)

    project: Mapped["Project"] = relationship("Project", back_populates="characters")  # type: ignore[name-defined]  # noqa: F821

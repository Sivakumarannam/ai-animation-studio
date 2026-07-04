import uuid
from typing import Any

from sqlalchemy import ForeignKey, Integer, JSON, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from database.base import Base, TimestampMixin, UUIDMixin


class Story(UUIDMixin, TimestampMixin, Base):
    __tablename__ = "stories"

    project_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("projects.id", ondelete="CASCADE"), nullable=False, index=True
    )
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    premise: Mapped[str] = mapped_column(Text, nullable=False, default="")
    full_script: Mapped[str] = mapped_column(Text, nullable=False, default="")
    genre: Mapped[str] = mapped_column(String(100), nullable=False, default="")
    tone: Mapped[str] = mapped_column(String(100), nullable=False, default="")
    duration_target: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    language: Mapped[str] = mapped_column(String(10), nullable=False, default="en")
    status: Mapped[str] = mapped_column(String(50), nullable=False, default="draft", index=True)
    ai_metadata: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False, default=dict)

    project: Mapped["Project"] = relationship("Project", back_populates="stories")  # type: ignore[name-defined]  # noqa: F821
    scenes: Mapped[list["Scene"]] = relationship(  # type: ignore[name-defined]  # noqa: F821
        "Scene", back_populates="story", lazy="select", order_by="Scene.ordering"
    )

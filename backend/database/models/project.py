import uuid
from typing import Any

from sqlalchemy import ForeignKey, JSON, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from database.base import Base, TimestampMixin, UUIDMixin


class Project(UUIDMixin, TimestampMixin, Base):
    __tablename__ = "projects"

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False, default="")
    status: Mapped[str] = mapped_column(String(50), nullable=False, default="draft", index=True)
    plugin_id: Mapped[str] = mapped_column(String(100), nullable=False, default="")
    animation_style: Mapped[str] = mapped_column(String(100), nullable=False, default="cartoon_2d")
    metadata_: Mapped[dict[str, Any]] = mapped_column("metadata", JSON, nullable=False, default=dict)

    user: Mapped["User"] = relationship("User", back_populates="projects")  # type: ignore[name-defined]  # noqa: F821
    stories: Mapped[list["Story"]] = relationship(
        "Story", back_populates="project", lazy="select", passive_deletes=True
    )
    characters: Mapped[list["Character"]] = relationship(
        "Character", back_populates="project", lazy="select", passive_deletes=True
    )





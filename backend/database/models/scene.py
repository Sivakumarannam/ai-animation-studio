import uuid

from sqlalchemy import Float, ForeignKey, Integer, JSON, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from database.base import Base, TimestampMixin, UUIDMixin


class Scene(UUIDMixin, TimestampMixin, Base):
    __tablename__ = "scenes"

    story_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("stories.id", ondelete="CASCADE"), nullable=False, index=True
    )
    scene_number: Mapped[int] = mapped_column(Integer, nullable=False)
    title: Mapped[str] = mapped_column(String(255), nullable=False, default="")
    description: Mapped[str] = mapped_column(Text, nullable=False, default="")
    dialogue: Mapped[str] = mapped_column(Text, nullable=False, default="")
    action_notes: Mapped[str] = mapped_column(Text, nullable=False, default="")
    duration_seconds: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    background_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), nullable=True)
    status: Mapped[str] = mapped_column(String(50), nullable=False, default="pending")
    ordering: Mapped[int] = mapped_column(Integer, nullable=False, default=0, index=True)

    story: Mapped["Story"] = relationship("Story", back_populates="scenes")  # type: ignore[name-defined]  # noqa: F821
    scene_characters: Mapped[list["SceneCharacter"]] = relationship(
        "SceneCharacter", back_populates="scene", lazy="select"
    )
    assets: Mapped[list["Asset"]] = relationship(  # type: ignore[name-defined]  # noqa: F821
        "Asset", back_populates="scene", lazy="select"
    )


class SceneCharacter(Base):
    __tablename__ = "scene_characters"

    scene_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("scenes.id", ondelete="CASCADE"), primary_key=True
    )
    character_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("characters.id", ondelete="CASCADE"), primary_key=True
    )
    role: Mapped[str] = mapped_column(String(100), nullable=False, default="supporting")
    position_data: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)

    scene: Mapped["Scene"] = relationship("Scene", back_populates="scene_characters")
    character: Mapped["Character"] = relationship("Character")  # type: ignore[name-defined]  # noqa: F821

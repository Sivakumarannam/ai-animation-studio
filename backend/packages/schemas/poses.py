from typing import Any
from pydantic import BaseModel, Field


class PoseCreate(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    slug: str = Field(min_length=1, max_length=100)
    description: str = ""
    category: str = "basic"
    rig_data: dict[str, Any] = {}
    thumbnail_url: str = ""
    preview_url: str = ""
    tags: list[str] = []
    duration_frames: int = Field(default=1, ge=1)
    is_loopable: bool = False
    sort_order: int = 0


class PoseUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=100)
    description: str | None = None
    category: str | None = None
    rig_data: dict[str, Any] | None = None
    thumbnail_url: str | None = None
    preview_url: str | None = None
    tags: list[str] | None = None
    duration_frames: int | None = None
    is_loopable: bool | None = None
    sort_order: int | None = None


class PoseResponse(BaseModel):
    id: str
    name: str
    slug: str
    description: str
    category: str
    rig_data: dict[str, Any]
    thumbnail_url: str
    preview_url: str
    tags: list[str]
    duration_frames: int
    is_loopable: bool
    is_library: bool
    sort_order: int
    created_at: str
    updated_at: str

    model_config = {"from_attributes": True}

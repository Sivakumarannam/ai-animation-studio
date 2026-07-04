from typing import Any
from pydantic import BaseModel, Field


class ExpressionCreate(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    slug: str = Field(min_length=1, max_length=100)
    description: str = ""
    category: str = "basic"
    rig_data: dict[str, Any] = {}
    thumbnail_url: str = ""
    preview_url: str = ""
    tags: list[str] = []
    intensity: float = Field(default=1.0, ge=0.0, le=2.0)
    sort_order: int = 0


class ExpressionUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=100)
    description: str | None = None
    category: str | None = None
    rig_data: dict[str, Any] | None = None
    thumbnail_url: str | None = None
    preview_url: str | None = None
    tags: list[str] | None = None
    intensity: float | None = None
    sort_order: int | None = None


class ExpressionResponse(BaseModel):
    id: str
    name: str
    slug: str
    description: str
    category: str
    rig_data: dict[str, Any]
    thumbnail_url: str
    preview_url: str
    tags: list[str]
    intensity: float
    is_library: bool
    sort_order: int
    created_at: str
    updated_at: str

    model_config = {"from_attributes": True}

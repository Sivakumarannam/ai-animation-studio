from typing import Any
from pydantic import BaseModel, Field


class ProjectCreate(BaseModel):
    title: str = Field(min_length=1, max_length=500)
    description: str = ""
    plugin_id: str = Field(min_length=1, max_length=100)
    animation_style: str = "cartoon_2d"
    metadata: dict[str, Any] = {}


class ProjectUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=500)
    description: str | None = None
    animation_style: str | None = None
    status: str | None = None
    metadata: dict[str, Any] | None = None


class ProjectResponse(BaseModel):
    id: str
    user_id: str
    title: str
    description: str
    status: str
    plugin_id: str
    animation_style: str
    metadata: dict[str, Any]
    created_at: str
    updated_at: str

    model_config = {"from_attributes": True}

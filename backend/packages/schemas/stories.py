from typing import Any
from pydantic import BaseModel, Field


class StoryCreate(BaseModel):
    title: str = Field(min_length=1, max_length=500)
    premise: str = ""
    genre: str = ""
    tone: str = ""
    duration_target: int = Field(default=0, ge=0)
    language: str = "en"


class StoryUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=500)
    premise: str | None = None
    full_script: str | None = None
    genre: str | None = None
    tone: str | None = None
    duration_target: int | None = None
    language: str | None = None
    status: str | None = None


class StoryGenerateRequest(BaseModel):
    premise: str = Field(min_length=10)
    genre: str = ""
    tone: str = ""
    duration_target: int = Field(default=300, ge=30, le=3600)
    language: str = "en"
    style_hints: dict[str, Any] = {}


class StoryResponse(BaseModel):
    id: str
    project_id: str
    title: str
    premise: str
    full_script: str
    genre: str
    tone: str
    duration_target: int
    language: str
    status: str
    ai_metadata: dict[str, Any]
    created_at: str
    updated_at: str

    model_config = {"from_attributes": True}

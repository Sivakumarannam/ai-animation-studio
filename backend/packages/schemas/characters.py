from typing import Any
from pydantic import BaseModel, Field


class CharacterCreate(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    description: str = ""
    personality: str = ""
    voice_profile: str = ""
    age_range: str = ""
    gender: str = ""
    asset_data: dict[str, Any] = {}


class CharacterUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=255)
    description: str | None = None
    personality: str | None = None
    voice_profile: str | None = None
    age_range: str | None = None
    gender: str | None = None
    thumbnail_url: str | None = None
    asset_data: dict[str, Any] | None = None


class CharacterResponse(BaseModel):
    id: str
    project_id: str
    name: str
    description: str
    personality: str
    voice_profile: str
    age_range: str
    gender: str
    is_library: bool
    thumbnail_url: str
    asset_data: dict[str, Any]
    created_at: str
    updated_at: str

    model_config = {"from_attributes": True}

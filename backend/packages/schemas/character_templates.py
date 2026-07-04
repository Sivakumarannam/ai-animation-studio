from typing import Any
from pydantic import BaseModel, Field


class CharacterTemplateCreate(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    name_local: str = ""
    slug: str = Field(min_length=1, max_length=255)
    archetype: str = ""
    plugin_id: str = ""
    description: str = ""
    personality: str = ""
    age_range: str = ""
    gender: str = ""
    language: str = ""
    voice_profile: dict[str, Any] = {}
    animation_rig: dict[str, Any] = {}
    expression_overrides: dict[str, Any] = {}
    pose_overrides: dict[str, Any] = {}
    clothing_variants: list[dict[str, Any]] = []
    accessories: list[dict[str, Any]] = []
    thumbnail_url: str = ""
    preview_url: str = ""
    tags: list[str] = []
    typical_expressions: list[str] = []
    metadata_: dict[str, Any] = {}
    sort_order: int = 0


class CharacterTemplateUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=255)
    name_local: str | None = None
    archetype: str | None = None
    description: str | None = None
    personality: str | None = None
    age_range: str | None = None
    gender: str | None = None
    voice_profile: dict[str, Any] | None = None
    animation_rig: dict[str, Any] | None = None
    expression_overrides: dict[str, Any] | None = None
    pose_overrides: dict[str, Any] | None = None
    clothing_variants: list[dict[str, Any]] | None = None
    accessories: list[dict[str, Any]] | None = None
    thumbnail_url: str | None = None
    preview_url: str | None = None
    tags: list[str] | None = None
    typical_expressions: list[str] | None = None
    sort_order: int | None = None


class CharacterTemplateResponse(BaseModel):
    id: str
    name: str
    name_local: str
    slug: str
    archetype: str
    plugin_id: str
    description: str
    personality: str
    age_range: str
    gender: str
    language: str
    voice_profile: dict[str, Any]
    animation_rig: dict[str, Any]
    expression_overrides: dict[str, Any]
    pose_overrides: dict[str, Any]
    clothing_variants: list[dict[str, Any]]
    accessories: list[dict[str, Any]]
    thumbnail_url: str
    preview_url: str
    tags: list[str]
    typical_expressions: list[str]
    is_library: bool
    version: int
    sort_order: int
    created_at: str
    updated_at: str

    model_config = {"from_attributes": True}

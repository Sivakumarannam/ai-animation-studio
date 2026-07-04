"""Enhanced schemas for Background, Prop, and Asset Manager search."""
from typing import Any
from uuid import UUID
from pydantic import BaseModel, Field


# ---------------------------------------------------------------------------
# Background (enhanced)
# ---------------------------------------------------------------------------

class BackgroundCreate(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    category: str = ""
    tags: list[str] = []
    file_url: str = ""
    thumbnail_url: str = ""
    description: str = ""
    style: str = ""       # e.g. "cartoon", "realistic", "watercolor"
    time_of_day: str = "" # "day", "night", "sunset", "dawn"
    weather: str = ""     # "clear", "rain", "snow"
    is_library: bool = True
    project_id: UUID | None = None
    metadata_: dict[str, Any] = {}


class BackgroundUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=255)
    category: str | None = None
    tags: list[str] | None = None
    file_url: str | None = None
    thumbnail_url: str | None = None
    description: str | None = None
    style: str | None = None
    time_of_day: str | None = None
    weather: str | None = None


class BackgroundResponse(BaseModel):
    id: str
    name: str
    category: str
    tags: list[str]
    file_url: str
    thumbnail_url: str
    is_library: bool
    project_id: str | None
    created_at: str

    model_config = {"from_attributes": True}


# ---------------------------------------------------------------------------
# Prop (enhanced)
# ---------------------------------------------------------------------------

class PropCreate(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    category: str = ""
    tags: list[str] = []
    file_url: str = ""
    thumbnail_url: str = ""
    description: str = ""
    # Drag-and-drop placement defaults
    default_width: float = 100.0
    default_height: float = 100.0
    pivot_x: float = 0.5  # 0=left, 0.5=center, 1=right
    pivot_y: float = 0.5  # 0=top, 0.5=center, 1=bottom
    attach_point: str = ""  # e.g. "hand_left", "hand_right", "floor"
    is_library: bool = True
    project_id: UUID | None = None
    metadata_: dict[str, Any] = {}


class PropUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=255)
    category: str | None = None
    tags: list[str] | None = None
    file_url: str | None = None
    thumbnail_url: str | None = None
    description: str | None = None
    default_width: float | None = None
    default_height: float | None = None


class PropResponse(BaseModel):
    id: str
    name: str
    category: str
    tags: list[str]
    file_url: str
    thumbnail_url: str
    is_library: bool
    project_id: str | None
    created_at: str

    model_config = {"from_attributes": True}


# ---------------------------------------------------------------------------
# Asset Manager — search/import/export
# ---------------------------------------------------------------------------

class AssetSearchRequest(BaseModel):
    query: str = ""
    asset_types: list[str] = []   # "background", "prop", "expression", "pose", "character_template"
    categories: list[str] = []
    tags: list[str] = []
    is_library: bool | None = None
    page: int = Field(default=1, ge=1)
    page_size: int = Field(default=24, ge=1, le=100)


class AssetSearchResult(BaseModel):
    asset_type: str
    id: str
    name: str
    category: str
    tags: list[str]
    thumbnail_url: str
    is_library: bool


class AssetSearchResponse(BaseModel):
    results: list[AssetSearchResult]
    total: int
    page: int
    page_size: int
    total_pages: int


class AssetImportRequest(BaseModel):
    asset_type: str  # "background" | "prop" | "character_template"
    file_url: str
    name: str
    category: str = ""
    tags: list[str] = []
    metadata_: dict[str, Any] = {}


class AssetExportRequest(BaseModel):
    asset_type: str
    asset_id: UUID
    format: str = "json"  # "json" | "zip"


class DuplicateCheckResponse(BaseModel):
    is_duplicate: bool
    duplicate_id: str | None
    similarity_score: float

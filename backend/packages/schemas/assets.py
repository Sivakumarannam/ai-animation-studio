from typing import Any
from uuid import UUID
from pydantic import BaseModel, Field


class BackgroundCreate(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    category: str = ""
    tags: list[str] = []
    is_library: bool = True
    project_id: str | None = None
    metadata_: dict[str, Any] = {}


class BackgroundResponse(BaseModel):
    id: str
    name: str
    category: str
    tags: list[str]
    file_url: str
    thumbnail_url: str
    is_library: bool
    project_id: str | None
    is_deleted: bool = False
    metadata_: dict[str, Any] = Field(default={}, alias="metadata")
    created_at: str

    model_config = {"from_attributes": True, "populate_by_name": True}


class PropCreate(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    category: str = ""
    tags: list[str] = []
    is_library: bool = True
    project_id: str | None = None
    metadata_: dict[str, Any] = {}


class PropResponse(BaseModel):
    id: str
    name: str
    category: str
    tags: list[str]
    file_url: str
    thumbnail_url: str
    is_library: bool
    project_id: str | None
    is_deleted: bool = False
    metadata_: dict[str, Any] = Field(default={}, alias="metadata")
    created_at: str

    model_config = {"from_attributes": True, "populate_by_name": True}


class AssetUploadResponse(BaseModel):
    id: str
    asset_type: str
    file_url: str
    storage_bucket: str
    storage_key: str
    file_size_bytes: int
    status: str
    metadata: dict[str, Any]
    created_at: str

    model_config = {"from_attributes": True}


# Audio
class AudioCreate(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    category: str = ""
    tags: list[str] = []
    file_url: str = ""
    preview_url: str = ""
    duration_seconds: float = 0.0
    is_library: bool = True
    project_id: UUID | None = None
    metadata_: dict[str, Any] = {}


class AudioUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=255)
    category: str | None = None
    tags: list[str] | None = None
    file_url: str | None = None
    preview_url: str | None = None
    duration_seconds: float | None = None
    is_library: bool | None = None
    project_id: UUID | None = None
    metadata_: dict[str, Any] | None = None


class AudioResponse(BaseModel):
    id: str
    name: str
    category: str
    tags: list[str]
    file_url: str
    preview_url: str
    duration_seconds: float
    is_library: bool
    project_id: str | None
    is_deleted: bool
    metadata_: dict[str, Any] = Field(default={}, alias="metadata")
    created_at: str
    updated_at: str

    model_config = {"from_attributes": True, "populate_by_name": True}


# Music
class MusicCreate(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    category: str = ""
    tags: list[str] = []
    file_url: str = ""
    preview_url: str = ""
    duration_seconds: float = 0.0
    is_library: bool = True
    project_id: UUID | None = None
    metadata_: dict[str, Any] = {}


class MusicUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=255)
    category: str | None = None
    tags: list[str] | None = None
    file_url: str | None = None
    preview_url: str | None = None
    duration_seconds: float | None = None
    is_library: bool | None = None
    project_id: UUID | None = None
    metadata_: dict[str, Any] | None = None


class MusicResponse(BaseModel):
    id: str
    name: str
    category: str
    tags: list[str]
    file_url: str
    preview_url: str
    duration_seconds: float
    is_library: bool
    project_id: str | None
    is_deleted: bool
    metadata_: dict[str, Any] = Field(default={}, alias="metadata")
    created_at: str
    updated_at: str

    model_config = {"from_attributes": True, "populate_by_name": True}


# Sound Effect
class SoundEffectCreate(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    category: str = ""
    tags: list[str] = []
    file_url: str = ""
    preview_url: str = ""
    duration_seconds: float = 0.0
    is_library: bool = True
    project_id: UUID | None = None
    metadata_: dict[str, Any] = {}


class SoundEffectUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=255)
    category: str | None = None
    tags: list[str] | None = None
    file_url: str | None = None
    preview_url: str | None = None
    duration_seconds: float | None = None
    is_library: bool | None = None
    project_id: UUID | None = None
    metadata_: dict[str, Any] | None = None


class SoundEffectResponse(BaseModel):
    id: str
    name: str
    category: str
    tags: list[str]
    file_url: str
    preview_url: str
    duration_seconds: float
    is_library: bool
    project_id: str | None
    is_deleted: bool
    metadata_: dict[str, Any] = Field(default={}, alias="metadata")
    created_at: str
    updated_at: str

    model_config = {"from_attributes": True, "populate_by_name": True}


# Animation Preset
class AnimationPresetCreate(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    category: str = ""
    data: dict[str, Any] = {}
    preview_url: str = ""
    is_library: bool = True
    tags: list[str] = []
    metadata_: dict[str, Any] = {}


class AnimationPresetUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=255)
    category: str | None = None
    data: dict[str, Any] | None = None
    preview_url: str | None = None
    is_library: bool | None = None
    tags: list[str] | None = None
    metadata_: dict[str, Any] | None = None


class AnimationPresetResponse(BaseModel):
    id: str
    name: str
    category: str
    data: dict[str, Any]
    preview_url: str
    is_library: bool
    is_deleted: bool
    tags: list[str]
    metadata_: dict[str, Any] = Field(default={}, alias="metadata")
    created_at: str

    model_config = {"from_attributes": True, "populate_by_name": True}


# Bulk Requests
class BulkDeleteRequest(BaseModel):
    ids: list[UUID]


class BulkRestoreRequest(BaseModel):
    ids: list[UUID]


class BulkUpdateRequest(BaseModel):
    ids: list[UUID]
    category: str | None = None
    tags: list[str] | None = None
    metadata_: dict[str, Any] | None = None

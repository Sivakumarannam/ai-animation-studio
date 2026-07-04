from typing import Any
from uuid import UUID
from pydantic import BaseModel, Field


# ---------------------------------------------------------------------------
# Scene Composition
# ---------------------------------------------------------------------------

class CompositionCreate(BaseModel):
    scene_id: UUID
    background_id: UUID | None = None
    background_override: dict[str, Any] = {}
    camera: dict[str, Any] = {}
    lighting: dict[str, Any] = {}
    layers: list[dict[str, Any]] = []
    characters: list[dict[str, Any]] = []
    props: list[dict[str, Any]] = []
    canvas_width: int = Field(default=1920, ge=1)
    canvas_height: int = Field(default=1080, ge=1)


class CompositionUpdate(BaseModel):
    background_id: UUID | None = None
    background_override: dict[str, Any] | None = None
    camera: dict[str, Any] | None = None
    lighting: dict[str, Any] | None = None
    layers: list[dict[str, Any]] | None = None
    characters: list[dict[str, Any]] | None = None
    props: list[dict[str, Any]] | None = None
    canvas_width: int | None = None
    canvas_height: int | None = None
    status: str | None = None


class CompositionResponse(BaseModel):
    id: str
    scene_id: str
    background_id: str | None
    background_override: dict[str, Any]
    camera: dict[str, Any]
    lighting: dict[str, Any]
    layers: list[dict[str, Any]]
    characters: list[dict[str, Any]]
    props: list[dict[str, Any]]
    canvas_width: int
    canvas_height: int
    status: str
    version: int
    created_at: str
    updated_at: str

    model_config = {"from_attributes": True}


# ---------------------------------------------------------------------------
# Timeline
# ---------------------------------------------------------------------------

class TimelineCreate(BaseModel):
    composition_id: UUID
    fps: int = Field(default=24, ge=1, le=120)
    total_frames: int = Field(default=0, ge=0)
    duration_seconds: float = Field(default=0.0, ge=0.0)
    keyframes: list[dict[str, Any]] = []
    clips: list[dict[str, Any]] = []
    transitions: list[dict[str, Any]] = []
    camera_events: list[dict[str, Any]] = []
    audio_events: list[dict[str, Any]] = []
    subtitle_events: list[dict[str, Any]] = []


class TimelineUpdate(BaseModel):
    fps: int | None = None
    total_frames: int | None = None
    duration_seconds: float | None = None
    keyframes: list[dict[str, Any]] | None = None
    clips: list[dict[str, Any]] | None = None
    transitions: list[dict[str, Any]] | None = None
    camera_events: list[dict[str, Any]] | None = None
    audio_events: list[dict[str, Any]] | None = None
    subtitle_events: list[dict[str, Any]] | None = None
    playhead_frame: int | None = None


class TimelineResponse(BaseModel):
    id: str
    composition_id: str
    fps: int
    total_frames: int
    duration_seconds: float
    keyframes: list[dict[str, Any]]
    clips: list[dict[str, Any]]
    transitions: list[dict[str, Any]]
    camera_events: list[dict[str, Any]]
    audio_events: list[dict[str, Any]]
    subtitle_events: list[dict[str, Any]]
    playhead_frame: int
    created_at: str
    updated_at: str

    model_config = {"from_attributes": True}


# ---------------------------------------------------------------------------
# Asset Version
# ---------------------------------------------------------------------------

class AssetVersionResponse(BaseModel):
    id: str
    asset_type: str
    asset_id: str
    version_number: int
    change_summary: str
    file_url: str
    file_size_bytes: int
    is_published: bool
    created_at: str

    model_config = {"from_attributes": True}

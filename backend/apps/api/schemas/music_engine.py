"""
Phase 9 — Music & Sound Engine Pydantic v2 schemas.
Mirrors animation_engine.py / voice_engine.py schemas shape exactly.
"""
from __future__ import annotations

from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict


# ---------------------------------------------------------------------------
# Shared
# ---------------------------------------------------------------------------

class PaginationMeta(BaseModel):
    total: int
    page: int
    page_size: int
    total_pages: int


# ---------------------------------------------------------------------------
# MusicGenerationJob
# ---------------------------------------------------------------------------

class MusicJobResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    project_id: UUID
    scene_id: UUID | None = None
    episode_id: UUID | None = None
    job_type: str
    status: str
    mood: str
    triggered_by: str
    params: dict[str, Any]
    result: dict[str, Any] | None = None
    error_message: str | None = None
    started_at: datetime | None = None
    completed_at: datetime | None = None
    created_at: datetime
    updated_at: datetime


class MusicJobListResponse(BaseModel):
    items: list[MusicJobResponse]
    meta: PaginationMeta


# ---------------------------------------------------------------------------
# MusicOutput
# ---------------------------------------------------------------------------

class MusicOutputResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    job_id: UUID
    project_id: UUID
    scene_id: UUID | None = None
    episode_id: UUID | None = None
    output_type: str
    mood: str
    loop_type: str
    storage_key: str
    duration_seconds: float
    sample_rate: int
    format: str
    file_size_bytes: int
    provider: str
    copyright_safe: bool
    status: str
    created_at: datetime


class MusicOutputListResponse(BaseModel):
    items: list[MusicOutputResponse]
    meta: PaginationMeta


# ---------------------------------------------------------------------------
# SoundEffectAsset
# ---------------------------------------------------------------------------

class SFXAssetResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    sfx_key: str
    name: str
    description: str
    category: str
    tags: list[str]
    storage_key: str
    duration_seconds: float
    format: str
    sample_rate: int
    is_builtin: bool
    is_active: bool
    created_at: datetime


class SFXAssetListResponse(BaseModel):
    items: list[SFXAssetResponse]
    meta: PaginationMeta


# ---------------------------------------------------------------------------
# MusicRetryQueue
# ---------------------------------------------------------------------------

class MusicRetryQueueResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    project_id: UUID
    scene_id: UUID | None = None
    episode_id: UUID | None = None
    original_job_id: UUID | None = None
    status: str
    retry_count: int
    max_retries: int
    reason: str
    params: dict[str, Any]
    next_retry_at: datetime | None = None
    created_at: datetime
    updated_at: datetime


class MusicRetryQueueListResponse(BaseModel):
    items: list[MusicRetryQueueResponse]
    meta: PaginationMeta


# ---------------------------------------------------------------------------
# Dashboard
# ---------------------------------------------------------------------------

class MusicDashboardStats(BaseModel):
    total_jobs: int
    jobs_completed: int
    jobs_pending: int
    jobs_failed: int
    jobs_running: int
    total_music_outputs: int
    total_sfx_assets: int
    total_retry_queue: int
    recent_jobs: list[MusicJobResponse]


# ---------------------------------------------------------------------------
# Dispatch / trigger
# ---------------------------------------------------------------------------

class DispatchResponse(BaseModel):
    job_id: UUID
    status: str
    message: str
    dispatch_mode: str


class TriggerMusicTrackRequest(BaseModel):
    """Generate a background music track for a scene or episode."""
    project_id: UUID
    scene_id: UUID | None = None
    episode_id: UUID | None = None
    mood: str = "neutral"       # comedy | adventure | sad | happy | tension | victory | neutral
    duration_seconds: float = 30.0
    loop_type: str = "looping"  # looping | one_shot
    prompt: str = ""
    bpm: int = 0
    instruments: list[str] = []
    output_format: str = "wav"
    extra_params: dict[str, Any] = {}


class TriggerSceneAudioRequest(BaseModel):
    """Generate complete audio (music + SFX) for a scene."""
    project_id: UUID
    scene_id: UUID
    episode_id: UUID | None = None
    mood: str = "neutral"
    duration_seconds: float = 30.0
    output_format: str = "wav"
    include_sfx: bool = True
    sfx_keys: list[str] = []     # specific SFX to mix in
    extra_params: dict[str, Any] = {}

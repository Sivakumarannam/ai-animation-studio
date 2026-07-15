"""
Phase 8 — Voice Engine Pydantic v2 schemas.
Mirrors animation_engine.py schemas shape exactly.
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
# VoiceGenerationJob
# ---------------------------------------------------------------------------

class VoiceJobResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    project_id: UUID
    scene_id: UUID | None = None
    episode_id: UUID | None = None
    character_id: str | None = None
    job_type: str
    status: str
    triggered_by: str
    params: dict[str, Any]
    result: dict[str, Any] | None = None
    error_message: str | None = None
    started_at: datetime | None = None
    completed_at: datetime | None = None
    created_at: datetime
    updated_at: datetime


class VoiceJobListResponse(BaseModel):
    items: list[VoiceJobResponse]
    meta: PaginationMeta


# ---------------------------------------------------------------------------
# VoiceOutput
# ---------------------------------------------------------------------------

class VoiceOutputResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    job_id: UUID
    project_id: UUID
    scene_id: UUID | None = None
    character_id: str | None = None
    character_name: str | None = None
    dialogue_line: str
    language: str
    emotion: str
    voice_id: str | None = None
    storage_key: str
    duration_seconds: float
    sample_rate: int
    format: str
    file_size_bytes: int
    provider: str
    status: str
    metadata: dict[str, Any]
    created_at: datetime


class VoiceOutputListResponse(BaseModel):
    items: list[VoiceOutputResponse]
    meta: PaginationMeta


# ---------------------------------------------------------------------------
# VoiceRetryQueue
# ---------------------------------------------------------------------------

class VoiceRetryQueueResponse(BaseModel):
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


class VoiceRetryQueueListResponse(BaseModel):
    items: list[VoiceRetryQueueResponse]
    meta: PaginationMeta


# ---------------------------------------------------------------------------
# Dashboard
# ---------------------------------------------------------------------------

class VoiceDashboardStats(BaseModel):
    total_jobs: int
    jobs_completed: int
    jobs_pending: int
    jobs_failed: int
    jobs_running: int
    total_voice_outputs: int
    total_retry_queue: int
    recent_jobs: list[VoiceJobResponse]


# ---------------------------------------------------------------------------
# Dispatch response
# ---------------------------------------------------------------------------

class DispatchResponse(BaseModel):
    job_id: UUID
    status: str
    message: str
    dispatch_mode: str


# ---------------------------------------------------------------------------
# Trigger requests
# ---------------------------------------------------------------------------

class TriggerVoiceLineRequest(BaseModel):
    """Generate voice audio for a single dialogue line."""
    project_id: UUID
    scene_id: UUID | None = None
    episode_id: UUID | None = None
    character_id: str = ""
    character_name: str = ""
    dialogue_line: str
    language: str = "en"
    voice_id: str = ""
    emotion: str = "neutral"
    speed: float = 1.0
    pitch: float = 0.0
    output_format: str = "wav"
    voice_seed: int = 0
    extra_params: dict[str, Any] = {}


class SceneDialogueLine(BaseModel):
    """One dialogue line within a scene voice generation request."""
    character_id: str = ""
    character_name: str = ""
    dialogue_line: str
    language: str = "en"
    voice_id: str = ""
    emotion: str = "neutral"
    speed: float = 1.0
    voice_seed: int = 0


class TriggerSceneVoiceRequest(BaseModel):
    """Generate voice audio for all dialogue lines in a scene."""
    project_id: UUID
    scene_id: UUID
    episode_id: UUID | None = None
    dialogue_lines: list[SceneDialogueLine] = []
    output_format: str = "wav"
    extra_params: dict[str, Any] = {}

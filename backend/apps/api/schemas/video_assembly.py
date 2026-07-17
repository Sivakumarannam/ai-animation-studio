"""
Phase 10 — Video Assembly Engine Pydantic schemas.

Mirrors apps/api/schemas/music_engine.py exactly.
"""
from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any

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
# Job
# ---------------------------------------------------------------------------

class VideoAssemblyJobResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    project_id: uuid.UUID
    episode_id: uuid.UUID | None
    job_type: str
    status: str
    mode: str
    triggered_by: str
    params: dict[str, Any]
    result: dict[str, Any] | None
    error_message: str | None
    started_at: datetime | None
    completed_at: datetime | None
    duration_seconds: float | None
    created_at: datetime
    updated_at: datetime


class VideoAssemblyJobListResponse(BaseModel):
    items: list[VideoAssemblyJobResponse]
    meta: PaginationMeta


# ---------------------------------------------------------------------------
# Output
# ---------------------------------------------------------------------------

class VideoOutputResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    job_id: uuid.UUID
    project_id: uuid.UUID
    episode_id: uuid.UUID | None
    output_type: str
    status: str
    storage_key: str
    storage_bucket: str
    file_size_bytes: int
    duration_seconds: float
    width: int
    height: int
    fps: int
    format: str
    provider: str
    scene_count: int
    has_voice: bool
    has_music: bool
    has_subtitles: bool
    quality_passed: bool
    quality_score: float
    output_metadata: dict[str, Any]
    created_at: datetime


class VideoOutputListResponse(BaseModel):
    items: list[VideoOutputResponse]
    meta: PaginationMeta


# ---------------------------------------------------------------------------
# Retry queue
# ---------------------------------------------------------------------------

class VideoRetryQueueResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    project_id: uuid.UUID
    episode_id: uuid.UUID | None
    original_job_id: uuid.UUID | None
    status: str
    retry_count: int
    max_retries: int
    reason: str
    params: dict[str, Any]
    next_retry_at: datetime | None
    created_at: datetime
    updated_at: datetime


class VideoRetryQueueListResponse(BaseModel):
    items: list[VideoRetryQueueResponse]
    meta: PaginationMeta


# ---------------------------------------------------------------------------
# Dashboard stats
# ---------------------------------------------------------------------------

class VideoAssemblyDashboardStats(BaseModel):
    total_jobs: int
    jobs_completed: int
    jobs_pending: int
    jobs_failed: int
    jobs_running: int
    total_video_outputs: int
    total_retry_entries: int
    recent_jobs: list[VideoAssemblyJobResponse]


# ---------------------------------------------------------------------------
# Trigger requests
# ---------------------------------------------------------------------------

class TriggerAssembleEpisodeRequest(BaseModel):
    project_id: uuid.UUID
    episode_id: uuid.UUID | None = None
    output_type: str = "episode_cut"   # "episode_cut" | "short_form_cut"
    width: int = 1920
    height: int = 1080
    fps: int = 24
    include_subtitles: bool = False
    triggered_by: str = "api"


class TriggerRetryQueueRequest(BaseModel):
    project_id: uuid.UUID
    limit: int = 10


# ---------------------------------------------------------------------------
# Dispatch response
# ---------------------------------------------------------------------------

class DispatchResponse(BaseModel):
    job_id: str
    task_id: str
    mode: str
    status: str

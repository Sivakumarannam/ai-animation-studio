"""
Phase 7 — Animation Engine API schemas.
"""
from __future__ import annotations

from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel


# ---------------------------------------------------------------------------
# Shared
# ---------------------------------------------------------------------------

class PaginationMeta(BaseModel):
    total: int
    page: int
    page_size: int
    total_pages: int


# ---------------------------------------------------------------------------
# AnimationJob schemas
# ---------------------------------------------------------------------------

class AnimationJobResponse(BaseModel):
    id: UUID
    project_id: UUID
    scene_id: UUID | None
    episode_id: UUID | None
    job_type: str
    status: str
    mode: str
    triggered_by: str
    params: dict[str, Any]
    result: dict[str, Any]
    error_message: str
    started_at: datetime | None
    completed_at: datetime | None
    duration_seconds: float | None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class AnimationJobListResponse(BaseModel):
    items: list[AnimationJobResponse]
    meta: PaginationMeta


# ---------------------------------------------------------------------------
# AnimationRenderOutput schemas
# ---------------------------------------------------------------------------

class AnimationRenderOutputResponse(BaseModel):
    id: UUID
    job_id: UUID
    project_id: UUID
    scene_id: UUID | None
    episode_id: UUID | None
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
    render_params: dict[str, Any]
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class AnimationRenderOutputListResponse(BaseModel):
    items: list[AnimationRenderOutputResponse]
    meta: PaginationMeta


# ---------------------------------------------------------------------------
# AnimationRetryQueue schemas
# ---------------------------------------------------------------------------

class AnimationRetryQueueResponse(BaseModel):
    id: UUID
    project_id: UUID
    scene_id: UUID | None
    episode_id: UUID | None
    original_job_id: UUID | None
    retry_count: int
    max_retries: int
    status: str
    reason: str
    next_retry_at: datetime | None
    resolved_at: datetime | None
    params: dict[str, Any]
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class AnimationRetryQueueListResponse(BaseModel):
    items: list[AnimationRetryQueueResponse]
    meta: PaginationMeta


# ---------------------------------------------------------------------------
# Dashboard
# ---------------------------------------------------------------------------

class AnimationDashboardStats(BaseModel):
    total_jobs: int
    jobs_completed: int
    jobs_pending: int
    jobs_failed: int
    jobs_running: int
    total_render_outputs: int
    total_retry_queue: int
    recent_jobs: list[AnimationJobResponse]


# ---------------------------------------------------------------------------
# Trigger requests
# ---------------------------------------------------------------------------

class TriggerSceneAnimationRequest(BaseModel):
    project_id: UUID
    scene_id: UUID
    episode_id: UUID | None = None
    duration_seconds: float = 5.0
    fps: int = 24
    width: int = 1920
    height: int = 1080
    camera_motion: str = "static"
    # Character data: [{character_id, asset_storage_key, position_x, position_y, scale, expression, pose}]
    characters: list[dict[str, Any]] = []
    background_storage_key: str = ""
    dialogue_segments: list[dict[str, Any]] = []
    extra_params: dict[str, Any] = {}


class TriggerEpisodeAnimationRequest(BaseModel):
    project_id: UUID
    episode_id: UUID
    scene_ids: list[UUID] = []
    fps: int = 24
    width: int = 1920
    height: int = 1080
    force_re_render: bool = False


class DispatchResponse(BaseModel):
    job_id: UUID
    status: str
    message: str
    dispatch_mode: str

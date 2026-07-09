"""
Phase 6 — AI Asset Generation Engine API schemas.
"""
from __future__ import annotations

from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, Field


# ---------------------------------------------------------------------------
# Shared
# ---------------------------------------------------------------------------

class PaginationMeta(BaseModel):
    total: int
    page: int
    page_size: int
    total_pages: int


# ---------------------------------------------------------------------------
# AssetProject
# ---------------------------------------------------------------------------

class AssetProjectCreate(BaseModel):
    project_id: UUID
    name: str = ""
    description: str = ""
    quality_threshold: float = 90.0
    max_retries: int = 3
    target_resolution: str = "1024x1024"
    config: dict[str, Any] = Field(default_factory=dict)


class AssetProjectUpdate(BaseModel):
    name: str | None = None
    description: str | None = None
    quality_threshold: float | None = None
    max_retries: int | None = None
    target_resolution: str | None = None
    config: dict[str, Any] | None = None


class AssetProjectResponse(BaseModel):
    id: UUID
    project_id: UUID
    name: str
    description: str
    quality_threshold: float
    max_retries: int
    target_resolution: str
    is_active: bool
    total_assets_generated: int
    total_retries: int
    avg_quality_score: float
    storage_bytes_used: int
    config: dict[str, Any]
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class AssetProjectListResponse(BaseModel):
    items: list[AssetProjectResponse]
    meta: PaginationMeta


# ---------------------------------------------------------------------------
# AssetStyle
# ---------------------------------------------------------------------------

class AssetStyleCreate(BaseModel):
    name: str
    slug: str
    description: str = ""
    style_prompt: str = ""
    negative_prompt: str = ""
    keywords: list[str] = Field(default_factory=list)
    color_palette: list[str] = Field(default_factory=list)
    reference_artists: list[str] = Field(default_factory=list)
    style_type: str = "2d_cartoon"


class AssetStyleResponse(BaseModel):
    id: UUID
    name: str
    slug: str
    description: str
    style_prompt: str
    negative_prompt: str
    keywords: list[str]
    color_palette: list[str]
    reference_artists: list[str]
    style_type: str
    is_default: bool
    is_active: bool
    usage_count: int
    avg_quality_score: float
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class AssetStyleListResponse(BaseModel):
    items: list[AssetStyleResponse]
    meta: PaginationMeta


# ---------------------------------------------------------------------------
# AssetCollection
# ---------------------------------------------------------------------------

class AssetCollectionCreate(BaseModel):
    project_id: UUID
    name: str
    description: str = ""
    collection_type: str = "mixed"
    tags: list[str] = Field(default_factory=list)


class AssetCollectionResponse(BaseModel):
    id: UUID
    project_id: UUID
    name: str
    description: str
    collection_type: str
    asset_count: int
    is_active: bool
    tags: list[str]
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class AssetCollectionListResponse(BaseModel):
    items: list[AssetCollectionResponse]
    meta: PaginationMeta


# ---------------------------------------------------------------------------
# Asset
# ---------------------------------------------------------------------------

class AssetCreate(BaseModel):
    project_id: UUID
    name: str
    description: str = ""
    asset_type: str
    collection_id: UUID | None = None
    style_id: UUID | None = None
    character_id: UUID | None = None
    episode_id: UUID | None = None
    scene_id: UUID | None = None
    tags: list[str] = Field(default_factory=list)
    generation_params: dict[str, Any] = Field(default_factory=dict)


class AssetResponse(BaseModel):
    id: UUID
    project_id: UUID
    collection_id: UUID | None
    style_id: UUID | None
    character_id: UUID | None
    episode_id: UUID | None
    scene_id: UUID | None
    name: str
    description: str
    asset_type: str
    status: str
    version_count: int
    retry_count: int
    max_retries: int
    quality_score: float
    quality_threshold: float
    storage_key: str
    width: int
    height: int
    file_size_bytes: int
    mime_type: str
    tags: list[str]
    generation_params: dict[str, Any]
    generated_at: datetime | None
    is_deleted: bool
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class AssetListResponse(BaseModel):
    items: list[AssetResponse]
    meta: PaginationMeta


# ---------------------------------------------------------------------------
# AssetVersion
# ---------------------------------------------------------------------------

class AssetVersionResponse(BaseModel):
    id: UUID
    asset_id: UUID
    version_number: int
    version_label: str
    storage_key: str
    width: int
    height: int
    file_size_bytes: int
    quality_score: float
    is_approved: bool
    is_rejected: bool
    rejection_reason: str
    generation_seed: int
    generation_steps: int
    cfg_scale: float
    sampler: str
    generation_params: dict[str, Any]
    evaluation_scores: dict[str, Any]
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class AssetVersionListResponse(BaseModel):
    items: list[AssetVersionResponse]
    meta: PaginationMeta


# ---------------------------------------------------------------------------
# AssetPrompt
# ---------------------------------------------------------------------------

class AssetPromptResponse(BaseModel):
    id: UUID
    asset_id: UUID | None
    positive_prompt: str
    negative_prompt: str
    style_prompt: str
    camera_prompt: str
    composition_prompt: str
    lighting_prompt: str
    color_prompt: str
    consistency_prompt: str
    full_prompt: str
    full_negative_prompt: str
    prompt_type: str
    quality_score: float
    was_successful: bool
    use_count: int
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class AssetPromptListResponse(BaseModel):
    items: list[AssetPromptResponse]
    meta: PaginationMeta


# ---------------------------------------------------------------------------
# AssetEvaluation
# ---------------------------------------------------------------------------

class AssetEvaluationResponse(BaseModel):
    id: UUID
    asset_id: UUID
    version_id: UUID | None
    overall_score: float
    prompt_quality: float
    image_quality: float
    character_consistency: float
    background_consistency: float
    composition_score: float
    lighting_score: float
    style_match: float
    scene_match: float
    resolution_score: float
    artifact_score: float
    hands_score: float
    face_score: float
    text_error_score: float
    passed_threshold: bool
    failure_reasons: list[str]
    notes: str
    evaluated_by: str
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class AssetEvaluationListResponse(BaseModel):
    items: list[AssetEvaluationResponse]
    meta: PaginationMeta


# ---------------------------------------------------------------------------
# GenerationJob
# ---------------------------------------------------------------------------

class GenerationJobResponse(BaseModel):
    id: UUID
    project_id: UUID | None
    asset_id: UUID | None
    episode_id: UUID | None
    job_type: str
    status: str
    dispatch_mode: str
    celery_task_id: str
    result: dict[str, Any]
    error_message: str
    started_at: datetime | None
    completed_at: datetime | None
    duration_ms: int
    retry_count: int
    max_retries: int
    params: dict[str, Any]
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class GenerationJobListResponse(BaseModel):
    items: list[GenerationJobResponse]
    meta: PaginationMeta


# ---------------------------------------------------------------------------
# RetryQueue
# ---------------------------------------------------------------------------

class RetryQueueResponse(BaseModel):
    id: UUID
    asset_id: UUID
    project_id: UUID
    failure_reason: str
    failure_details: str
    quality_score: float
    retry_count: int
    max_retries: int
    status: str
    priority: int
    last_retry_at: datetime | None
    resolved_at: datetime | None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class RetryQueueListResponse(BaseModel):
    items: list[RetryQueueResponse]
    meta: PaginationMeta


# ---------------------------------------------------------------------------
# SceneComposition
# ---------------------------------------------------------------------------

class SceneCompositionResponse(BaseModel):
    id: UUID
    project_id: UUID
    scene_id: UUID | None
    episode_id: UUID | None
    name: str
    description: str
    composition_type: str
    foreground_elements: list[str]
    midground_elements: list[str]
    background_elements: list[str]
    focus_point: str
    lighting_direction: str
    color_harmony: str
    negative_space: float
    composition_prompt: str
    layout_data: dict[str, Any]
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class SceneCompositionListResponse(BaseModel):
    items: list[SceneCompositionResponse]
    meta: PaginationMeta


# ---------------------------------------------------------------------------
# CameraShot
# ---------------------------------------------------------------------------

class CameraShotResponse(BaseModel):
    id: UUID
    composition_id: UUID | None
    scene_id: UUID | None
    episode_id: UUID | None
    shot_type: str
    shot_order: int
    description: str
    camera_movement: str
    focal_length: str
    depth_of_field: str
    camera_prompt: str
    asset_id: UUID | None
    quality_score: float
    shot_data: dict[str, Any]
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class CameraShotListResponse(BaseModel):
    items: list[CameraShotResponse]
    meta: PaginationMeta


# ---------------------------------------------------------------------------
# Presets
# ---------------------------------------------------------------------------

class LightingPresetResponse(BaseModel):
    id: UUID
    name: str
    slug: str
    description: str
    lighting_type: str
    lighting_prompt: str
    time_of_day: str
    weather: str
    intensity: float
    color_temperature: str
    is_active: bool
    use_count: int
    avg_quality_score: float
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class LightingPresetListResponse(BaseModel):
    items: list[LightingPresetResponse]
    meta: PaginationMeta


class PosePresetResponse(BaseModel):
    id: UUID
    name: str
    slug: str
    description: str
    pose_type: str
    pose_prompt: str
    body_orientation: str
    is_active: bool
    use_count: int
    avg_quality_score: float
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class PosePresetListResponse(BaseModel):
    items: list[PosePresetResponse]
    meta: PaginationMeta


class ExpressionPresetResponse(BaseModel):
    id: UUID
    name: str
    slug: str
    description: str
    expression_type: str
    expression_prompt: str
    intensity: float
    is_active: bool
    use_count: int
    avg_quality_score: float
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class ExpressionPresetListResponse(BaseModel):
    items: list[ExpressionPresetResponse]
    meta: PaginationMeta


# ---------------------------------------------------------------------------
# GenerationHistory
# ---------------------------------------------------------------------------

class GenerationHistoryResponse(BaseModel):
    id: UUID
    project_id: UUID
    episode_id: UUID | None
    run_type: str
    triggered_by: str
    assets_planned: int
    assets_generated: int
    assets_accepted: int
    assets_rejected: int
    retries_count: int
    avg_quality_score: float
    duration_seconds: float
    run_status: str
    error_summary: str
    started_at: datetime | None
    finished_at: datetime | None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class GenerationHistoryListResponse(BaseModel):
    items: list[GenerationHistoryResponse]
    meta: PaginationMeta


# ---------------------------------------------------------------------------
# Dispatch / Trigger
# ---------------------------------------------------------------------------

class TriggerEpisodeGenerationRequest(BaseModel):
    episode_id: UUID
    project_id: UUID
    asset_types: list[str] = Field(
        default_factory=lambda: [
            "character", "character_expression", "character_pose",
            "background", "prop", "scene_layout"
        ]
    )
    quality_threshold: float = 90.0
    max_retries: int = 3
    force_regenerate: bool = False


class TriggerAssetGenerationRequest(BaseModel):
    asset_id: UUID
    force_regenerate: bool = False
    custom_params: dict[str, Any] = Field(default_factory=dict)


class DispatchResponse(BaseModel):
    job_id: UUID
    status: str
    message: str
    dispatch_mode: str


# ---------------------------------------------------------------------------
# Search
# ---------------------------------------------------------------------------

class AssetSearchRequest(BaseModel):
    query: str = ""
    asset_type: str | None = None
    project_id: UUID | None = None
    collection_id: UUID | None = None
    character_id: UUID | None = None
    episode_id: UUID | None = None
    tags: list[str] = Field(default_factory=list)
    min_quality: float = 0.0
    status: str | None = None
    limit: int = Field(20, ge=1, le=100)
    offset: int = Field(0, ge=0)


class AssetSearchResponse(BaseModel):
    items: list[AssetResponse]
    total: int
    query: str


# ---------------------------------------------------------------------------
# Dashboard
# ---------------------------------------------------------------------------

class AssetDashboardStats(BaseModel):
    total_assets: int
    assets_completed: int
    assets_pending: int
    assets_failed: int
    assets_generating: int
    total_retries: int
    avg_quality_score: float
    assets_by_type: dict[str, int]
    recent_jobs: list[GenerationJobResponse]
    storage_bytes_used: int
    generation_history_7d: list[dict[str, Any]]


# ---------------------------------------------------------------------------
# AssetMemory
# ---------------------------------------------------------------------------

class AssetMemoryResponse(BaseModel):
    id: UUID
    project_id: UUID
    memory_type: str
    scope: str
    key: str
    value: dict[str, Any]
    confidence: float
    use_count: int
    last_used_at: datetime | None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class AssetMemoryListResponse(BaseModel):
    items: list[AssetMemoryResponse]
    meta: PaginationMeta

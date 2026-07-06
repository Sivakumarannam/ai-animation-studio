"""
Phase 3 — Story Intelligence Pydantic schemas.
All request/response models for the /si (story-intelligence) API.
"""
from __future__ import annotations

from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, Field


# ─────────────────────────────────────────────────────────────────────────────
# Shared
# ─────────────────────────────────────────────────────────────────────────────

class PaginationMeta(BaseModel):
    page: int
    page_size: int
    total: int
    total_pages: int


# ─────────────────────────────────────────────────────────────────────────────
# World
# ─────────────────────────────────────────────────────────────────────────────

class WorldCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=500)
    description: str = ""
    rules: list[Any] = []
    locations: dict[str, Any] = {}
    timeline_data: list[Any] = []
    factions: list[Any] = []
    objects: list[Any] = []
    lore: str = ""


class WorldUpdate(BaseModel):
    name: str | None = None
    description: str | None = None
    rules: list[Any] | None = None
    locations: dict[str, Any] | None = None
    timeline_data: list[Any] | None = None
    factions: list[Any] | None = None
    objects: list[Any] | None = None
    lore: str | None = None
    status: str | None = None


class WorldResponse(BaseModel):
    id: UUID
    project_id: UUID
    name: str
    description: str
    rules: list[Any]
    locations: dict[str, Any]
    timeline_data: list[Any]
    factions: list[Any]
    objects: list[Any]
    lore: str
    status: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class WorldListResponse(BaseModel):
    items: list[WorldResponse]
    meta: PaginationMeta


# ─────────────────────────────────────────────────────────────────────────────
# Season
# ─────────────────────────────────────────────────────────────────────────────

class SeasonCreate(BaseModel):
    title: str = Field(..., min_length=1, max_length=500)
    description: str = ""
    story_arc: str = ""
    season_number: int | None = None
    episode_count: int = 10


class SeasonUpdate(BaseModel):
    title: str | None = None
    description: str | None = None
    story_arc: str | None = None
    status: str | None = None
    episode_count: int | None = None


class SeasonResponse(BaseModel):
    id: UUID
    world_id: UUID
    project_id: UUID
    season_number: int
    title: str
    description: str
    story_arc: str
    status: str
    episode_count: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class SeasonListResponse(BaseModel):
    items: list[SeasonResponse]
    meta: PaginationMeta


# ─────────────────────────────────────────────────────────────────────────────
# Episode
# ─────────────────────────────────────────────────────────────────────────────

class EpisodeCreate(BaseModel):
    title: str = Field(..., min_length=1, max_length=500)
    summary: str = ""
    opening: str = ""
    middle: str = ""
    ending: str = ""
    moral: str = ""
    episode_number: int | None = None
    duration_target_seconds: int = 300


class EpisodeUpdate(BaseModel):
    title: str | None = None
    summary: str | None = None
    opening: str | None = None
    middle: str | None = None
    ending: str | None = None
    moral: str | None = None
    status: str | None = None
    duration_target_seconds: int | None = None


class EpisodeResponse(BaseModel):
    id: UUID
    season_id: UUID
    world_id: UUID
    project_id: UUID
    episode_number: int
    title: str
    summary: str
    opening: str
    middle: str
    ending: str
    moral: str
    duration_target_seconds: int
    story_score: float
    status: str
    generation_metadata: dict[str, Any]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class EpisodeListResponse(BaseModel):
    items: list[EpisodeResponse]
    meta: PaginationMeta


# ─────────────────────────────────────────────────────────────────────────────
# StoryScene
# ─────────────────────────────────────────────────────────────────────────────

class StorySceneCreate(BaseModel):
    scene_number: int
    scene_goal: str = ""
    location: str = ""
    character_names: list[str] = []
    dialogue: list[Any] = []
    narration: str = ""
    image_prompt: str = ""
    animation_prompt: str = ""
    camera_direction: str = ""
    duration_seconds: float = 60.0


class StorySceneUpdate(BaseModel):
    scene_goal: str | None = None
    location: str | None = None
    character_names: list[str] | None = None
    dialogue: list[Any] | None = None
    narration: str | None = None
    image_prompt: str | None = None
    animation_prompt: str | None = None
    camera_direction: str | None = None
    duration_seconds: float | None = None
    status: str | None = None


class StorySceneResponse(BaseModel):
    id: UUID
    episode_id: UUID
    scene_number: int
    scene_goal: str
    location: str
    character_names: list[str]
    dialogue: list[Any]
    narration: str
    image_prompt: str
    animation_prompt: str
    camera_direction: str
    duration_seconds: float
    status: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class StorySceneListResponse(BaseModel):
    items: list[StorySceneResponse]
    meta: PaginationMeta


# ─────────────────────────────────────────────────────────────────────────────
# StoryIdea
# ─────────────────────────────────────────────────────────────────────────────

class StoryIdeaCreate(BaseModel):
    title: str = Field(..., min_length=1, max_length=500)
    premise: str = ""
    genre: str = "comedy"
    tone: str = "light"
    story_type: str = "comedy"
    target_audience: str = "general"
    estimated_episodes: int = 3
    world_id: UUID | None = None


class GenerateIdeasRequest(BaseModel):
    genre: str = "comedy"
    story_type: str = "comedy"
    count: int = Field(default=3, ge=1, le=10)
    world_id: UUID | None = None


class StoryIdeaUpdate(BaseModel):
    status: str | None = None
    title: str | None = None
    premise: str | None = None


class StoryIdeaResponse(BaseModel):
    id: UUID
    project_id: UUID
    world_id: UUID | None
    title: str
    premise: str
    genre: str
    tone: str
    story_type: str
    target_audience: str
    estimated_episodes: int
    status: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class StoryIdeaListResponse(BaseModel):
    items: list[StoryIdeaResponse]
    meta: PaginationMeta


# ─────────────────────────────────────────────────────────────────────────────
# StoryMemory
# ─────────────────────────────────────────────────────────────────────────────

class StoryMemoryCreate(BaseModel):
    memory_type: str
    key: str = Field(..., min_length=1, max_length=500)
    value: dict[str, Any]
    episode_id: UUID | None = None


class StoryMemoryResponse(BaseModel):
    id: UUID
    world_id: UUID
    memory_type: str
    key: str
    value: dict[str, Any]
    episode_id: UUID | None
    is_active: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class StoryMemoryListResponse(BaseModel):
    items: list[StoryMemoryResponse]
    meta: PaginationMeta


# ─────────────────────────────────────────────────────────────────────────────
# StoryEvaluation
# ─────────────────────────────────────────────────────────────────────────────

class StoryEvaluationResponse(BaseModel):
    id: UUID
    episode_id: UUID
    evaluator_version: str
    originality_score: float
    consistency_score: float
    creativity_score: float
    grammar_score: float
    flow_score: float
    entertainment_score: float
    educational_value_score: float
    story_arc_score: float
    dialogue_score: float
    overall_score: float
    feedback: dict[str, Any]
    approved: bool
    evaluated_at: datetime
    created_at: datetime

    class Config:
        from_attributes = True


# ─────────────────────────────────────────────────────────────────────────────
# GenerationJob
# ─────────────────────────────────────────────────────────────────────────────

class GenerationJobResponse(BaseModel):
    id: UUID
    project_id: UUID | None
    job_type: str
    entity_type: str
    entity_id: UUID | None
    status: str
    celery_task_id: str
    execution_mode: str
    progress_percent: int
    current_step: str
    result: dict[str, Any]
    error_message: str
    retry_count: int
    max_retries: int
    started_at: datetime | None
    completed_at: datetime | None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class GenerationJobListResponse(BaseModel):
    items: list[GenerationJobResponse]
    meta: PaginationMeta


# ─────────────────────────────────────────────────────────────────────────────
# Pipeline / Generation requests
# ─────────────────────────────────────────────────────────────────────────────

class RunFullPipelineRequest(BaseModel):
    genre: str = "comedy"
    story_type: str = "comedy"
    episode_count: int | None = None
    world_id: UUID | None = None
    world_data: dict[str, Any] = {}
    knowledge_collection_id: UUID | None = None


class GenerateEpisodeRequest(BaseModel):
    season_id: UUID
    world_id: UUID
    knowledge_collection_id: UUID | None = None


class DispatchResponse(BaseModel):
    job_id: str
    task_id: str
    mode: str   # "async" or "sync"
    status: str
    result: dict[str, Any] | None = None


# ─────────────────────────────────────────────────────────────────────────────
# Analytics / Stats
# ─────────────────────────────────────────────────────────────────────────────

class StoryIntelligenceStats(BaseModel):
    worlds: int
    seasons: int
    episodes: int
    scenes: int
    ideas: int
    memories: int
    jobs_by_status: dict[str, int]
    avg_story_score: float


class StoryVersionResponse(BaseModel):
    id: UUID
    entity_type: str
    entity_id: UUID
    version_number: int
    snapshot: dict[str, Any]
    change_summary: str
    created_by: str
    created_at: datetime

    class Config:
        from_attributes = True

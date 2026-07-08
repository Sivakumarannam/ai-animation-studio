"""
Phase 5 — Research & Trend Intelligence Engine Pydantic schemas.
All request/response models for the /rs (research) API.
"""
from __future__ import annotations

from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, Field

from apps.api.schemas.intelligence import PaginationMeta


# ─────────────────────────────────────────────────────────────────────────────
# Source
# ─────────────────────────────────────────────────────────────────────────────

class ResearchSourceCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=500)
    source_type: str = Field(..., min_length=1, max_length=100)
    url: str = ""
    description: str = ""
    fetch_interval_seconds: int = 3600
    config: dict[str, Any] = {}


class ResearchSourceResponse(BaseModel):
    id: UUID
    name: str
    source_type: str
    url: str
    description: str
    is_active: bool
    fetch_interval_seconds: int
    fetch_count: int
    error_count: int
    last_fetched_at: datetime | None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class ResearchSourceListResponse(BaseModel):
    items: list[ResearchSourceResponse]
    meta: PaginationMeta


# ─────────────────────────────────────────────────────────────────────────────
# Trend
# ─────────────────────────────────────────────────────────────────────────────

class ResearchTrendResponse(BaseModel):
    id: UUID
    keyword: str
    normalized_keyword: str
    category: str
    region: str
    language: str
    trend_score: float
    velocity: float
    growth_rate: float
    popularity_index: float
    is_emerging: bool
    is_declining: bool
    status: str
    discovered_at: datetime | None
    created_at: datetime

    class Config:
        from_attributes = True


class ResearchTrendListResponse(BaseModel):
    items: list[ResearchTrendResponse]
    meta: PaginationMeta


# ─────────────────────────────────────────────────────────────────────────────
# Topic
# ─────────────────────────────────────────────────────────────────────────────

class ResearchTopicCreate(BaseModel):
    canonical_name: str = Field(..., min_length=1, max_length=500)
    description: str = ""
    keywords: list[str] = []
    categories: list[str] = []
    language: str = "en"


class ResearchTopicResponse(BaseModel):
    id: UUID
    canonical_name: str
    slug: str
    description: str
    keywords: list[str]
    categories: list[str]
    language: str
    status: str
    research_status: str
    trend_score: float
    research_quality: float
    fact_confidence: float
    opportunity_score: float
    article_count: int
    fact_count: int
    researched_at: datetime | None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class ResearchTopicListResponse(BaseModel):
    items: list[ResearchTopicResponse]
    meta: PaginationMeta


# ─────────────────────────────────────────────────────────────────────────────
# Cluster
# ─────────────────────────────────────────────────────────────────────────────

class ResearchClusterResponse(BaseModel):
    id: UUID
    canonical_name: str
    description: str
    keywords: list[str]
    categories: list[str]
    topic_ids: list[str]
    topic_count: int
    confidence: float
    avg_opportunity_score: float
    status: str
    created_at: datetime

    class Config:
        from_attributes = True


class ResearchClusterListResponse(BaseModel):
    items: list[ResearchClusterResponse]
    meta: PaginationMeta


# ─────────────────────────────────────────────────────────────────────────────
# Article
# ─────────────────────────────────────────────────────────────────────────────

class ResearchArticleResponse(BaseModel):
    id: UUID
    topic_id: UUID
    title: str
    url: str
    summary: str
    author: str
    published_at: datetime | None
    source_type: str
    language: str
    quality_score: float
    relevance_score: float
    status: str
    created_at: datetime

    class Config:
        from_attributes = True


class ResearchArticleListResponse(BaseModel):
    items: list[ResearchArticleResponse]
    meta: PaginationMeta


# ─────────────────────────────────────────────────────────────────────────────
# Fact
# ─────────────────────────────────────────────────────────────────────────────

class ResearchFactResponse(BaseModel):
    id: UUID
    topic_id: UUID
    fact_type: str
    statement: str
    confidence: float
    supporting_sources: list[str]
    conflicting_sources: list[str]
    citations: list[dict[str, Any]]
    is_verified: bool
    is_rejected: bool
    rejection_reason: str
    verification_count: int
    created_at: datetime

    class Config:
        from_attributes = True


class ResearchFactListResponse(BaseModel):
    items: list[ResearchFactResponse]
    meta: PaginationMeta


# ─────────────────────────────────────────────────────────────────────────────
# Entity
# ─────────────────────────────────────────────────────────────────────────────

class ResearchEntityResponse(BaseModel):
    id: UUID
    topic_id: UUID
    entity_type: str
    name: str
    normalized_name: str
    description: str
    attributes: dict[str, Any]
    confidence: float
    wikidata_id: str
    wikipedia_url: str
    occurrence_count: int
    created_at: datetime

    class Config:
        from_attributes = True


# ─────────────────────────────────────────────────────────────────────────────
# Score
# ─────────────────────────────────────────────────────────────────────────────

class ResearchScoreResponse(BaseModel):
    id: UUID
    topic_id: UUID
    trend_score: float
    research_quality: float
    fact_confidence: float
    competition_score: float
    novelty_score: float
    audience_fit: float
    seasonality_score: float
    educational_value: float
    entertainment_value: float
    overall_score: float
    breakdown: dict[str, Any]
    scored_at: datetime | None
    created_at: datetime

    class Config:
        from_attributes = True


# ─────────────────────────────────────────────────────────────────────────────
# Queue
# ─────────────────────────────────────────────────────────────────────────────

class ResearchQueueResponse(BaseModel):
    id: UUID
    topic_id: UUID
    project_id: UUID | None
    priority: int
    status: str
    overall_score: float
    research_summary: dict[str, Any]
    queued_at: datetime | None
    processed_at: datetime | None
    error_message: str
    retry_count: int
    created_at: datetime

    class Config:
        from_attributes = True


class ResearchQueueListResponse(BaseModel):
    items: list[ResearchQueueResponse]
    meta: PaginationMeta


# ─────────────────────────────────────────────────────────────────────────────
# Job
# ─────────────────────────────────────────────────────────────────────────────

class ResearchJobResponse(BaseModel):
    id: UUID
    job_type: str
    status: str
    topic_id: UUID | None
    execution_mode: str
    progress_percent: int
    current_step: str
    result: dict[str, Any]
    error_message: str
    retry_count: int
    started_at: datetime | None
    completed_at: datetime | None
    created_at: datetime

    class Config:
        from_attributes = True


class ResearchJobListResponse(BaseModel):
    items: list[ResearchJobResponse]
    meta: PaginationMeta


# ─────────────────────────────────────────────────────────────────────────────
# History
# ─────────────────────────────────────────────────────────────────────────────

class ResearchHistoryResponse(BaseModel):
    id: UUID
    run_type: str
    status: str
    trends_discovered: int
    topics_researched: int
    facts_verified: int
    opportunities_scored: int
    knowledge_docs_created: int
    duration_seconds: float
    error_message: str
    triggered_by: str
    created_at: datetime

    class Config:
        from_attributes = True


class ResearchHistoryListResponse(BaseModel):
    items: list[ResearchHistoryResponse]
    meta: PaginationMeta


# ─────────────────────────────────────────────────────────────────────────────
# Dashboard / Stats
# ─────────────────────────────────────────────────────────────────────────────

class ResearchDashboardStats(BaseModel):
    active_trends: int
    emerging_trends: int
    total_topics: int
    topics_by_status: dict[str, int]
    researched_topics: int
    verified_facts: int
    knowledge_docs_created: int
    queue_pending: int
    jobs_by_status: dict[str, int]
    scheduler_status: dict[str, Any]
    top_trends: list[ResearchTrendResponse]
    top_opportunities: list[ResearchTopicResponse]


# ─────────────────────────────────────────────────────────────────────────────
# Scheduler
# ─────────────────────────────────────────────────────────────────────────────

class SchedulerStatusResponse(BaseModel):
    phases: dict[str, Any]


class SchedulerTriggerRequest(BaseModel):
    phase: str = Field(..., description="One of: trend_discovery, research_refresh, opportunity_report")


class DispatchResponse(BaseModel):
    job_id: str
    task_id: str
    mode: str
    status: str
    result: dict[str, Any] | None = None


# ─────────────────────────────────────────────────────────────────────────────
# Analytics
# ─────────────────────────────────────────────────────────────────────────────

class ResearchAnalyticsResponse(BaseModel):
    id: UUID
    period_type: str
    period_start: datetime
    period_end: datetime
    total_trends: int
    active_trends: int
    emerging_trends: int
    total_topics: int
    researched_topics: int
    verified_facts: int
    knowledge_docs_created: int
    opportunities_scored: int
    avg_opportunity_score: float
    top_categories: list[str]
    top_keywords: list[str]
    created_at: datetime

    class Config:
        from_attributes = True

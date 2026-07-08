"""
Phase 5 — AI Research & Trend Intelligence Engine database models.

All tables are prefixed with `rs_` (Research) to avoid collisions with
Phase 1/2/3/4 tables.

Hierarchy:
  ResearchSource (rs_sources)            — configured data sources
  ResearchTrend  (rs_trends)             — raw discovered trends
  ResearchTopic  (rs_topics)             — normalised topics
  ResearchCluster (rs_clusters)          — clustered topic groups
  ResearchArticle (rs_articles)          — fetched articles per topic
  ResearchFact    (rs_facts)             — extracted facts
  ResearchEntity  (rs_entities)          — people, places, dates, events, stats
  ResearchScore   (rs_scores)            — opportunity scores
  ResearchQueue   (rs_queue)             — story generation queue
  ResearchJob     (rs_jobs)              — async pipeline job tracking
  ResearchHistory (rs_history)           — scheduler run log
  ResearchMemory  (rs_memory)            — persistent research memory
  ResearchVersion (rs_versions)          — snapshot store
  ResearchAnalytics (rs_analytics)       — aggregated analytics
"""
from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any

from sqlalchemy import (
    Boolean,
    DateTime,
    Float,
    ForeignKey,
    Index,
    Integer,
    JSON,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from database.base import Base, TimestampMixin, UUIDMixin


# ---------------------------------------------------------------------------
# ResearchSource
# ---------------------------------------------------------------------------

class ResearchSource(UUIDMixin, TimestampMixin, Base):
    """A configured data source (RSS feed, Wikipedia, Google Trends, etc.)."""
    __tablename__ = "rs_sources"

    name: Mapped[str] = mapped_column(String(500), nullable=False)
    source_type: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    # "rss" | "wikipedia" | "google_trends" | "wikidata" | "youtube_rss"
    # "open_government" | "internet_archive" | "common_crawl" | "news_rss"
    url: Mapped[str] = mapped_column(String(2000), nullable=False, default="")
    description: Mapped[str] = mapped_column(Text, nullable=False, default="")
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True, index=True)
    fetch_interval_seconds: Mapped[int] = mapped_column(Integer, nullable=False, default=3600)
    last_fetched_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    fetch_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    error_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    last_error: Mapped[str] = mapped_column(Text, nullable=False, default="")
    config: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False, default=dict)
    metadata_: Mapped[dict[str, Any]] = mapped_column("rs_metadata", JSON, nullable=False, default=dict)

    __table_args__ = (
        Index("ix_rs_sources_type_active", "source_type", "is_active"),
    )


# ---------------------------------------------------------------------------
# ResearchTrend
# ---------------------------------------------------------------------------

class ResearchTrend(UUIDMixin, TimestampMixin, Base):
    """A single raw trending signal from a source."""
    __tablename__ = "rs_trends"

    source_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("rs_sources.id", ondelete="SET NULL"),
        nullable=True, index=True
    )
    keyword: Mapped[str] = mapped_column(String(500), nullable=False, index=True)
    normalized_keyword: Mapped[str] = mapped_column(String(500), nullable=False, index=True)
    category: Mapped[str] = mapped_column(String(200), nullable=False, default="general")
    region: Mapped[str] = mapped_column(String(100), nullable=False, default="global")
    language: Mapped[str] = mapped_column(String(20), nullable=False, default="en")
    trend_score: Mapped[float] = mapped_column(Float, nullable=False, default=0.0, index=True)
    velocity: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    growth_rate: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    popularity_index: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    is_emerging: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False, index=True)
    is_declining: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    status: Mapped[str] = mapped_column(String(50), nullable=False, default="active", index=True)
    # "active" | "archived" | "merged"
    raw_data: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False, default=dict)
    discovered_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    __table_args__ = (
        Index("ix_rs_trends_keyword_status", "normalized_keyword", "status"),
        Index("ix_rs_trends_score_emerging", "trend_score", "is_emerging"),
    )


# ---------------------------------------------------------------------------
# ResearchTopic
# ---------------------------------------------------------------------------

class ResearchTopic(UUIDMixin, TimestampMixin, Base):
    """A normalised, deduplicated topic ready for research."""
    __tablename__ = "rs_topics"

    canonical_name: Mapped[str] = mapped_column(String(500), nullable=False, index=True)
    slug: Mapped[str] = mapped_column(String(500), nullable=False, unique=True, index=True)
    description: Mapped[str] = mapped_column(Text, nullable=False, default="")
    keywords: Mapped[list[str]] = mapped_column(JSON, nullable=False, default=list)
    categories: Mapped[list[str]] = mapped_column(JSON, nullable=False, default=list)
    language: Mapped[str] = mapped_column(String(20), nullable=False, default="en")
    status: Mapped[str] = mapped_column(String(50), nullable=False, default="discovered", index=True)
    # "discovered" | "researching" | "researched" | "verified" | "queued" | "completed" | "rejected"
    research_status: Mapped[str] = mapped_column(String(50), nullable=False, default="pending", index=True)
    # "pending" | "running" | "completed" | "failed"
    trend_score: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    research_quality: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    fact_confidence: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    opportunity_score: Mapped[float] = mapped_column(Float, nullable=False, default=0.0, index=True)
    source_trend_ids: Mapped[list[str]] = mapped_column(JSON, nullable=False, default=list)
    duplicate_of_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("rs_topics.id", ondelete="SET NULL"),
        nullable=True
    )
    article_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    fact_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    researched_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    metadata_: Mapped[dict[str, Any]] = mapped_column("rs_metadata", JSON, nullable=False, default=dict)

    articles: Mapped[list["ResearchArticle"]] = relationship(
        "ResearchArticle", back_populates="topic", lazy="select"
    )
    facts: Mapped[list["ResearchFact"]] = relationship(
        "ResearchFact", back_populates="topic", lazy="select"
    )
    entities: Mapped[list["ResearchEntity"]] = relationship(
        "ResearchEntity", back_populates="topic", lazy="select"
    )
    score: Mapped["ResearchScore | None"] = relationship(
        "ResearchScore", back_populates="topic", uselist=False, lazy="select"
    )

    __table_args__ = (
        Index("ix_rs_topics_status_score", "status", "opportunity_score"),
        Index("ix_rs_topics_research_status", "research_status"),
    )


# ---------------------------------------------------------------------------
# ResearchCluster
# ---------------------------------------------------------------------------

class ResearchCluster(UUIDMixin, TimestampMixin, Base):
    """A group of related topics clustered by semantic similarity."""
    __tablename__ = "rs_clusters"

    canonical_name: Mapped[str] = mapped_column(String(500), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False, default="")
    keywords: Mapped[list[str]] = mapped_column(JSON, nullable=False, default=list)
    categories: Mapped[list[str]] = mapped_column(JSON, nullable=False, default=list)
    topic_ids: Mapped[list[str]] = mapped_column(JSON, nullable=False, default=list)
    topic_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    confidence: Mapped[float] = mapped_column(Float, nullable=False, default=1.0)
    centroid: Mapped[list[float]] = mapped_column(JSON, nullable=False, default=list)
    avg_opportunity_score: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    status: Mapped[str] = mapped_column(String(50), nullable=False, default="active", index=True)
    metadata_: Mapped[dict[str, Any]] = mapped_column("rs_metadata", JSON, nullable=False, default=dict)

    __table_args__ = (
        Index("ix_rs_clusters_status_score", "status", "avg_opportunity_score"),
    )


# ---------------------------------------------------------------------------
# ResearchArticle
# ---------------------------------------------------------------------------

class ResearchArticle(UUIDMixin, TimestampMixin, Base):
    """A fetched article/document providing research on a topic."""
    __tablename__ = "rs_articles"

    topic_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("rs_topics.id", ondelete="CASCADE"),
        nullable=False, index=True
    )
    source_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("rs_sources.id", ondelete="SET NULL"),
        nullable=True, index=True
    )
    title: Mapped[str] = mapped_column(String(1000), nullable=False)
    url: Mapped[str] = mapped_column(String(2000), nullable=False, default="")
    content: Mapped[str] = mapped_column(Text, nullable=False, default="")
    summary: Mapped[str] = mapped_column(Text, nullable=False, default="")
    author: Mapped[str] = mapped_column(String(500), nullable=False, default="")
    published_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    source_type: Mapped[str] = mapped_column(String(100), nullable=False, default="rss")
    language: Mapped[str] = mapped_column(String(20), nullable=False, default="en")
    content_hash: Mapped[str] = mapped_column(String(64), nullable=False, default="", index=True)
    quality_score: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    relevance_score: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    status: Mapped[str] = mapped_column(String(50), nullable=False, default="fetched", index=True)
    # "fetched" | "processed" | "failed"
    error_message: Mapped[str] = mapped_column(Text, nullable=False, default="")
    metadata_: Mapped[dict[str, Any]] = mapped_column("rs_metadata", JSON, nullable=False, default=dict)

    topic: Mapped["ResearchTopic"] = relationship("ResearchTopic", back_populates="articles")

    __table_args__ = (
        Index("ix_rs_articles_topic_status", "topic_id", "status"),
        Index("ix_rs_articles_content_hash", "content_hash"),
    )


# ---------------------------------------------------------------------------
# ResearchFact
# ---------------------------------------------------------------------------

class ResearchFact(UUIDMixin, TimestampMixin, Base):
    """An extracted, structured fact from research articles."""
    __tablename__ = "rs_facts"

    topic_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("rs_topics.id", ondelete="CASCADE"),
        nullable=False, index=True
    )
    article_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("rs_articles.id", ondelete="SET NULL"),
        nullable=True
    )
    fact_type: Mapped[str] = mapped_column(String(100), nullable=False, default="general", index=True)
    # "statistic" | "quote" | "event" | "definition" | "claim" | "general"
    statement: Mapped[str] = mapped_column(Text, nullable=False)
    confidence: Mapped[float] = mapped_column(Float, nullable=False, default=0.5, index=True)
    supporting_sources: Mapped[list[str]] = mapped_column(JSON, nullable=False, default=list)
    conflicting_sources: Mapped[list[str]] = mapped_column(JSON, nullable=False, default=list)
    citations: Mapped[list[dict[str, Any]]] = mapped_column(JSON, nullable=False, default=list)
    is_verified: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False, index=True)
    is_rejected: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    rejection_reason: Mapped[str] = mapped_column(Text, nullable=False, default="")
    verification_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    metadata_: Mapped[dict[str, Any]] = mapped_column("rs_metadata", JSON, nullable=False, default=dict)

    topic: Mapped["ResearchTopic"] = relationship("ResearchTopic", back_populates="facts")

    __table_args__ = (
        Index("ix_rs_facts_topic_type", "topic_id", "fact_type"),
        Index("ix_rs_facts_confidence_verified", "confidence", "is_verified"),
    )


# ---------------------------------------------------------------------------
# ResearchEntity
# ---------------------------------------------------------------------------

class ResearchEntity(UUIDMixin, TimestampMixin, Base):
    """A named entity extracted from research (person, place, date, event, stat)."""
    __tablename__ = "rs_entities"

    topic_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("rs_topics.id", ondelete="CASCADE"),
        nullable=False, index=True
    )
    article_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("rs_articles.id", ondelete="SET NULL"),
        nullable=True
    )
    entity_type: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    # "person" | "place" | "date" | "event" | "statistic" | "organization" | "concept"
    name: Mapped[str] = mapped_column(String(500), nullable=False)
    normalized_name: Mapped[str] = mapped_column(String(500), nullable=False, index=True)
    description: Mapped[str] = mapped_column(Text, nullable=False, default="")
    attributes: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False, default=dict)
    confidence: Mapped[float] = mapped_column(Float, nullable=False, default=1.0)
    wikidata_id: Mapped[str] = mapped_column(String(100), nullable=False, default="")
    wikipedia_url: Mapped[str] = mapped_column(String(2000), nullable=False, default="")
    occurrence_count: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    metadata_: Mapped[dict[str, Any]] = mapped_column("rs_metadata", JSON, nullable=False, default=dict)

    topic: Mapped["ResearchTopic"] = relationship("ResearchTopic", back_populates="entities")

    __table_args__ = (
        Index("ix_rs_entities_topic_type", "topic_id", "entity_type"),
        Index("ix_rs_entities_normalized_name", "normalized_name"),
    )


# ---------------------------------------------------------------------------
# ResearchScore
# ---------------------------------------------------------------------------

class ResearchScore(UUIDMixin, TimestampMixin, Base):
    """Multi-dimensional opportunity score for a research topic."""
    __tablename__ = "rs_scores"

    topic_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("rs_topics.id", ondelete="CASCADE"),
        nullable=False, unique=True, index=True
    )
    trend_score: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    research_quality: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    fact_confidence: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    competition_score: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    novelty_score: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    audience_fit: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    seasonality_score: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    educational_value: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    entertainment_value: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    overall_score: Mapped[float] = mapped_column(Float, nullable=False, default=0.0, index=True)
    scoring_version: Mapped[str] = mapped_column(String(50), nullable=False, default="1.0")
    breakdown: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False, default=dict)
    scored_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    topic: Mapped["ResearchTopic"] = relationship("ResearchTopic", back_populates="score")

    __table_args__ = (
        Index("ix_rs_scores_overall", "overall_score"),
    )


# ---------------------------------------------------------------------------
# ResearchQueue
# ---------------------------------------------------------------------------

class ResearchQueue(UUIDMixin, TimestampMixin, Base):
    """Topics queued for Story Intelligence generation."""
    __tablename__ = "rs_queue"

    topic_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("rs_topics.id", ondelete="CASCADE"),
        nullable=False, index=True
    )
    project_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("projects.id", ondelete="SET NULL"),
        nullable=True, index=True
    )
    priority: Mapped[int] = mapped_column(Integer, nullable=False, default=50, index=True)
    status: Mapped[str] = mapped_column(String(50), nullable=False, default="pending", index=True)
    # "pending" | "processing" | "completed" | "failed" | "paused"
    overall_score: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    research_summary: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False, default=dict)
    knowledge_chunk_ids: Mapped[list[str]] = mapped_column(JSON, nullable=False, default=list)
    story_job_id: Mapped[str] = mapped_column(String(255), nullable=False, default="")
    queued_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    processed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    error_message: Mapped[str] = mapped_column(Text, nullable=False, default="")
    retry_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    __table_args__ = (
        Index("ix_rs_queue_status_priority", "status", "priority"),
        UniqueConstraint("topic_id", name="uq_rs_queue_topic"),
    )


# ---------------------------------------------------------------------------
# ResearchJob
# ---------------------------------------------------------------------------

class ResearchJob(UUIDMixin, TimestampMixin, Base):
    """Async research pipeline job (mirrors EmbeddingJob)."""
    __tablename__ = "rs_jobs"

    job_type: Mapped[str] = mapped_column(String(100), nullable=False, default="discover_trends", index=True)
    # "discover_trends" | "research_topic" | "cluster_topics" | "verify_facts"
    # "integrate_knowledge" | "score_opportunities" | "scheduler_tick"
    status: Mapped[str] = mapped_column(String(50), nullable=False, default="pending", index=True)
    # "pending" | "running" | "completed" | "failed"
    topic_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("rs_topics.id", ondelete="SET NULL"),
        nullable=True, index=True
    )
    celery_task_id: Mapped[str] = mapped_column(String(255), nullable=False, default="")
    execution_mode: Mapped[str] = mapped_column(String(20), nullable=False, default="sync")
    progress_percent: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    current_step: Mapped[str] = mapped_column(String(200), nullable=False, default="")
    result: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False, default=dict)
    error_message: Mapped[str] = mapped_column(Text, nullable=False, default="")
    retry_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    max_retries: Mapped[int] = mapped_column(Integer, nullable=False, default=3)
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    __table_args__ = (
        Index("ix_rs_jobs_type_status", "job_type", "status"),
    )


# ---------------------------------------------------------------------------
# ResearchHistory
# ---------------------------------------------------------------------------

class ResearchHistory(UUIDMixin, TimestampMixin, Base):
    """Audit log of every scheduler run / pipeline execution."""
    __tablename__ = "rs_history"

    run_type: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    # "trend_discovery" | "research_refresh" | "opportunity_report" | "manual"
    status: Mapped[str] = mapped_column(String(50), nullable=False, default="completed", index=True)
    trends_discovered: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    topics_researched: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    facts_verified: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    opportunities_scored: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    knowledge_docs_created: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    duration_seconds: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    error_message: Mapped[str] = mapped_column(Text, nullable=False, default="")
    details: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False, default=dict)
    triggered_by: Mapped[str] = mapped_column(String(100), nullable=False, default="scheduler")

    __table_args__ = (
        Index("ix_rs_history_type_status", "run_type", "status"),
        Index("ix_rs_history_created", "created_at"),
    )


# ---------------------------------------------------------------------------
# ResearchMemory
# ---------------------------------------------------------------------------

class ResearchMemory(UUIDMixin, TimestampMixin, Base):
    """Persistent research memory — what has been researched, what to avoid."""
    __tablename__ = "rs_memory"

    memory_type: Mapped[str] = mapped_column(String(100), nullable=False, default="researched_topic", index=True)
    # "researched_topic" | "rejected_topic" | "blacklist" | "preference" | "context"
    key: Mapped[str] = mapped_column(String(500), nullable=False, index=True)
    value: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False, default=dict)
    confidence: Mapped[float] = mapped_column(Float, nullable=False, default=1.0)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    source: Mapped[str] = mapped_column(String(200), nullable=False, default="system")

    __table_args__ = (
        Index("ix_rs_memory_type_key", "memory_type", "key"),
        Index("ix_rs_memory_active", "is_active"),
    )


# ---------------------------------------------------------------------------
# ResearchVersion
# ---------------------------------------------------------------------------

class ResearchVersion(UUIDMixin, TimestampMixin, Base):
    """Full JSON snapshot of any Research entity at a point in time."""
    __tablename__ = "rs_versions"

    entity_type: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    entity_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False, index=True)
    version_number: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    snapshot: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False, default=dict)
    change_summary: Mapped[str] = mapped_column(Text, nullable=False, default="")
    created_by: Mapped[str] = mapped_column(String(100), nullable=False, default="system")

    __table_args__ = (
        Index("ix_rs_versions_entity", "entity_type", "entity_id"),
    )


# ---------------------------------------------------------------------------
# ResearchAnalytics
# ---------------------------------------------------------------------------

class ResearchAnalytics(UUIDMixin, TimestampMixin, Base):
    """Aggregated analytics snapshots for the research dashboard."""
    __tablename__ = "rs_analytics"

    period_type: Mapped[str] = mapped_column(String(50), nullable=False, default="hourly", index=True)
    # "hourly" | "daily" | "weekly"
    period_start: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, index=True)
    period_end: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    total_trends: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    active_trends: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    emerging_trends: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    total_topics: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    researched_topics: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    verified_facts: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    knowledge_docs_created: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    opportunities_scored: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    avg_opportunity_score: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    top_categories: Mapped[list[str]] = mapped_column(JSON, nullable=False, default=list)
    top_keywords: Mapped[list[str]] = mapped_column(JSON, nullable=False, default=list)
    details: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False, default=dict)

    __table_args__ = (
        Index("ix_rs_analytics_period", "period_type", "period_start"),
    )

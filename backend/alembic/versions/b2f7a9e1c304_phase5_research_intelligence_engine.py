"""phase5_research_intelligence_engine

Revision ID: b2f7a9e1c304
Revises: 9c163cebabb8
Create Date: 2026-07-07 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = 'b2f7a9e1c304'
down_revision: Union[str, None] = '9c163cebabb8'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # rs_sources
    op.create_table(
        'rs_sources',
        sa.Column('name', sa.String(500), nullable=False),
        sa.Column('source_type', sa.String(100), nullable=False),
        sa.Column('url', sa.String(2000), nullable=False),
        sa.Column('description', sa.Text(), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=False),
        sa.Column('fetch_interval_seconds', sa.Integer(), nullable=False),
        sa.Column('last_fetched_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('fetch_count', sa.Integer(), nullable=False),
        sa.Column('error_count', sa.Integer(), nullable=False),
        sa.Column('last_error', sa.Text(), nullable=False),
        sa.Column('config', sa.JSON(), nullable=False),
        sa.Column('rs_metadata', sa.JSON(), nullable=False),
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_rs_sources_source_type'), 'rs_sources', ['source_type'], unique=False)
    op.create_index('ix_rs_sources_type_active', 'rs_sources', ['source_type', 'is_active'], unique=False)

    # rs_trends
    op.create_table(
        'rs_trends',
        sa.Column('source_id', sa.UUID(), nullable=True),
        sa.Column('keyword', sa.String(500), nullable=False),
        sa.Column('normalized_keyword', sa.String(500), nullable=False),
        sa.Column('category', sa.String(200), nullable=False),
        sa.Column('region', sa.String(100), nullable=False),
        sa.Column('language', sa.String(20), nullable=False),
        sa.Column('trend_score', sa.Float(), nullable=False),
        sa.Column('velocity', sa.Float(), nullable=False),
        sa.Column('growth_rate', sa.Float(), nullable=False),
        sa.Column('popularity_index', sa.Float(), nullable=False),
        sa.Column('is_emerging', sa.Boolean(), nullable=False),
        sa.Column('is_declining', sa.Boolean(), nullable=False),
        sa.Column('status', sa.String(50), nullable=False),
        sa.Column('raw_data', sa.JSON(), nullable=False),
        sa.Column('discovered_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['source_id'], ['rs_sources.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_rs_trends_keyword'), 'rs_trends', ['keyword'], unique=False)
    op.create_index(op.f('ix_rs_trends_normalized_keyword'), 'rs_trends', ['normalized_keyword'], unique=False)
    op.create_index(op.f('ix_rs_trends_trend_score'), 'rs_trends', ['trend_score'], unique=False)
    op.create_index(op.f('ix_rs_trends_is_emerging'), 'rs_trends', ['is_emerging'], unique=False)
    op.create_index(op.f('ix_rs_trends_status'), 'rs_trends', ['status'], unique=False)
    op.create_index('ix_rs_trends_keyword_status', 'rs_trends', ['normalized_keyword', 'status'], unique=False)
    op.create_index('ix_rs_trends_score_emerging', 'rs_trends', ['trend_score', 'is_emerging'], unique=False)

    # rs_topics
    op.create_table(
        'rs_topics',
        sa.Column('canonical_name', sa.String(500), nullable=False),
        sa.Column('slug', sa.String(500), nullable=False),
        sa.Column('description', sa.Text(), nullable=False),
        sa.Column('keywords', sa.JSON(), nullable=False),
        sa.Column('categories', sa.JSON(), nullable=False),
        sa.Column('language', sa.String(20), nullable=False),
        sa.Column('status', sa.String(50), nullable=False),
        sa.Column('research_status', sa.String(50), nullable=False),
        sa.Column('trend_score', sa.Float(), nullable=False),
        sa.Column('research_quality', sa.Float(), nullable=False),
        sa.Column('fact_confidence', sa.Float(), nullable=False),
        sa.Column('opportunity_score', sa.Float(), nullable=False),
        sa.Column('source_trend_ids', sa.JSON(), nullable=False),
        sa.Column('duplicate_of_id', sa.UUID(), nullable=True),
        sa.Column('article_count', sa.Integer(), nullable=False),
        sa.Column('fact_count', sa.Integer(), nullable=False),
        sa.Column('researched_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('rs_metadata', sa.JSON(), nullable=False),
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['duplicate_of_id'], ['rs_topics.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('slug'),
    )
    op.create_index(op.f('ix_rs_topics_canonical_name'), 'rs_topics', ['canonical_name'], unique=False)
    op.create_index(op.f('ix_rs_topics_slug'), 'rs_topics', ['slug'], unique=True)
    op.create_index(op.f('ix_rs_topics_status'), 'rs_topics', ['status'], unique=False)
    op.create_index(op.f('ix_rs_topics_research_status'), 'rs_topics', ['research_status'], unique=False)
    op.create_index(op.f('ix_rs_topics_opportunity_score'), 'rs_topics', ['opportunity_score'], unique=False)
    op.create_index('ix_rs_topics_status_score', 'rs_topics', ['status', 'opportunity_score'], unique=False)

    # rs_clusters
    op.create_table(
        'rs_clusters',
        sa.Column('canonical_name', sa.String(500), nullable=False),
        sa.Column('description', sa.Text(), nullable=False),
        sa.Column('keywords', sa.JSON(), nullable=False),
        sa.Column('categories', sa.JSON(), nullable=False),
        sa.Column('topic_ids', sa.JSON(), nullable=False),
        sa.Column('topic_count', sa.Integer(), nullable=False),
        sa.Column('confidence', sa.Float(), nullable=False),
        sa.Column('centroid', sa.JSON(), nullable=False),
        sa.Column('avg_opportunity_score', sa.Float(), nullable=False),
        sa.Column('status', sa.String(50), nullable=False),
        sa.Column('rs_metadata', sa.JSON(), nullable=False),
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_rs_clusters_status'), 'rs_clusters', ['status'], unique=False)
    op.create_index('ix_rs_clusters_status_score', 'rs_clusters', ['status', 'avg_opportunity_score'], unique=False)

    # rs_articles
    op.create_table(
        'rs_articles',
        sa.Column('topic_id', sa.UUID(), nullable=False),
        sa.Column('source_id', sa.UUID(), nullable=True),
        sa.Column('title', sa.String(1000), nullable=False),
        sa.Column('url', sa.String(2000), nullable=False),
        sa.Column('content', sa.Text(), nullable=False),
        sa.Column('summary', sa.Text(), nullable=False),
        sa.Column('author', sa.String(500), nullable=False),
        sa.Column('published_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('source_type', sa.String(100), nullable=False),
        sa.Column('language', sa.String(20), nullable=False),
        sa.Column('content_hash', sa.String(64), nullable=False),
        sa.Column('quality_score', sa.Float(), nullable=False),
        sa.Column('relevance_score', sa.Float(), nullable=False),
        sa.Column('status', sa.String(50), nullable=False),
        sa.Column('error_message', sa.Text(), nullable=False),
        sa.Column('rs_metadata', sa.JSON(), nullable=False),
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['topic_id'], ['rs_topics.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['source_id'], ['rs_sources.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_rs_articles_topic_id'), 'rs_articles', ['topic_id'], unique=False)
    op.create_index(op.f('ix_rs_articles_status'), 'rs_articles', ['status'], unique=False)
    op.create_index('ix_rs_articles_topic_status', 'rs_articles', ['topic_id', 'status'], unique=False)
    op.create_index('ix_rs_articles_content_hash', 'rs_articles', ['content_hash'], unique=False)

    # rs_facts
    op.create_table(
        'rs_facts',
        sa.Column('topic_id', sa.UUID(), nullable=False),
        sa.Column('article_id', sa.UUID(), nullable=True),
        sa.Column('fact_type', sa.String(100), nullable=False),
        sa.Column('statement', sa.Text(), nullable=False),
        sa.Column('confidence', sa.Float(), nullable=False),
        sa.Column('supporting_sources', sa.JSON(), nullable=False),
        sa.Column('conflicting_sources', sa.JSON(), nullable=False),
        sa.Column('citations', sa.JSON(), nullable=False),
        sa.Column('is_verified', sa.Boolean(), nullable=False),
        sa.Column('is_rejected', sa.Boolean(), nullable=False),
        sa.Column('rejection_reason', sa.Text(), nullable=False),
        sa.Column('verification_count', sa.Integer(), nullable=False),
        sa.Column('rs_metadata', sa.JSON(), nullable=False),
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['topic_id'], ['rs_topics.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['article_id'], ['rs_articles.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_rs_facts_topic_id'), 'rs_facts', ['topic_id'], unique=False)
    op.create_index(op.f('ix_rs_facts_fact_type'), 'rs_facts', ['fact_type'], unique=False)
    op.create_index(op.f('ix_rs_facts_is_verified'), 'rs_facts', ['is_verified'], unique=False)
    op.create_index('ix_rs_facts_topic_type', 'rs_facts', ['topic_id', 'fact_type'], unique=False)
    op.create_index('ix_rs_facts_confidence_verified', 'rs_facts', ['confidence', 'is_verified'], unique=False)

    # rs_entities
    op.create_table(
        'rs_entities',
        sa.Column('topic_id', sa.UUID(), nullable=False),
        sa.Column('article_id', sa.UUID(), nullable=True),
        sa.Column('entity_type', sa.String(100), nullable=False),
        sa.Column('name', sa.String(500), nullable=False),
        sa.Column('normalized_name', sa.String(500), nullable=False),
        sa.Column('description', sa.Text(), nullable=False),
        sa.Column('attributes', sa.JSON(), nullable=False),
        sa.Column('confidence', sa.Float(), nullable=False),
        sa.Column('wikidata_id', sa.String(100), nullable=False),
        sa.Column('wikipedia_url', sa.String(2000), nullable=False),
        sa.Column('occurrence_count', sa.Integer(), nullable=False),
        sa.Column('rs_metadata', sa.JSON(), nullable=False),
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['topic_id'], ['rs_topics.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['article_id'], ['rs_articles.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_rs_entities_topic_id'), 'rs_entities', ['topic_id'], unique=False)
    op.create_index(op.f('ix_rs_entities_entity_type'), 'rs_entities', ['entity_type'], unique=False)
    op.create_index('ix_rs_entities_topic_type', 'rs_entities', ['topic_id', 'entity_type'], unique=False)
    op.create_index('ix_rs_entities_normalized_name', 'rs_entities', ['normalized_name'], unique=False)

    # rs_scores
    op.create_table(
        'rs_scores',
        sa.Column('topic_id', sa.UUID(), nullable=False),
        sa.Column('trend_score', sa.Float(), nullable=False),
        sa.Column('research_quality', sa.Float(), nullable=False),
        sa.Column('fact_confidence', sa.Float(), nullable=False),
        sa.Column('competition_score', sa.Float(), nullable=False),
        sa.Column('novelty_score', sa.Float(), nullable=False),
        sa.Column('audience_fit', sa.Float(), nullable=False),
        sa.Column('seasonality_score', sa.Float(), nullable=False),
        sa.Column('educational_value', sa.Float(), nullable=False),
        sa.Column('entertainment_value', sa.Float(), nullable=False),
        sa.Column('overall_score', sa.Float(), nullable=False),
        sa.Column('scoring_version', sa.String(50), nullable=False),
        sa.Column('breakdown', sa.JSON(), nullable=False),
        sa.Column('scored_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['topic_id'], ['rs_topics.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('topic_id'),
    )
    op.create_index(op.f('ix_rs_scores_topic_id'), 'rs_scores', ['topic_id'], unique=True)
    op.create_index('ix_rs_scores_overall', 'rs_scores', ['overall_score'], unique=False)

    # rs_queue
    op.create_table(
        'rs_queue',
        sa.Column('topic_id', sa.UUID(), nullable=False),
        sa.Column('project_id', sa.UUID(), nullable=True),
        sa.Column('priority', sa.Integer(), nullable=False),
        sa.Column('status', sa.String(50), nullable=False),
        sa.Column('overall_score', sa.Float(), nullable=False),
        sa.Column('research_summary', sa.JSON(), nullable=False),
        sa.Column('knowledge_chunk_ids', sa.JSON(), nullable=False),
        sa.Column('story_job_id', sa.String(255), nullable=False),
        sa.Column('queued_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('processed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('error_message', sa.Text(), nullable=False),
        sa.Column('retry_count', sa.Integer(), nullable=False),
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['topic_id'], ['rs_topics.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['project_id'], ['projects.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('topic_id', name='uq_rs_queue_topic'),
    )
    op.create_index(op.f('ix_rs_queue_topic_id'), 'rs_queue', ['topic_id'], unique=True)
    op.create_index(op.f('ix_rs_queue_status'), 'rs_queue', ['status'], unique=False)
    op.create_index(op.f('ix_rs_queue_priority'), 'rs_queue', ['priority'], unique=False)
    op.create_index('ix_rs_queue_status_priority', 'rs_queue', ['status', 'priority'], unique=False)

    # rs_jobs
    op.create_table(
        'rs_jobs',
        sa.Column('job_type', sa.String(100), nullable=False),
        sa.Column('status', sa.String(50), nullable=False),
        sa.Column('topic_id', sa.UUID(), nullable=True),
        sa.Column('celery_task_id', sa.String(255), nullable=False),
        sa.Column('execution_mode', sa.String(20), nullable=False),
        sa.Column('progress_percent', sa.Integer(), nullable=False),
        sa.Column('current_step', sa.String(200), nullable=False),
        sa.Column('result', sa.JSON(), nullable=False),
        sa.Column('error_message', sa.Text(), nullable=False),
        sa.Column('retry_count', sa.Integer(), nullable=False),
        sa.Column('max_retries', sa.Integer(), nullable=False),
        sa.Column('started_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('completed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['topic_id'], ['rs_topics.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_rs_jobs_job_type'), 'rs_jobs', ['job_type'], unique=False)
    op.create_index(op.f('ix_rs_jobs_status'), 'rs_jobs', ['status'], unique=False)
    op.create_index('ix_rs_jobs_type_status', 'rs_jobs', ['job_type', 'status'], unique=False)

    # rs_history
    op.create_table(
        'rs_history',
        sa.Column('run_type', sa.String(100), nullable=False),
        sa.Column('status', sa.String(50), nullable=False),
        sa.Column('trends_discovered', sa.Integer(), nullable=False),
        sa.Column('topics_researched', sa.Integer(), nullable=False),
        sa.Column('facts_verified', sa.Integer(), nullable=False),
        sa.Column('opportunities_scored', sa.Integer(), nullable=False),
        sa.Column('knowledge_docs_created', sa.Integer(), nullable=False),
        sa.Column('duration_seconds', sa.Float(), nullable=False),
        sa.Column('error_message', sa.Text(), nullable=False),
        sa.Column('details', sa.JSON(), nullable=False),
        sa.Column('triggered_by', sa.String(100), nullable=False),
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_rs_history_run_type'), 'rs_history', ['run_type'], unique=False)
    op.create_index(op.f('ix_rs_history_status'), 'rs_history', ['status'], unique=False)
    op.create_index('ix_rs_history_type_status', 'rs_history', ['run_type', 'status'], unique=False)
    op.create_index('ix_rs_history_created', 'rs_history', ['created_at'], unique=False)

    # rs_memory
    op.create_table(
        'rs_memory',
        sa.Column('memory_type', sa.String(100), nullable=False),
        sa.Column('key', sa.String(500), nullable=False),
        sa.Column('value', sa.JSON(), nullable=False),
        sa.Column('confidence', sa.Float(), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=False),
        sa.Column('expires_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('source', sa.String(200), nullable=False),
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_rs_memory_memory_type'), 'rs_memory', ['memory_type'], unique=False)
    op.create_index(op.f('ix_rs_memory_key'), 'rs_memory', ['key'], unique=False)
    op.create_index('ix_rs_memory_type_key', 'rs_memory', ['memory_type', 'key'], unique=False)
    op.create_index('ix_rs_memory_active', 'rs_memory', ['is_active'], unique=False)

    # rs_versions
    op.create_table(
        'rs_versions',
        sa.Column('entity_type', sa.String(100), nullable=False),
        sa.Column('entity_id', sa.UUID(), nullable=False),
        sa.Column('version_number', sa.Integer(), nullable=False),
        sa.Column('snapshot', sa.JSON(), nullable=False),
        sa.Column('change_summary', sa.Text(), nullable=False),
        sa.Column('created_by', sa.String(100), nullable=False),
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_rs_versions_entity_type'), 'rs_versions', ['entity_type'], unique=False)
    op.create_index(op.f('ix_rs_versions_entity_id'), 'rs_versions', ['entity_id'], unique=False)
    op.create_index('ix_rs_versions_entity', 'rs_versions', ['entity_type', 'entity_id'], unique=False)

    # rs_analytics
    op.create_table(
        'rs_analytics',
        sa.Column('period_type', sa.String(50), nullable=False),
        sa.Column('period_start', sa.DateTime(timezone=True), nullable=False),
        sa.Column('period_end', sa.DateTime(timezone=True), nullable=False),
        sa.Column('total_trends', sa.Integer(), nullable=False),
        sa.Column('active_trends', sa.Integer(), nullable=False),
        sa.Column('emerging_trends', sa.Integer(), nullable=False),
        sa.Column('total_topics', sa.Integer(), nullable=False),
        sa.Column('researched_topics', sa.Integer(), nullable=False),
        sa.Column('verified_facts', sa.Integer(), nullable=False),
        sa.Column('knowledge_docs_created', sa.Integer(), nullable=False),
        sa.Column('opportunities_scored', sa.Integer(), nullable=False),
        sa.Column('avg_opportunity_score', sa.Float(), nullable=False),
        sa.Column('top_categories', sa.JSON(), nullable=False),
        sa.Column('top_keywords', sa.JSON(), nullable=False),
        sa.Column('details', sa.JSON(), nullable=False),
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_rs_analytics_period_type'), 'rs_analytics', ['period_type'], unique=False)
    op.create_index(op.f('ix_rs_analytics_period_start'), 'rs_analytics', ['period_start'], unique=False)
    op.create_index('ix_rs_analytics_period', 'rs_analytics', ['period_type', 'period_start'], unique=False)


def downgrade() -> None:
    op.drop_table('rs_analytics')
    op.drop_table('rs_versions')
    op.drop_table('rs_memory')
    op.drop_table('rs_history')
    op.drop_table('rs_jobs')
    op.drop_table('rs_queue')
    op.drop_table('rs_scores')
    op.drop_table('rs_entities')
    op.drop_table('rs_facts')
    op.drop_table('rs_articles')
    op.drop_table('rs_clusters')
    op.drop_table('rs_topics')
    op.drop_table('rs_trends')
    op.drop_table('rs_sources')

"""phase6_asset_generation_engine

Revision ID: c4e1f2a3b5d6
Revises: b2f7a9e1c304
Create Date: 2026-07-08 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID, JSON

revision: str = 'c4e1f2a3b5d6'
down_revision: Union[str, None] = 'b2f7a9e1c304'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ag_styles — must be created before ag_projects (FK)
    op.create_table(
        'ag_styles',
        sa.Column('id', UUID(as_uuid=True), primary_key=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.Column('name', sa.String(200), nullable=False),
        sa.Column('slug', sa.String(200), nullable=False, unique=True),
        sa.Column('description', sa.Text, nullable=False, server_default=''),
        sa.Column('style_prompt', sa.Text, nullable=False, server_default=''),
        sa.Column('negative_prompt', sa.Text, nullable=False, server_default=''),
        sa.Column('keywords', JSON, nullable=False, server_default='[]'),
        sa.Column('color_palette', JSON, nullable=False, server_default='[]'),
        sa.Column('reference_artists', JSON, nullable=False, server_default='[]'),
        sa.Column('style_type', sa.String(100), nullable=False, server_default='2d_cartoon'),
        sa.Column('is_default', sa.Boolean, nullable=False, server_default='false'),
        sa.Column('is_active', sa.Boolean, nullable=False, server_default='true'),
        sa.Column('usage_count', sa.Integer, nullable=False, server_default='0'),
        sa.Column('avg_quality_score', sa.Float, nullable=False, server_default='0'),
        sa.Column('extra', JSON, nullable=False, server_default='{}'),
    )
    op.create_index('ix_ag_styles_name', 'ag_styles', ['name'])
    op.create_index('ix_ag_styles_slug', 'ag_styles', ['slug'])
    op.create_index('ix_ag_styles_style_type', 'ag_styles', ['style_type'])
    op.create_index('ix_ag_styles_is_default', 'ag_styles', ['is_default'])

    # ag_projects
    op.create_table(
        'ag_projects',
        sa.Column('id', UUID(as_uuid=True), primary_key=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.Column('project_id', UUID(as_uuid=True), sa.ForeignKey('projects.id', ondelete='CASCADE'), nullable=False, unique=True),
        sa.Column('name', sa.String(500), nullable=False, server_default=''),
        sa.Column('description', sa.Text, nullable=False, server_default=''),
        sa.Column('default_style_id', UUID(as_uuid=True), sa.ForeignKey('ag_styles.id', ondelete='SET NULL'), nullable=True),
        sa.Column('quality_threshold', sa.Float, nullable=False, server_default='90'),
        sa.Column('max_retries', sa.Integer, nullable=False, server_default='3'),
        sa.Column('target_resolution', sa.String(50), nullable=False, server_default='1024x1024'),
        sa.Column('is_active', sa.Boolean, nullable=False, server_default='true'),
        sa.Column('total_assets_generated', sa.Integer, nullable=False, server_default='0'),
        sa.Column('total_retries', sa.Integer, nullable=False, server_default='0'),
        sa.Column('avg_quality_score', sa.Float, nullable=False, server_default='0'),
        sa.Column('storage_bytes_used', sa.Integer, nullable=False, server_default='0'),
        sa.Column('config', JSON, nullable=False, server_default='{}'),
        sa.Column('ag_project_meta', JSON, nullable=False, server_default='{}'),
    )
    op.create_index('ix_ag_projects_project_id', 'ag_projects', ['project_id'])
    op.create_index('ix_ag_projects_is_active', 'ag_projects', ['is_active'])

    # ag_collections
    op.create_table(
        'ag_collections',
        sa.Column('id', UUID(as_uuid=True), primary_key=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.Column('project_id', UUID(as_uuid=True), sa.ForeignKey('projects.id', ondelete='CASCADE'), nullable=False),
        sa.Column('name', sa.String(500), nullable=False),
        sa.Column('description', sa.Text, nullable=False, server_default=''),
        sa.Column('collection_type', sa.String(100), nullable=False, server_default='mixed'),
        sa.Column('asset_count', sa.Integer, nullable=False, server_default='0'),
        sa.Column('is_active', sa.Boolean, nullable=False, server_default='true'),
        sa.Column('cover_asset_id', UUID(as_uuid=True), nullable=True),
        sa.Column('tags', JSON, nullable=False, server_default='[]'),
        sa.Column('ag_collection_meta', JSON, nullable=False, server_default='{}'),
    )
    op.create_index('ix_ag_collections_project_id', 'ag_collections', ['project_id'])
    op.create_index('ix_ag_collections_collection_type', 'ag_collections', ['collection_type'])
    op.create_index('ix_ag_collections_project_type', 'ag_collections', ['project_id', 'collection_type'])

    # ag_assets
    op.create_table(
        'ag_assets',
        sa.Column('id', UUID(as_uuid=True), primary_key=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.Column('project_id', UUID(as_uuid=True), sa.ForeignKey('projects.id', ondelete='CASCADE'), nullable=False),
        sa.Column('collection_id', UUID(as_uuid=True), sa.ForeignKey('ag_collections.id', ondelete='SET NULL'), nullable=True),
        sa.Column('style_id', UUID(as_uuid=True), sa.ForeignKey('ag_styles.id', ondelete='SET NULL'), nullable=True),
        sa.Column('character_id', UUID(as_uuid=True), nullable=True),
        sa.Column('episode_id', UUID(as_uuid=True), nullable=True),
        sa.Column('scene_id', UUID(as_uuid=True), nullable=True),
        sa.Column('name', sa.String(500), nullable=False),
        sa.Column('description', sa.Text, nullable=False, server_default=''),
        sa.Column('asset_type', sa.String(100), nullable=False),
        sa.Column('status', sa.String(50), nullable=False, server_default='pending'),
        sa.Column('current_version_id', UUID(as_uuid=True), nullable=True),
        sa.Column('best_version_id', UUID(as_uuid=True), nullable=True),
        sa.Column('version_count', sa.Integer, nullable=False, server_default='0'),
        sa.Column('retry_count', sa.Integer, nullable=False, server_default='0'),
        sa.Column('max_retries', sa.Integer, nullable=False, server_default='3'),
        sa.Column('quality_score', sa.Float, nullable=False, server_default='0'),
        sa.Column('quality_threshold', sa.Float, nullable=False, server_default='90'),
        sa.Column('storage_key', sa.String(2000), nullable=False, server_default=''),
        sa.Column('storage_bucket', sa.String(500), nullable=False, server_default='assets'),
        sa.Column('width', sa.Integer, nullable=False, server_default='0'),
        sa.Column('height', sa.Integer, nullable=False, server_default='0'),
        sa.Column('file_size_bytes', sa.Integer, nullable=False, server_default='0'),
        sa.Column('mime_type', sa.String(100), nullable=False, server_default='image/png'),
        sa.Column('tags', JSON, nullable=False, server_default='[]'),
        sa.Column('consistency_fingerprint', JSON, nullable=False, server_default='{}'),
        sa.Column('generation_params', JSON, nullable=False, server_default='{}'),
        sa.Column('ag_asset_meta', JSON, nullable=False, server_default='{}'),
        sa.Column('generated_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('is_deleted', sa.Boolean, nullable=False, server_default='false'),
    )
    op.create_index('ix_ag_assets_project_id', 'ag_assets', ['project_id'])
    op.create_index('ix_ag_assets_collection_id', 'ag_assets', ['collection_id'])
    op.create_index('ix_ag_assets_character_id', 'ag_assets', ['character_id'])
    op.create_index('ix_ag_assets_episode_id', 'ag_assets', ['episode_id'])
    op.create_index('ix_ag_assets_scene_id', 'ag_assets', ['scene_id'])
    op.create_index('ix_ag_assets_asset_type', 'ag_assets', ['asset_type'])
    op.create_index('ix_ag_assets_status', 'ag_assets', ['status'])
    op.create_index('ix_ag_assets_quality_score', 'ag_assets', ['quality_score'])
    op.create_index('ix_ag_assets_is_deleted', 'ag_assets', ['is_deleted'])
    op.create_index('ix_ag_assets_project_type_status', 'ag_assets', ['project_id', 'asset_type', 'status'])
    op.create_index('ix_ag_assets_character_type', 'ag_assets', ['character_id', 'asset_type'])
    op.create_index('ix_ag_assets_episode', 'ag_assets', ['episode_id', 'asset_type'])

    # ag_prompt_templates  (referenced by ag_prompts)
    op.create_table(
        'ag_prompt_templates',
        sa.Column('id', UUID(as_uuid=True), primary_key=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.Column('name', sa.String(500), nullable=False),
        sa.Column('asset_type', sa.String(100), nullable=False),
        sa.Column('style_type', sa.String(100), nullable=False, server_default='2d_cartoon'),
        sa.Column('positive_template', sa.Text, nullable=False, server_default=''),
        sa.Column('negative_template', sa.Text, nullable=False, server_default=''),
        sa.Column('style_template', sa.Text, nullable=False, server_default=''),
        sa.Column('camera_template', sa.Text, nullable=False, server_default=''),
        sa.Column('lighting_template', sa.Text, nullable=False, server_default=''),
        sa.Column('variables', JSON, nullable=False, server_default='[]'),
        sa.Column('is_active', sa.Boolean, nullable=False, server_default='true'),
        sa.Column('is_default', sa.Boolean, nullable=False, server_default='false'),
        sa.Column('use_count', sa.Integer, nullable=False, server_default='0'),
        sa.Column('avg_quality_score', sa.Float, nullable=False, server_default='0'),
        sa.Column('extra', JSON, nullable=False, server_default='{}'),
    )
    op.create_index('ix_ag_prompt_templates_name', 'ag_prompt_templates', ['name'])
    op.create_index('ix_ag_prompt_templates_asset_type', 'ag_prompt_templates', ['asset_type'])
    op.create_index('ix_ag_prompt_templates_type_style', 'ag_prompt_templates', ['asset_type', 'style_type'])

    # ag_prompts
    op.create_table(
        'ag_prompts',
        sa.Column('id', UUID(as_uuid=True), primary_key=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.Column('asset_id', UUID(as_uuid=True), sa.ForeignKey('ag_assets.id', ondelete='SET NULL'), nullable=True),
        sa.Column('template_id', UUID(as_uuid=True), sa.ForeignKey('ag_prompt_templates.id', ondelete='SET NULL'), nullable=True),
        sa.Column('positive_prompt', sa.Text, nullable=False, server_default=''),
        sa.Column('negative_prompt', sa.Text, nullable=False, server_default=''),
        sa.Column('style_prompt', sa.Text, nullable=False, server_default=''),
        sa.Column('camera_prompt', sa.Text, nullable=False, server_default=''),
        sa.Column('composition_prompt', sa.Text, nullable=False, server_default=''),
        sa.Column('lighting_prompt', sa.Text, nullable=False, server_default=''),
        sa.Column('color_prompt', sa.Text, nullable=False, server_default=''),
        sa.Column('consistency_prompt', sa.Text, nullable=False, server_default=''),
        sa.Column('full_prompt', sa.Text, nullable=False, server_default=''),
        sa.Column('full_negative_prompt', sa.Text, nullable=False, server_default=''),
        sa.Column('prompt_type', sa.String(100), nullable=False, server_default='character'),
        sa.Column('quality_score', sa.Float, nullable=False, server_default='0'),
        sa.Column('was_successful', sa.Boolean, nullable=False, server_default='false'),
        sa.Column('use_count', sa.Integer, nullable=False, server_default='0'),
        sa.Column('generation_params', JSON, nullable=False, server_default='{}'),
        sa.Column('ag_prompt_meta', JSON, nullable=False, server_default='{}'),
    )
    op.create_index('ix_ag_prompts_asset_id', 'ag_prompts', ['asset_id'])
    op.create_index('ix_ag_prompts_prompt_type', 'ag_prompts', ['prompt_type'])
    op.create_index('ix_ag_prompts_was_successful', 'ag_prompts', ['was_successful'])

    # ag_versions
    op.create_table(
        'ag_versions',
        sa.Column('id', UUID(as_uuid=True), primary_key=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.Column('asset_id', UUID(as_uuid=True), sa.ForeignKey('ag_assets.id', ondelete='CASCADE'), nullable=False),
        sa.Column('prompt_id', UUID(as_uuid=True), sa.ForeignKey('ag_prompts.id', ondelete='SET NULL'), nullable=True),
        sa.Column('version_number', sa.Integer, nullable=False, server_default='1'),
        sa.Column('version_label', sa.String(50), nullable=False, server_default='original'),
        sa.Column('storage_key', sa.String(2000), nullable=False, server_default=''),
        sa.Column('storage_bucket', sa.String(500), nullable=False, server_default='assets'),
        sa.Column('width', sa.Integer, nullable=False, server_default='0'),
        sa.Column('height', sa.Integer, nullable=False, server_default='0'),
        sa.Column('file_size_bytes', sa.Integer, nullable=False, server_default='0'),
        sa.Column('quality_score', sa.Float, nullable=False, server_default='0'),
        sa.Column('is_approved', sa.Boolean, nullable=False, server_default='false'),
        sa.Column('is_rejected', sa.Boolean, nullable=False, server_default='false'),
        sa.Column('rejection_reason', sa.Text, nullable=False, server_default=''),
        sa.Column('generation_seed', sa.Integer, nullable=False, server_default='0'),
        sa.Column('generation_steps', sa.Integer, nullable=False, server_default='20'),
        sa.Column('cfg_scale', sa.Float, nullable=False, server_default='7'),
        sa.Column('sampler', sa.String(100), nullable=False, server_default='euler_a'),
        sa.Column('generation_params', JSON, nullable=False, server_default='{}'),
        sa.Column('evaluation_scores', JSON, nullable=False, server_default='{}'),
        sa.Column('ag_version_meta', JSON, nullable=False, server_default='{}'),
    )
    op.create_index('ix_ag_versions_asset_id', 'ag_versions', ['asset_id'])
    op.create_index('ix_ag_versions_quality_score', 'ag_versions', ['quality_score'])
    op.create_index('ix_ag_versions_is_approved', 'ag_versions', ['is_approved'])
    op.create_index('ix_ag_versions_asset_number', 'ag_versions', ['asset_id', 'version_number'])
    op.create_unique_constraint('uq_ag_versions_asset_version', 'ag_versions', ['asset_id', 'version_number'])

    # ag_generated_images
    op.create_table(
        'ag_generated_images',
        sa.Column('id', UUID(as_uuid=True), primary_key=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.Column('asset_id', UUID(as_uuid=True), sa.ForeignKey('ag_assets.id', ondelete='SET NULL'), nullable=True),
        sa.Column('version_id', UUID(as_uuid=True), sa.ForeignKey('ag_versions.id', ondelete='SET NULL'), nullable=True),
        sa.Column('prompt_id', UUID(as_uuid=True), sa.ForeignKey('ag_prompts.id', ondelete='SET NULL'), nullable=True),
        sa.Column('storage_key', sa.String(2000), nullable=False, server_default=''),
        sa.Column('storage_bucket', sa.String(500), nullable=False, server_default='assets'),
        sa.Column('width', sa.Integer, nullable=False, server_default='0'),
        sa.Column('height', sa.Integer, nullable=False, server_default='0'),
        sa.Column('file_size_bytes', sa.Integer, nullable=False, server_default='0'),
        sa.Column('mime_type', sa.String(100), nullable=False, server_default='image/png'),
        sa.Column('status', sa.String(50), nullable=False, server_default='pending'),
        sa.Column('generation_time_ms', sa.Integer, nullable=False, server_default='0'),
        sa.Column('provider', sa.String(100), nullable=False, server_default='mock'),
        sa.Column('provider_job_id', sa.String(500), nullable=False, server_default=''),
        sa.Column('generation_params', JSON, nullable=False, server_default='{}'),
        sa.Column('raw_metadata', JSON, nullable=False, server_default='{}'),
    )
    op.create_index('ix_ag_generated_images_asset_id', 'ag_generated_images', ['asset_id'])
    op.create_index('ix_ag_generated_images_version_id', 'ag_generated_images', ['version_id'])
    op.create_index('ix_ag_generated_images_status', 'ag_generated_images', ['status'])

    # ag_evaluations
    op.create_table(
        'ag_evaluations',
        sa.Column('id', UUID(as_uuid=True), primary_key=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.Column('asset_id', UUID(as_uuid=True), sa.ForeignKey('ag_assets.id', ondelete='CASCADE'), nullable=False),
        sa.Column('version_id', UUID(as_uuid=True), sa.ForeignKey('ag_versions.id', ondelete='SET NULL'), nullable=True),
        sa.Column('image_id', UUID(as_uuid=True), sa.ForeignKey('ag_generated_images.id', ondelete='SET NULL'), nullable=True),
        sa.Column('overall_score', sa.Float, nullable=False, server_default='0'),
        sa.Column('prompt_quality', sa.Float, nullable=False, server_default='0'),
        sa.Column('image_quality', sa.Float, nullable=False, server_default='0'),
        sa.Column('character_consistency', sa.Float, nullable=False, server_default='0'),
        sa.Column('background_consistency', sa.Float, nullable=False, server_default='0'),
        sa.Column('composition_score', sa.Float, nullable=False, server_default='0'),
        sa.Column('lighting_score', sa.Float, nullable=False, server_default='0'),
        sa.Column('style_match', sa.Float, nullable=False, server_default='0'),
        sa.Column('scene_match', sa.Float, nullable=False, server_default='0'),
        sa.Column('resolution_score', sa.Float, nullable=False, server_default='0'),
        sa.Column('artifact_score', sa.Float, nullable=False, server_default='0'),
        sa.Column('hands_score', sa.Float, nullable=False, server_default='0'),
        sa.Column('face_score', sa.Float, nullable=False, server_default='0'),
        sa.Column('text_error_score', sa.Float, nullable=False, server_default='0'),
        sa.Column('passed_threshold', sa.Boolean, nullable=False, server_default='false'),
        sa.Column('failure_reasons', JSON, nullable=False, server_default='[]'),
        sa.Column('notes', sa.Text, nullable=False, server_default=''),
        sa.Column('evaluated_by', sa.String(100), nullable=False, server_default='mock'),
        sa.Column('raw_scores', JSON, nullable=False, server_default='{}'),
    )
    op.create_index('ix_ag_evaluations_asset_id', 'ag_evaluations', ['asset_id'])
    op.create_index('ix_ag_evaluations_version_id', 'ag_evaluations', ['version_id'])
    op.create_index('ix_ag_evaluations_overall_score', 'ag_evaluations', ['overall_score'])
    op.create_index('ix_ag_evaluations_passed_threshold', 'ag_evaluations', ['passed_threshold'])

    # ag_tags
    op.create_table(
        'ag_tags',
        sa.Column('id', UUID(as_uuid=True), primary_key=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.Column('name', sa.String(200), nullable=False, unique=True),
        sa.Column('slug', sa.String(200), nullable=False, unique=True),
        sa.Column('category', sa.String(100), nullable=False, server_default='type'),
        sa.Column('usage_count', sa.Integer, nullable=False, server_default='0'),
        sa.Column('color', sa.String(20), nullable=False, server_default='#6366f1'),
        sa.Column('is_active', sa.Boolean, nullable=False, server_default='true'),
    )
    op.create_index('ix_ag_tags_name', 'ag_tags', ['name'])
    op.create_index('ix_ag_tags_slug', 'ag_tags', ['slug'])

    # ag_embeddings
    op.create_table(
        'ag_embeddings',
        sa.Column('id', UUID(as_uuid=True), primary_key=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.Column('asset_id', UUID(as_uuid=True), sa.ForeignKey('ag_assets.id', ondelete='CASCADE'), nullable=False, unique=True),
        sa.Column('vector', JSON, nullable=False, server_default='[]'),
        sa.Column('vector_dim', sa.Integer, nullable=False, server_default='0'),
        sa.Column('source_text', sa.Text, nullable=False, server_default=''),
        sa.Column('embedding_model', sa.String(200), nullable=False, server_default='mock'),
        sa.Column('embedded_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('ag_embedding_meta', JSON, nullable=False, server_default='{}'),
    )
    op.create_index('ix_ag_embeddings_asset_id', 'ag_embeddings', ['asset_id'])

    # ag_memory
    op.create_table(
        'ag_memory',
        sa.Column('id', UUID(as_uuid=True), primary_key=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.Column('project_id', UUID(as_uuid=True), sa.ForeignKey('projects.id', ondelete='CASCADE'), nullable=False),
        sa.Column('memory_type', sa.String(100), nullable=False),
        sa.Column('scope', sa.String(100), nullable=False, server_default='global'),
        sa.Column('key', sa.String(500), nullable=False),
        sa.Column('value', JSON, nullable=False, server_default='{}'),
        sa.Column('confidence', sa.Float, nullable=False, server_default='1'),
        sa.Column('use_count', sa.Integer, nullable=False, server_default='0'),
        sa.Column('last_used_at', sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index('ix_ag_memory_project_id', 'ag_memory', ['project_id'])
    op.create_index('ix_ag_memory_memory_type', 'ag_memory', ['memory_type'])
    op.create_index('ix_ag_memory_key', 'ag_memory', ['key'])
    op.create_index('ix_ag_memory_project_type_scope', 'ag_memory', ['project_id', 'memory_type', 'scope'])

    # ag_compositions
    op.create_table(
        'ag_compositions',
        sa.Column('id', UUID(as_uuid=True), primary_key=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.Column('project_id', UUID(as_uuid=True), sa.ForeignKey('projects.id', ondelete='CASCADE'), nullable=False),
        sa.Column('scene_id', UUID(as_uuid=True), nullable=True),
        sa.Column('episode_id', UUID(as_uuid=True), nullable=True),
        sa.Column('name', sa.String(500), nullable=False, server_default=''),
        sa.Column('description', sa.Text, nullable=False, server_default=''),
        sa.Column('composition_type', sa.String(100), nullable=False, server_default='rule_of_thirds'),
        sa.Column('foreground_elements', JSON, nullable=False, server_default='[]'),
        sa.Column('midground_elements', JSON, nullable=False, server_default='[]'),
        sa.Column('background_elements', JSON, nullable=False, server_default='[]'),
        sa.Column('focus_point', sa.String(200), nullable=False, server_default=''),
        sa.Column('lighting_direction', sa.String(100), nullable=False, server_default='natural'),
        sa.Column('color_harmony', sa.String(100), nullable=False, server_default='complementary'),
        sa.Column('negative_space', sa.Float, nullable=False, server_default='0.3'),
        sa.Column('composition_prompt', sa.Text, nullable=False, server_default=''),
        sa.Column('layout_data', JSON, nullable=False, server_default='{}'),
    )
    op.create_index('ix_ag_compositions_project_id', 'ag_compositions', ['project_id'])
    op.create_index('ix_ag_compositions_scene_id', 'ag_compositions', ['scene_id'])
    op.create_index('ix_ag_compositions_episode_id', 'ag_compositions', ['episode_id'])

    # ag_camera_shots
    op.create_table(
        'ag_camera_shots',
        sa.Column('id', UUID(as_uuid=True), primary_key=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.Column('composition_id', UUID(as_uuid=True), sa.ForeignKey('ag_compositions.id', ondelete='SET NULL'), nullable=True),
        sa.Column('scene_id', UUID(as_uuid=True), nullable=True),
        sa.Column('episode_id', UUID(as_uuid=True), nullable=True),
        sa.Column('shot_type', sa.String(100), nullable=False),
        sa.Column('shot_order', sa.Integer, nullable=False, server_default='0'),
        sa.Column('description', sa.Text, nullable=False, server_default=''),
        sa.Column('camera_movement', sa.String(200), nullable=False, server_default='static'),
        sa.Column('focal_length', sa.String(50), nullable=False, server_default='50mm'),
        sa.Column('depth_of_field', sa.String(100), nullable=False, server_default='normal'),
        sa.Column('camera_prompt', sa.Text, nullable=False, server_default=''),
        sa.Column('asset_id', UUID(as_uuid=True), sa.ForeignKey('ag_assets.id', ondelete='SET NULL'), nullable=True),
        sa.Column('quality_score', sa.Float, nullable=False, server_default='0'),
        sa.Column('shot_data', JSON, nullable=False, server_default='{}'),
    )
    op.create_index('ix_ag_camera_shots_composition_id', 'ag_camera_shots', ['composition_id'])
    op.create_index('ix_ag_camera_shots_scene_id', 'ag_camera_shots', ['scene_id'])
    op.create_index('ix_ag_camera_shots_episode_id', 'ag_camera_shots', ['episode_id'])
    op.create_index('ix_ag_camera_shots_shot_type', 'ag_camera_shots', ['shot_type'])

    # ag_lighting_presets
    op.create_table(
        'ag_lighting_presets',
        sa.Column('id', UUID(as_uuid=True), primary_key=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.Column('name', sa.String(200), nullable=False),
        sa.Column('slug', sa.String(200), nullable=False, unique=True),
        sa.Column('description', sa.Text, nullable=False, server_default=''),
        sa.Column('lighting_type', sa.String(100), nullable=False, server_default='natural_day'),
        sa.Column('lighting_prompt', sa.Text, nullable=False, server_default=''),
        sa.Column('time_of_day', sa.String(50), nullable=False, server_default='day'),
        sa.Column('weather', sa.String(50), nullable=False, server_default='clear'),
        sa.Column('intensity', sa.Float, nullable=False, server_default='0.8'),
        sa.Column('color_temperature', sa.String(50), nullable=False, server_default='neutral'),
        sa.Column('is_active', sa.Boolean, nullable=False, server_default='true'),
        sa.Column('use_count', sa.Integer, nullable=False, server_default='0'),
        sa.Column('avg_quality_score', sa.Float, nullable=False, server_default='0'),
        sa.Column('preset_data', JSON, nullable=False, server_default='{}'),
    )
    op.create_index('ix_ag_lighting_presets_name', 'ag_lighting_presets', ['name'])
    op.create_index('ix_ag_lighting_presets_slug', 'ag_lighting_presets', ['slug'])
    op.create_index('ix_ag_lighting_presets_lighting_type', 'ag_lighting_presets', ['lighting_type'])

    # ag_pose_presets
    op.create_table(
        'ag_pose_presets',
        sa.Column('id', UUID(as_uuid=True), primary_key=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.Column('name', sa.String(200), nullable=False),
        sa.Column('slug', sa.String(200), nullable=False, unique=True),
        sa.Column('description', sa.Text, nullable=False, server_default=''),
        sa.Column('pose_type', sa.String(100), nullable=False, server_default='standing'),
        sa.Column('pose_prompt', sa.Text, nullable=False, server_default=''),
        sa.Column('body_orientation', sa.String(100), nullable=False, server_default='front'),
        sa.Column('is_active', sa.Boolean, nullable=False, server_default='true'),
        sa.Column('use_count', sa.Integer, nullable=False, server_default='0'),
        sa.Column('avg_quality_score', sa.Float, nullable=False, server_default='0'),
        sa.Column('pose_data', JSON, nullable=False, server_default='{}'),
    )
    op.create_index('ix_ag_pose_presets_name', 'ag_pose_presets', ['name'])
    op.create_index('ix_ag_pose_presets_slug', 'ag_pose_presets', ['slug'])
    op.create_index('ix_ag_pose_presets_pose_type', 'ag_pose_presets', ['pose_type'])

    # ag_expression_presets
    op.create_table(
        'ag_expression_presets',
        sa.Column('id', UUID(as_uuid=True), primary_key=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.Column('name', sa.String(200), nullable=False),
        sa.Column('slug', sa.String(200), nullable=False, unique=True),
        sa.Column('description', sa.Text, nullable=False, server_default=''),
        sa.Column('expression_type', sa.String(100), nullable=False, server_default='neutral'),
        sa.Column('expression_prompt', sa.Text, nullable=False, server_default=''),
        sa.Column('intensity', sa.Float, nullable=False, server_default='0.7'),
        sa.Column('is_active', sa.Boolean, nullable=False, server_default='true'),
        sa.Column('use_count', sa.Integer, nullable=False, server_default='0'),
        sa.Column('avg_quality_score', sa.Float, nullable=False, server_default='0'),
        sa.Column('expression_data', JSON, nullable=False, server_default='{}'),
    )
    op.create_index('ix_ag_expression_presets_name', 'ag_expression_presets', ['name'])
    op.create_index('ix_ag_expression_presets_slug', 'ag_expression_presets', ['slug'])
    op.create_index('ix_ag_expression_presets_expression_type', 'ag_expression_presets', ['expression_type'])

    # ag_negative_prompts
    op.create_table(
        'ag_negative_prompts',
        sa.Column('id', UUID(as_uuid=True), primary_key=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.Column('name', sa.String(200), nullable=False),
        sa.Column('content', sa.Text, nullable=False, server_default=''),
        sa.Column('category', sa.String(100), nullable=False, server_default='universal'),
        sa.Column('is_active', sa.Boolean, nullable=False, server_default='true'),
        sa.Column('priority', sa.Integer, nullable=False, server_default='0'),
        sa.Column('use_count', sa.Integer, nullable=False, server_default='0'),
    )
    op.create_index('ix_ag_negative_prompts_name', 'ag_negative_prompts', ['name'])
    op.create_index('ix_ag_negative_prompts_category', 'ag_negative_prompts', ['category'])

    # ag_prompt_history
    op.create_table(
        'ag_prompt_history',
        sa.Column('id', UUID(as_uuid=True), primary_key=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.Column('prompt_id', UUID(as_uuid=True), sa.ForeignKey('ag_prompts.id', ondelete='SET NULL'), nullable=True),
        sa.Column('asset_id', UUID(as_uuid=True), sa.ForeignKey('ag_assets.id', ondelete='SET NULL'), nullable=True),
        sa.Column('full_prompt', sa.Text, nullable=False, server_default=''),
        sa.Column('full_negative_prompt', sa.Text, nullable=False, server_default=''),
        sa.Column('quality_score', sa.Float, nullable=False, server_default='0'),
        sa.Column('was_accepted', sa.Boolean, nullable=False, server_default='false'),
        sa.Column('rejection_reasons', JSON, nullable=False, server_default='[]'),
        sa.Column('generation_params', JSON, nullable=False, server_default='{}'),
        sa.Column('executed_at', sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index('ix_ag_prompt_history_prompt_id', 'ag_prompt_history', ['prompt_id'])
    op.create_index('ix_ag_prompt_history_asset_id', 'ag_prompt_history', ['asset_id'])

    # ag_retry_queue
    op.create_table(
        'ag_retry_queue',
        sa.Column('id', UUID(as_uuid=True), primary_key=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.Column('asset_id', UUID(as_uuid=True), sa.ForeignKey('ag_assets.id', ondelete='CASCADE'), nullable=False),
        sa.Column('project_id', UUID(as_uuid=True), sa.ForeignKey('projects.id', ondelete='CASCADE'), nullable=False),
        sa.Column('failure_reason', sa.String(200), nullable=False),
        sa.Column('failure_details', sa.Text, nullable=False, server_default=''),
        sa.Column('quality_score', sa.Float, nullable=False, server_default='0'),
        sa.Column('retry_count', sa.Integer, nullable=False, server_default='0'),
        sa.Column('max_retries', sa.Integer, nullable=False, server_default='3'),
        sa.Column('status', sa.String(50), nullable=False, server_default='pending'),
        sa.Column('priority', sa.Integer, nullable=False, server_default='5'),
        sa.Column('last_retry_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('resolved_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('retry_params', JSON, nullable=False, server_default='{}'),
    )
    op.create_index('ix_ag_retry_queue_asset_id', 'ag_retry_queue', ['asset_id'])
    op.create_index('ix_ag_retry_queue_project_id', 'ag_retry_queue', ['project_id'])
    op.create_index('ix_ag_retry_queue_failure_reason', 'ag_retry_queue', ['failure_reason'])
    op.create_index('ix_ag_retry_queue_status', 'ag_retry_queue', ['status'])
    op.create_index('ix_ag_retry_queue_priority', 'ag_retry_queue', ['priority'])
    op.create_index('ix_ag_retry_queue_status_priority', 'ag_retry_queue', ['status', 'priority'])

    # ag_generation_jobs
    op.create_table(
        'ag_generation_jobs',
        sa.Column('id', UUID(as_uuid=True), primary_key=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.Column('project_id', UUID(as_uuid=True), sa.ForeignKey('projects.id', ondelete='SET NULL'), nullable=True),
        sa.Column('asset_id', UUID(as_uuid=True), sa.ForeignKey('ag_assets.id', ondelete='SET NULL'), nullable=True),
        sa.Column('episode_id', UUID(as_uuid=True), nullable=True),
        sa.Column('job_type', sa.String(100), nullable=False),
        sa.Column('status', sa.String(50), nullable=False, server_default='pending'),
        sa.Column('dispatch_mode', sa.String(50), nullable=False, server_default='sync'),
        sa.Column('celery_task_id', sa.String(500), nullable=False, server_default=''),
        sa.Column('result', JSON, nullable=False, server_default='{}'),
        sa.Column('error_message', sa.Text, nullable=False, server_default=''),
        sa.Column('started_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('completed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('duration_ms', sa.Integer, nullable=False, server_default='0'),
        sa.Column('retry_count', sa.Integer, nullable=False, server_default='0'),
        sa.Column('max_retries', sa.Integer, nullable=False, server_default='3'),
        sa.Column('params', JSON, nullable=False, server_default='{}'),
        sa.Column('ag_job_meta', JSON, nullable=False, server_default='{}'),
    )
    op.create_index('ix_ag_generation_jobs_project_id', 'ag_generation_jobs', ['project_id'])
    op.create_index('ix_ag_generation_jobs_asset_id', 'ag_generation_jobs', ['asset_id'])
    op.create_index('ix_ag_generation_jobs_episode_id', 'ag_generation_jobs', ['episode_id'])
    op.create_index('ix_ag_generation_jobs_job_type', 'ag_generation_jobs', ['job_type'])
    op.create_index('ix_ag_generation_jobs_status', 'ag_generation_jobs', ['status'])
    op.create_index('ix_ag_generation_jobs_type_status', 'ag_generation_jobs', ['job_type', 'status'])
    op.create_index('ix_ag_generation_jobs_project_status', 'ag_generation_jobs', ['project_id', 'status'])

    # ag_generation_history
    op.create_table(
        'ag_generation_history',
        sa.Column('id', UUID(as_uuid=True), primary_key=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.Column('project_id', UUID(as_uuid=True), sa.ForeignKey('projects.id', ondelete='CASCADE'), nullable=False),
        sa.Column('episode_id', UUID(as_uuid=True), nullable=True),
        sa.Column('run_type', sa.String(100), nullable=False, server_default='episode'),
        sa.Column('triggered_by', sa.String(100), nullable=False, server_default='system'),
        sa.Column('assets_planned', sa.Integer, nullable=False, server_default='0'),
        sa.Column('assets_generated', sa.Integer, nullable=False, server_default='0'),
        sa.Column('assets_accepted', sa.Integer, nullable=False, server_default='0'),
        sa.Column('assets_rejected', sa.Integer, nullable=False, server_default='0'),
        sa.Column('retries_count', sa.Integer, nullable=False, server_default='0'),
        sa.Column('avg_quality_score', sa.Float, nullable=False, server_default='0'),
        sa.Column('duration_seconds', sa.Float, nullable=False, server_default='0'),
        sa.Column('run_status', sa.String(50), nullable=False, server_default='completed'),
        sa.Column('error_summary', sa.Text, nullable=False, server_default=''),
        sa.Column('run_data', JSON, nullable=False, server_default='{}'),
        sa.Column('started_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('finished_at', sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index('ix_ag_generation_history_project_id', 'ag_generation_history', ['project_id'])
    op.create_index('ix_ag_generation_history_episode_id', 'ag_generation_history', ['episode_id'])
    op.create_index('ix_ag_generation_history_run_type', 'ag_generation_history', ['run_type'])
    op.create_index('ix_ag_generation_history_run_status', 'ag_generation_history', ['run_status'])

    # ag_cache
    op.create_table(
        'ag_cache',
        sa.Column('id', UUID(as_uuid=True), primary_key=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.Column('project_id', UUID(as_uuid=True), sa.ForeignKey('projects.id', ondelete='CASCADE'), nullable=False),
        sa.Column('asset_id', UUID(as_uuid=True), sa.ForeignKey('ag_assets.id', ondelete='CASCADE'), nullable=False),
        sa.Column('cache_key', sa.String(64), nullable=False, unique=True),
        sa.Column('asset_type', sa.String(100), nullable=False),
        sa.Column('quality_score', sa.Float, nullable=False, server_default='0'),
        sa.Column('hit_count', sa.Integer, nullable=False, server_default='0'),
        sa.Column('last_hit_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('expires_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('is_valid', sa.Boolean, nullable=False, server_default='true'),
    )
    op.create_index('ix_ag_cache_project_id', 'ag_cache', ['project_id'])
    op.create_index('ix_ag_cache_asset_id', 'ag_cache', ['asset_id'])
    op.create_index('ix_ag_cache_cache_key', 'ag_cache', ['cache_key'])
    op.create_index('ix_ag_cache_asset_type', 'ag_cache', ['asset_type'])
    op.create_index('ix_ag_cache_is_valid', 'ag_cache', ['is_valid'])

    # ag_relationships
    op.create_table(
        'ag_relationships',
        sa.Column('id', UUID(as_uuid=True), primary_key=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.Column('source_asset_id', UUID(as_uuid=True), sa.ForeignKey('ag_assets.id', ondelete='CASCADE'), nullable=False),
        sa.Column('target_asset_id', UUID(as_uuid=True), sa.ForeignKey('ag_assets.id', ondelete='CASCADE'), nullable=False),
        sa.Column('relationship_type', sa.String(100), nullable=False),
        sa.Column('strength', sa.Float, nullable=False, server_default='1'),
        sa.Column('ag_rel_meta', JSON, nullable=False, server_default='{}'),
    )
    op.create_index('ix_ag_relationships_source_asset_id', 'ag_relationships', ['source_asset_id'])
    op.create_index('ix_ag_relationships_target_asset_id', 'ag_relationships', ['target_asset_id'])
    op.create_index('ix_ag_relationships_relationship_type', 'ag_relationships', ['relationship_type'])
    op.create_index('ix_ag_relationships_source_type', 'ag_relationships', ['source_asset_id', 'relationship_type'])
    op.create_unique_constraint(
        'uq_ag_relationships_src_tgt_type', 'ag_relationships',
        ['source_asset_id', 'target_asset_id', 'relationship_type']
    )


def downgrade() -> None:
    op.drop_table('ag_relationships')
    op.drop_table('ag_cache')
    op.drop_table('ag_generation_history')
    op.drop_table('ag_generation_jobs')
    op.drop_table('ag_retry_queue')
    op.drop_table('ag_prompt_history')
    op.drop_table('ag_negative_prompts')
    op.drop_table('ag_expression_presets')
    op.drop_table('ag_pose_presets')
    op.drop_table('ag_lighting_presets')
    op.drop_table('ag_camera_shots')
    op.drop_table('ag_compositions')
    op.drop_table('ag_memory')
    op.drop_table('ag_embeddings')
    op.drop_table('ag_tags')
    op.drop_table('ag_evaluations')
    op.drop_table('ag_generated_images')
    op.drop_table('ag_versions')
    op.drop_table('ag_prompts')
    op.drop_table('ag_prompt_templates')
    op.drop_table('ag_assets')
    op.drop_table('ag_collections')
    op.drop_table('ag_projects')
    op.drop_table('ag_styles')

"""phase7_animation_engine

Revision ID: f1a2b3c4d5e6
Revises: e31c0776919b
Create Date: 2026-07-13 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID, JSON

revision: str = 'f1a2b3c4d5e6'
down_revision: Union[str, None] = 'e31c0776919b'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # an_jobs — must be created first (an_render_outputs + an_retry_queue FK here)
    op.create_table(
        'an_jobs',
        sa.Column('id', UUID(as_uuid=True), primary_key=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.Column('project_id', UUID(as_uuid=True), sa.ForeignKey('projects.id', ondelete='CASCADE'), nullable=False),
        sa.Column('scene_id', UUID(as_uuid=True), nullable=True),
        sa.Column('episode_id', UUID(as_uuid=True), nullable=True),
        sa.Column('job_type', sa.String(100), nullable=False),
        sa.Column('status', sa.String(50), nullable=False, server_default='pending'),
        sa.Column('mode', sa.String(20), nullable=False, server_default='sync'),
        sa.Column('triggered_by', sa.String(100), nullable=False, server_default='api'),
        sa.Column('params', JSON, nullable=False, server_default='{}'),
        sa.Column('result', JSON, nullable=False, server_default='{}'),
        sa.Column('error_message', sa.Text, nullable=False, server_default=''),
        sa.Column('started_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('completed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('duration_seconds', sa.Float, nullable=True),
    )
    op.create_index('ix_an_jobs_project_id', 'an_jobs', ['project_id'])
    op.create_index('ix_an_jobs_scene_id', 'an_jobs', ['scene_id'])
    op.create_index('ix_an_jobs_episode_id', 'an_jobs', ['episode_id'])
    op.create_index('ix_an_jobs_job_type', 'an_jobs', ['job_type'])
    op.create_index('ix_an_jobs_status', 'an_jobs', ['status'])
    op.create_index('ix_an_jobs_project_status', 'an_jobs', ['project_id', 'status'])
    op.create_index('ix_an_jobs_project_type', 'an_jobs', ['project_id', 'job_type'])

    # an_render_outputs
    op.create_table(
        'an_render_outputs',
        sa.Column('id', UUID(as_uuid=True), primary_key=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.Column('job_id', UUID(as_uuid=True), sa.ForeignKey('an_jobs.id', ondelete='CASCADE'), nullable=False),
        sa.Column('project_id', UUID(as_uuid=True), sa.ForeignKey('projects.id', ondelete='CASCADE'), nullable=False),
        sa.Column('scene_id', UUID(as_uuid=True), nullable=True),
        sa.Column('episode_id', UUID(as_uuid=True), nullable=True),
        sa.Column('output_type', sa.String(100), nullable=False, server_default='scene_clip'),
        sa.Column('status', sa.String(50), nullable=False, server_default='pending'),
        sa.Column('storage_key', sa.String(2000), nullable=False, server_default=''),
        sa.Column('storage_bucket', sa.String(500), nullable=False, server_default='animations'),
        sa.Column('file_size_bytes', sa.BigInteger, nullable=False, server_default='0'),
        sa.Column('duration_seconds', sa.Float, nullable=False, server_default='0'),
        sa.Column('width', sa.Integer, nullable=False, server_default='1920'),
        sa.Column('height', sa.Integer, nullable=False, server_default='1080'),
        sa.Column('fps', sa.Integer, nullable=False, server_default='24'),
        sa.Column('format', sa.String(20), nullable=False, server_default='mp4'),
        sa.Column('provider', sa.String(100), nullable=False, server_default='mock'),
        sa.Column('render_params', JSON, nullable=False, server_default='{}'),
        sa.Column('an_render_output_meta', JSON, nullable=False, server_default='{}'),
    )
    op.create_index('ix_an_render_outputs_job_id', 'an_render_outputs', ['job_id'])
    op.create_index('ix_an_render_outputs_project_id', 'an_render_outputs', ['project_id'])
    op.create_index('ix_an_render_outputs_scene_id', 'an_render_outputs', ['scene_id'])
    op.create_index('ix_an_render_outputs_episode_id', 'an_render_outputs', ['episode_id'])
    op.create_index('ix_an_render_outputs_output_type', 'an_render_outputs', ['output_type'])
    op.create_index('ix_an_render_outputs_status', 'an_render_outputs', ['status'])
    op.create_index('ix_an_render_outputs_project_type', 'an_render_outputs', ['project_id', 'output_type'])

    # an_retry_queue
    op.create_table(
        'an_retry_queue',
        sa.Column('id', UUID(as_uuid=True), primary_key=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.Column('project_id', UUID(as_uuid=True), sa.ForeignKey('projects.id', ondelete='CASCADE'), nullable=False),
        sa.Column('scene_id', UUID(as_uuid=True), nullable=True),
        sa.Column('episode_id', UUID(as_uuid=True), nullable=True),
        sa.Column('original_job_id', UUID(as_uuid=True), sa.ForeignKey('an_jobs.id', ondelete='SET NULL'), nullable=True),
        sa.Column('retry_count', sa.Integer, nullable=False, server_default='0'),
        sa.Column('max_retries', sa.Integer, nullable=False, server_default='3'),
        sa.Column('status', sa.String(50), nullable=False, server_default='pending'),
        sa.Column('reason', sa.Text, nullable=False, server_default=''),
        sa.Column('next_retry_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('resolved_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('params', JSON, nullable=False, server_default='{}'),
    )
    op.create_index('ix_an_retry_queue_project_id', 'an_retry_queue', ['project_id'])
    op.create_index('ix_an_retry_queue_scene_id', 'an_retry_queue', ['scene_id'])
    op.create_index('ix_an_retry_queue_episode_id', 'an_retry_queue', ['episode_id'])
    op.create_index('ix_an_retry_queue_status', 'an_retry_queue', ['status'])
    op.create_index('ix_an_retry_queue_project_status', 'an_retry_queue', ['project_id', 'status'])


def downgrade() -> None:
    op.drop_table('an_retry_queue')
    op.drop_table('an_render_outputs')
    op.drop_table('an_jobs')

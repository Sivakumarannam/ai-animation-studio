"""phase10_video_assembly_engine

Revision ID: a1b2c3d4e5f6
Revises: e5a09bad3ab4
Create Date: 2026-07-17

Phase 10 — Video Assembly Engine
Creates: va_jobs, va_outputs, va_retry_queue
"""
from __future__ import annotations

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "a1b2c3d4e5f6"
down_revision = "e5a09bad3ab4"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ------------------------------------------------------------------ va_jobs
    op.create_table(
        "va_jobs",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("project_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("episode_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("job_type", sa.String(50), nullable=False, server_default="assemble_episode"),
        sa.Column("status", sa.String(50), nullable=False, server_default="pending"),
        sa.Column("mode", sa.String(20), nullable=False, server_default="sync"),
        sa.Column("triggered_by", sa.String(100), nullable=False, server_default="api"),
        sa.Column("params", sa.JSON(), nullable=False, server_default="{}"),
        sa.Column("result", sa.JSON(), nullable=True),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("duration_seconds", sa.Float(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
    )
    op.create_index("ix_va_jobs_project_id", "va_jobs", ["project_id"])
    op.create_index("ix_va_jobs_status", "va_jobs", ["status"])
    op.create_index("ix_va_jobs_episode_id", "va_jobs", ["episode_id"])
    op.create_index("ix_va_jobs_project_status", "va_jobs", ["project_id", "status"])

    # --------------------------------------------------------------- va_outputs
    op.create_table(
        "va_outputs",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("job_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("va_jobs.id", ondelete="CASCADE"), nullable=False),
        sa.Column("project_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("episode_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("output_type", sa.String(100), nullable=False, server_default="episode_cut"),
        sa.Column("status", sa.String(50), nullable=False, server_default="completed"),
        sa.Column("storage_key", sa.String(2000), nullable=False, server_default=""),
        sa.Column("storage_bucket", sa.String(500), nullable=False, server_default="videos"),
        sa.Column("file_size_bytes", sa.BigInteger(), nullable=False, server_default="0"),
        sa.Column("duration_seconds", sa.Float(), nullable=False, server_default="0"),
        sa.Column("width", sa.Integer(), nullable=False, server_default="1920"),
        sa.Column("height", sa.Integer(), nullable=False, server_default="1080"),
        sa.Column("fps", sa.Integer(), nullable=False, server_default="24"),
        sa.Column("format", sa.String(20), nullable=False, server_default="mp4"),
        sa.Column("provider", sa.String(100), nullable=False, server_default="mock"),
        sa.Column("scene_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("has_voice", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("has_music", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("has_subtitles", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("quality_passed", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("quality_score", sa.Float(), nullable=False, server_default="100"),
        sa.Column("va_output_meta", sa.JSON(), nullable=False, server_default="{}"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
    )
    op.create_index("ix_va_outputs_project_id", "va_outputs", ["project_id"])
    op.create_index("ix_va_outputs_job_id", "va_outputs", ["job_id"])
    op.create_index("ix_va_outputs_episode_id", "va_outputs", ["episode_id"])
    op.create_index("ix_va_outputs_output_type", "va_outputs", ["output_type"])

    # ---------------------------------------------------------- va_retry_queue
    op.create_table(
        "va_retry_queue",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("project_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("episode_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("original_job_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("status", sa.String(50), nullable=False, server_default="pending"),
        sa.Column("retry_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("max_retries", sa.Integer(), nullable=False, server_default="3"),
        sa.Column("reason", sa.Text(), nullable=False, server_default=""),
        sa.Column("params", sa.JSON(), nullable=False, server_default="{}"),
        sa.Column("next_retry_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("resolved_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
    )
    op.create_index("ix_va_retry_queue_project_id", "va_retry_queue", ["project_id"])
    op.create_index("ix_va_retry_queue_status", "va_retry_queue", ["status"])
    op.create_index("ix_va_retry_queue_project_status", "va_retry_queue", ["project_id", "status"])


def downgrade() -> None:
    op.drop_table("va_retry_queue")
    op.drop_table("va_outputs")
    op.drop_table("va_jobs")

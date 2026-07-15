"""phase8_voice_engine

Revision ID: a2b3c4d5e6f7
Revises: f1a2b3c4d5e6
Create Date: 2026-07-15

Creates:
  vo_jobs           — voice generation jobs
  vo_outputs        — generated audio clips (one per dialogue line)
  vo_retry_queue    — failed lines pending retry
"""
from __future__ import annotations

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision = "a2b3c4d5e6f7"
down_revision = "f1a2b3c4d5e6"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # -------------------------------------------------------------------------
    # vo_jobs
    # -------------------------------------------------------------------------
    op.create_table(
        "vo_jobs",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("project_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("scene_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("episode_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("character_id", sa.String(255), nullable=True),
        sa.Column("job_type", sa.String(50), nullable=False, server_default="generate_line"),
        sa.Column("status", sa.String(50), nullable=False, server_default="pending"),
        sa.Column("triggered_by", sa.String(100), nullable=False, server_default="api"),
        sa.Column("params", sa.JSON(), nullable=False, server_default="{}"),
        sa.Column("result", sa.JSON(), nullable=True),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
    )
    op.create_index("ix_vo_jobs_project_id", "vo_jobs", ["project_id"])
    op.create_index("ix_vo_jobs_status", "vo_jobs", ["status"])
    op.create_index("ix_vo_jobs_scene_id", "vo_jobs", ["scene_id"])
    op.create_index("ix_vo_jobs_episode_id", "vo_jobs", ["episode_id"])

    # -------------------------------------------------------------------------
    # vo_outputs
    # -------------------------------------------------------------------------
    op.create_table(
        "vo_outputs",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "job_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("vo_jobs.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("project_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("scene_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("character_id", sa.String(255), nullable=True),
        sa.Column("character_name", sa.String(255), nullable=True),
        sa.Column("dialogue_line", sa.Text(), nullable=False, server_default=""),
        sa.Column("language", sa.String(20), nullable=False, server_default="en"),
        sa.Column("emotion", sa.String(50), nullable=False, server_default="neutral"),
        sa.Column("voice_id", sa.String(255), nullable=True),
        sa.Column("storage_key", sa.String(1024), nullable=False, server_default=""),
        sa.Column("duration_seconds", sa.Float(), nullable=False, server_default="0.0"),
        sa.Column("sample_rate", sa.Integer(), nullable=False, server_default="22050"),
        sa.Column("format", sa.String(20), nullable=False, server_default="wav"),
        sa.Column("file_size_bytes", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("provider", sa.String(100), nullable=False, server_default="mock"),
        sa.Column("status", sa.String(50), nullable=False, server_default="completed"),
        sa.Column("vo_output_meta", sa.JSON(), nullable=False, server_default="{}"),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
    )
    op.create_index("ix_vo_outputs_project_id", "vo_outputs", ["project_id"])
    op.create_index("ix_vo_outputs_job_id", "vo_outputs", ["job_id"])
    op.create_index("ix_vo_outputs_scene_id", "vo_outputs", ["scene_id"])
    op.create_index("ix_vo_outputs_character_id", "vo_outputs", ["character_id"])

    # -------------------------------------------------------------------------
    # vo_retry_queue
    # -------------------------------------------------------------------------
    op.create_table(
        "vo_retry_queue",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("project_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("scene_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("episode_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("original_job_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("status", sa.String(50), nullable=False, server_default="pending"),
        sa.Column("retry_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("max_retries", sa.Integer(), nullable=False, server_default="3"),
        sa.Column("reason", sa.Text(), nullable=False, server_default=""),
        sa.Column("params", sa.JSON(), nullable=False, server_default="{}"),
        sa.Column("next_retry_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
    )
    op.create_index("ix_vo_retry_queue_project_id", "vo_retry_queue", ["project_id"])
    op.create_index("ix_vo_retry_queue_status", "vo_retry_queue", ["status"])


def downgrade() -> None:
    op.drop_table("vo_retry_queue")
    op.drop_table("vo_outputs")
    op.drop_table("vo_jobs")

"""phase9_music_sound_engine

Revision ID: e5a09bad3ab4
Revises: a2b3c4d5e6f7
Create Date: 2026-07-17 07:33:57.185628

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "e5a09bad3ab4"
down_revision: Union[str, None] = "a2b3c4d5e6f7"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


# ---------------------------------------------------------------------------
# Pre-seeded SFX entries (inserted on upgrade, removed on downgrade)
# ---------------------------------------------------------------------------

SFX_ENTRIES = [
    ("footsteps_wood", "Footsteps on Wood", "Movement of character walking on a wooden floor", "movement", ["footsteps", "wood", "walk"], "sfx/builtin/footsteps_wood.wav", 2.0),
    ("footsteps_grass", "Footsteps on Grass", "Soft footsteps on grassy ground", "movement", ["footsteps", "grass", "outdoor"], "sfx/builtin/footsteps_grass.wav", 1.8),
    ("footsteps_concrete", "Footsteps on Concrete", "Hard footsteps on concrete or tile", "movement", ["footsteps", "concrete", "hard"], "sfx/builtin/footsteps_concrete.wav", 2.0),
    ("door_open_creak", "Door Opening (Creak)", "Old wooden door opening with a creak", "environment", ["door", "creak", "open"], "sfx/builtin/door_open_creak.wav", 1.5),
    ("door_close_slam", "Door Slamming", "Door closing with a hard slam", "environment", ["door", "slam", "close"], "sfx/builtin/door_close_slam.wav", 0.8),
    ("door_knock", "Door Knock", "Three quick knocks on a wooden door", "environment", ["door", "knock"], "sfx/builtin/door_knock.wav", 1.2),
    ("notification_soft", "Soft Notification", "Gentle chime notification sound", "ui", ["notification", "chime", "soft"], "sfx/builtin/notification_soft.wav", 0.5),
    ("notification_alert", "Alert Notification", "Urgent alert notification sound", "ui", ["notification", "alert", "urgent"], "sfx/builtin/notification_alert.wav", 0.7),
    ("comedy_sting_boing", "Comedy Boing", "Cartoon boing sound for comedy moments", "comedy", ["comedy", "cartoon", "boing"], "sfx/builtin/comedy_boing.wav", 0.8),
    ("comedy_sting_slide", "Comedy Slide Whistle", "Descending slide whistle for comic timing", "comedy", ["comedy", "slide", "whistle"], "sfx/builtin/comedy_slide_whistle.wav", 1.0),
    ("comedy_sting_fail", "Fail Trombone", "Wah-wah-wah failure sting", "comedy", ["comedy", "fail", "trombone"], "sfx/builtin/comedy_fail_trombone.wav", 2.0),
    ("victory_fanfare", "Victory Fanfare", "Short triumphant brass fanfare", "drama", ["victory", "fanfare", "triumph"], "sfx/builtin/victory_fanfare.wav", 3.0),
    ("defeat_sting", "Defeat Sting", "Somber defeat sting", "drama", ["defeat", "sad", "sting"], "sfx/builtin/defeat_sting.wav", 2.5),
    ("crowd_cheer", "Crowd Cheer", "Audience cheering and applause", "crowd", ["crowd", "cheer", "applause"], "sfx/builtin/crowd_cheer.wav", 4.0),
    ("crowd_gasp", "Crowd Gasp", "Audience collective gasp of surprise", "crowd", ["crowd", "gasp", "surprise"], "sfx/builtin/crowd_gasp.wav", 1.5),
]


def upgrade() -> None:
    # ── mu_jobs ───────────────────────────────────────────────────────────────
    op.create_table(
        "mu_jobs",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("project_id", sa.UUID(), nullable=False),
        sa.Column("scene_id", sa.UUID(), nullable=True),
        sa.Column("episode_id", sa.UUID(), nullable=True),
        sa.Column(
            "job_type",
            sa.String(length=100),
            server_default=sa.text("'generate_track'"),
            nullable=False,
        ),
        sa.Column(
            "mood",
            sa.String(length=50),
            server_default=sa.text("'neutral'"),
            nullable=False,
        ),
        sa.Column(
            "status",
            sa.String(length=50),
            server_default=sa.text("'pending'"),
            nullable=False,
        ),
        sa.Column(
            "triggered_by",
            sa.String(length=100),
            server_default=sa.text("'api'"),
            nullable=False,
        ),
        sa.Column(
            "params",
            postgresql.JSON(astext_type=sa.Text()),
            server_default=sa.text("'{}'::json"),
            nullable=False,
        ),
        sa.Column("result", postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["project_id"], ["projects.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_mu_jobs_project_id", "mu_jobs", ["project_id"])
    op.create_index("ix_mu_jobs_scene_id", "mu_jobs", ["scene_id"])
    op.create_index("ix_mu_jobs_episode_id", "mu_jobs", ["episode_id"])
    op.create_index("ix_mu_jobs_status", "mu_jobs", ["status"])
    op.create_index("ix_mu_jobs_project_status", "mu_jobs", ["project_id", "status"])
    op.create_index("ix_mu_jobs_mood", "mu_jobs", ["mood"])

    # ── mu_outputs ────────────────────────────────────────────────────────────
    op.create_table(
        "mu_outputs",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("job_id", sa.UUID(), nullable=False),
        sa.Column("project_id", sa.UUID(), nullable=False),
        sa.Column("scene_id", sa.UUID(), nullable=True),
        sa.Column("episode_id", sa.UUID(), nullable=True),
        sa.Column(
            "output_type",
            sa.String(length=100),
            server_default=sa.text("'background_music'"),
            nullable=False,
        ),
        sa.Column(
            "mood",
            sa.String(length=50),
            server_default=sa.text("'neutral'"),
            nullable=False,
        ),
        sa.Column(
            "loop_type",
            sa.String(length=50),
            server_default=sa.text("'looping'"),
            nullable=False,
        ),
        sa.Column(
            "storage_key",
            sa.String(length=2000),
            server_default=sa.text("''"),
            nullable=False,
        ),
        sa.Column(
            "duration_seconds",
            sa.Float(),
            server_default=sa.text("0"),
            nullable=False,
        ),
        sa.Column(
            "sample_rate",
            sa.Integer(),
            server_default=sa.text("44100"),
            nullable=False,
        ),
        sa.Column(
            "format",
            sa.String(length=20),
            server_default=sa.text("'wav'"),
            nullable=False,
        ),
        sa.Column(
            "file_size_bytes",
            sa.BigInteger(),
            server_default=sa.text("0"),
            nullable=False,
        ),
        sa.Column(
            "provider",
            sa.String(length=100),
            server_default=sa.text("'mock'"),
            nullable=False,
        ),
        sa.Column(
            "copyright_safe",
            sa.Boolean(),
            server_default=sa.text("true"),
            nullable=False,
        ),
        sa.Column(
            "status",
            sa.String(length=50),
            server_default=sa.text("'completed'"),
            nullable=False,
        ),
        sa.Column(
            "mu_output_meta",
            postgresql.JSON(astext_type=sa.Text()),
            server_default=sa.text("'{}'::json"),
            nullable=False,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["job_id"], ["mu_jobs.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["project_id"], ["projects.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_mu_outputs_job_id", "mu_outputs", ["job_id"])
    op.create_index("ix_mu_outputs_project_id", "mu_outputs", ["project_id"])
    op.create_index("ix_mu_outputs_scene_id", "mu_outputs", ["scene_id"])
    op.create_index("ix_mu_outputs_episode_id", "mu_outputs", ["episode_id"])
    op.create_index("ix_mu_outputs_mood", "mu_outputs", ["mood"])

    # ── mu_sfx_assets ─────────────────────────────────────────────────────────
    op.create_table(
        "mu_sfx_assets",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("sfx_key", sa.String(length=200), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("description", sa.Text(), server_default=sa.text("''"), nullable=False),
        sa.Column("category", sa.String(length=100), server_default=sa.text("'misc'"), nullable=False),
        sa.Column(
            "tags",
            postgresql.JSON(astext_type=sa.Text()),
            server_default=sa.text("'[]'::json"),
            nullable=False,
        ),
        sa.Column("storage_key", sa.String(length=2000), server_default=sa.text("''"), nullable=False),
        sa.Column("duration_seconds", sa.Float(), server_default=sa.text("0"), nullable=False),
        sa.Column("format", sa.String(length=20), server_default=sa.text("'wav'"), nullable=False),
        sa.Column("sample_rate", sa.Integer(), server_default=sa.text("44100"), nullable=False),
        sa.Column("is_builtin", sa.Boolean(), server_default=sa.text("true"), nullable=False),
        sa.Column("is_active", sa.Boolean(), server_default=sa.text("true"), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("sfx_key", name="mu_sfx_assets_sfx_key_key"),
    )
    op.create_index("ix_mu_sfx_assets_sfx_key", "mu_sfx_assets", ["sfx_key"])
    op.create_index("ix_mu_sfx_assets_category", "mu_sfx_assets", ["category"])
    op.create_index("ix_mu_sfx_assets_is_active", "mu_sfx_assets", ["is_active"])

    # ── mu_retry_queue ────────────────────────────────────────────────────────
    op.create_table(
        "mu_retry_queue",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("project_id", sa.UUID(), nullable=False),
        sa.Column("scene_id", sa.UUID(), nullable=True),
        sa.Column("episode_id", sa.UUID(), nullable=True),
        sa.Column("original_job_id", sa.UUID(), nullable=True),
        sa.Column(
            "status",
            sa.String(length=50),
            server_default=sa.text("'pending'"),
            nullable=False,
        ),
        sa.Column("retry_count", sa.Integer(), server_default=sa.text("0"), nullable=False),
        sa.Column("max_retries", sa.Integer(), server_default=sa.text("3"), nullable=False),
        sa.Column("reason", sa.Text(), server_default=sa.text("''"), nullable=False),
        sa.Column(
            "params",
            postgresql.JSON(astext_type=sa.Text()),
            server_default=sa.text("'{}'::json"),
            nullable=False,
        ),
        sa.Column("next_retry_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("resolved_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["original_job_id"], ["mu_jobs.id"], ondelete="SET NULL"
        ),
        sa.ForeignKeyConstraint(["project_id"], ["projects.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_mu_retry_queue_project_id", "mu_retry_queue", ["project_id"])
    op.create_index("ix_mu_retry_queue_status", "mu_retry_queue", ["status"])
    op.create_index(
        "ix_mu_retry_queue_project_status",
        "mu_retry_queue",
        ["project_id", "status"],
    )

    # ── seed SFX library ──────────────────────────────────────────────────────
    import uuid as _uuid

    mu_sfx_assets = sa.table(
        "mu_sfx_assets",
        sa.column("id", sa.UUID()),
        sa.column("sfx_key", sa.String()),
        sa.column("name", sa.String()),
        sa.column("description", sa.Text()),
        sa.column("category", sa.String()),
        sa.column("tags", postgresql.JSON()),
        sa.column("storage_key", sa.String()),
        sa.column("duration_seconds", sa.Float()),
        sa.column("is_builtin", sa.Boolean()),
        sa.column("is_active", sa.Boolean()),
    )
    op.bulk_insert(
        mu_sfx_assets,
        [
            {
                "id": str(_uuid.uuid4()),
                "sfx_key": sfx_key,
                "name": name,
                "description": description,
                "category": category,
                "tags": tags,
                "storage_key": storage_key,
                "duration_seconds": duration,
                "is_builtin": True,
                "is_active": True,
            }
            for sfx_key, name, description, category, tags, storage_key, duration in SFX_ENTRIES
        ],
    )


def downgrade() -> None:
    op.drop_table("mu_retry_queue")
    op.drop_index("ix_mu_sfx_assets_is_active", table_name="mu_sfx_assets")
    op.drop_index("ix_mu_sfx_assets_category", table_name="mu_sfx_assets")
    op.drop_index("ix_mu_sfx_assets_sfx_key", table_name="mu_sfx_assets")
    op.drop_table("mu_sfx_assets")
    op.drop_index("ix_mu_outputs_mood", table_name="mu_outputs")
    op.drop_index("ix_mu_outputs_episode_id", table_name="mu_outputs")
    op.drop_index("ix_mu_outputs_scene_id", table_name="mu_outputs")
    op.drop_index("ix_mu_outputs_project_id", table_name="mu_outputs")
    op.drop_index("ix_mu_outputs_job_id", table_name="mu_outputs")
    op.drop_table("mu_outputs")
    op.drop_index("ix_mu_jobs_mood", table_name="mu_jobs")
    op.drop_index("ix_mu_jobs_project_status", table_name="mu_jobs")
    op.drop_index("ix_mu_jobs_status", table_name="mu_jobs")
    op.drop_index("ix_mu_jobs_episode_id", table_name="mu_jobs")
    op.drop_index("ix_mu_jobs_scene_id", table_name="mu_jobs")
    op.drop_index("ix_mu_jobs_project_id", table_name="mu_jobs")
    op.drop_table("mu_jobs")

"""add asset management libraries

Revision ID: a6a68de3e40e
Revises: 13f55ed28352
Create Date: 2026-07-04 18:31:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = 'a6a68de3e40e'
down_revision: Union[str, None] = '13f55ed28352'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Alter character_templates
    op.add_column('character_templates', sa.Column('is_deleted', sa.Boolean(), nullable=False, server_default='false'))

    # 2. Alter backgrounds
    op.add_column('backgrounds', sa.Column('is_deleted', sa.Boolean(), nullable=False, server_default='false'))
    op.add_column('backgrounds', sa.Column('metadata', sa.JSON(), nullable=False, server_default='{}'))

    # 3. Alter props
    op.add_column('props', sa.Column('is_deleted', sa.Boolean(), nullable=False, server_default='false'))
    op.add_column('props', sa.Column('metadata', sa.JSON(), nullable=False, server_default='{}'))

    # 4. Alter animation_presets
    op.add_column('animation_presets', sa.Column('is_deleted', sa.Boolean(), nullable=False, server_default='false'))
    op.add_column('animation_presets', sa.Column('tags', sa.JSON(), nullable=False, server_default='[]'))
    op.add_column('animation_presets', sa.Column('metadata', sa.JSON(), nullable=False, server_default='{}'))

    # 5. Create audio table
    op.create_table('audio',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('category', sa.String(length=100), nullable=False, server_default=''),
        sa.Column('tags', sa.JSON(), nullable=False, server_default='[]'),
        sa.Column('file_url', sa.String(length=500), nullable=False, server_default=''),
        sa.Column('preview_url', sa.String(length=500), nullable=False, server_default=''),
        sa.Column('duration_seconds', sa.Float(), nullable=False, server_default='0.0'),
        sa.Column('is_library', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('project_id', sa.UUID(), nullable=True),
        sa.Column('is_deleted', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('metadata', sa.JSON(), nullable=False, server_default='{}'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )

    # 6. Create music table
    op.create_table('music',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('category', sa.String(length=100), nullable=False, server_default=''),
        sa.Column('tags', sa.JSON(), nullable=False, server_default='[]'),
        sa.Column('file_url', sa.String(length=500), nullable=False, server_default=''),
        sa.Column('preview_url', sa.String(length=500), nullable=False, server_default=''),
        sa.Column('duration_seconds', sa.Float(), nullable=False, server_default='0.0'),
        sa.Column('is_library', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('project_id', sa.UUID(), nullable=True),
        sa.Column('is_deleted', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('metadata', sa.JSON(), nullable=False, server_default='{}'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )

    # 7. Create sound_effects table
    op.create_table('sound_effects',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('category', sa.String(length=100), nullable=False, server_default=''),
        sa.Column('tags', sa.JSON(), nullable=False, server_default='[]'),
        sa.Column('file_url', sa.String(length=500), nullable=False, server_default=''),
        sa.Column('preview_url', sa.String(length=500), nullable=False, server_default=''),
        sa.Column('duration_seconds', sa.Float(), nullable=False, server_default='0.0'),
        sa.Column('is_library', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('project_id', sa.UUID(), nullable=True),
        sa.Column('is_deleted', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('metadata', sa.JSON(), nullable=False, server_default='{}'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )


def downgrade() -> None:
    op.drop_table('sound_effects')
    op.drop_table('music')
    op.drop_table('audio')
    op.drop_column('animation_presets', 'metadata')
    op.drop_column('animation_presets', 'tags')
    op.drop_column('animation_presets', 'is_deleted')
    op.drop_column('props', 'metadata')
    op.drop_column('props', 'is_deleted')
    op.drop_column('backgrounds', 'metadata')
    op.drop_column('backgrounds', 'is_deleted')
    op.drop_column('character_templates', 'is_deleted')

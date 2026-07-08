"""kn_collections_documents_project_id_nullable

Revision ID: d99cb779fee9
Revises: b2f7a9e1c304
Create Date: 2026-07-08 06:52:48.652587

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = 'd99cb779fee9'
down_revision: Union[str, None] = 'b2f7a9e1c304'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.alter_column("kn_collections", "project_id", existing_type=sa.UUID(), nullable=True)
    op.alter_column("kn_documents", "project_id", existing_type=sa.UUID(), nullable=True)


def downgrade() -> None:
    op.alter_column("kn_documents", "project_id", existing_type=sa.UUID(), nullable=False)
    op.alter_column("kn_collections", "project_id", existing_type=sa.UUID(), nullable=False)

"""merge_phase6_and_kn_nullable_fix

Revision ID: e31c0776919b
Revises: c4e1f2a3b5d6, d99cb779fee9
Create Date: 2026-07-11 17:37:27.518763

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = 'e31c0776919b'
down_revision: Union[str, None] = ('c4e1f2a3b5d6', 'd99cb779fee9')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass

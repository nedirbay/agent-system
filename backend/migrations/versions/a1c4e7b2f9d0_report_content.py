"""report content

Revision ID: a1c4e7b2f9d0
Revises: 9efe1a3fd119
Create Date: 2026-06-13 10:00:00.000000
"""
from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa


revision: str = 'a1c4e7b2f9d0'
down_revision: str | None = '9efe1a3fd119'
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column('reports', sa.Column('content', sa.Text(), nullable=True))


def downgrade() -> None:
    op.drop_column('reports', 'content')

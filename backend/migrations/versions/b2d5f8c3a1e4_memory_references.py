"""memory references

Revision ID: b2d5f8c3a1e4
Revises: a1c4e7b2f9d0
Create Date: 2026-06-13 12:00:00.000000
"""
from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa


revision: str = 'b2d5f8c3a1e4'
down_revision: str | None = 'a1c4e7b2f9d0'
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        'memory_references',
        sa.Column('id', sa.Uuid(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('memory_id', sa.Uuid(), nullable=False),
        sa.Column('related_entity_type', sa.String(length=255), nullable=True),
        sa.Column('related_entity_id', sa.Uuid(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(
        op.f('ix_memory_references_memory_id'),
        'memory_references',
        ['memory_id'],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(op.f('ix_memory_references_memory_id'), table_name='memory_references')
    op.drop_table('memory_references')

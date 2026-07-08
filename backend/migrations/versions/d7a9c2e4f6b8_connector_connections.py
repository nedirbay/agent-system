"""connector connections

Revision ID: d7a9c2e4f6b8
Revises: c3f6a9d2b1e5
Create Date: 2026-06-13 14:00:00.000000
"""
from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa


revision: str = 'd7a9c2e4f6b8'
down_revision: str | None = 'c3f6a9d2b1e5'
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        'connector_connections',
        sa.Column('id', sa.Uuid(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('user_id', sa.Uuid(), nullable=True),
        sa.Column('connector_type', sa.String(length=64), nullable=False),
        sa.Column('label', sa.String(length=255), nullable=False),
        sa.Column('status', sa.String(length=32), nullable=False),
        sa.Column('config', sa.JSON(), nullable=False),
        sa.Column('secret_ciphertext', sa.Text(), nullable=True),
        sa.Column('secret_hint', sa.String(length=64), nullable=True),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(
        op.f('ix_connector_connections_user_id'),
        'connector_connections',
        ['user_id'],
        unique=False,
    )
    op.create_index(
        op.f('ix_connector_connections_connector_type'),
        'connector_connections',
        ['connector_type'],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(
        op.f('ix_connector_connections_connector_type'),
        table_name='connector_connections',
    )
    op.drop_index(
        op.f('ix_connector_connections_user_id'),
        table_name='connector_connections',
    )
    op.drop_table('connector_connections')

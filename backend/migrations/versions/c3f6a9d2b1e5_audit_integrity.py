"""audit trail integrity columns

Adds actor_type, correlation_id and the tamper-evident hash-chain columns
(prev_hash, entry_hash) to audit_logs, plus query indexes on entity_type and
action (Faza 9 Task 29 / AUD-001..004).

Revision ID: c3f6a9d2b1e5
Revises: b2d5f8c3a1e4
Create Date: 2026-06-13 13:00:00.000000
"""
from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa


revision: str = 'c3f6a9d2b1e5'
down_revision: str | None = 'b2d5f8c3a1e4'
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column('audit_logs', sa.Column('actor_type', sa.String(length=32), nullable=True))
    op.add_column('audit_logs', sa.Column('correlation_id', sa.String(length=64), nullable=True))
    op.add_column('audit_logs', sa.Column('prev_hash', sa.String(length=64), nullable=True))
    op.add_column('audit_logs', sa.Column('entry_hash', sa.String(length=64), nullable=True))
    op.create_index(op.f('ix_audit_logs_entity_type'), 'audit_logs', ['entity_type'], unique=False)
    op.create_index(op.f('ix_audit_logs_action'), 'audit_logs', ['action'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_audit_logs_action'), table_name='audit_logs')
    op.drop_index(op.f('ix_audit_logs_entity_type'), table_name='audit_logs')
    op.drop_column('audit_logs', 'entry_hash')
    op.drop_column('audit_logs', 'prev_hash')
    op.drop_column('audit_logs', 'correlation_id')
    op.drop_column('audit_logs', 'actor_type')

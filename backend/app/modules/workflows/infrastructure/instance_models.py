from __future__ import annotations

import uuid
from datetime import datetime, timezone

from sqlalchemy import (
    JSON,
    Boolean,
    DateTime,
    Integer,
    String,
    Text,
    Uuid,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class WorkflowInstanceModel(Base):
    """A running execution of a (dynamic) workflow bound to one request/task."""

    __tablename__ = "workflow_instances"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )
    task_id: Mapped[uuid.UUID | None] = mapped_column(Uuid, nullable=True)
    request: Mapped[str] = mapped_column(Text, nullable=False)
    summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="Created")
    current_step: Mapped[int | None] = mapped_column(Integer, nullable=True)
    context: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    fallback: Mapped[bool] = mapped_column(Boolean, default=False)


class WorkflowStepModel(Base):
    """One step of an instance; mirrors one AGENT_RUNS record."""

    __tablename__ = "workflow_steps"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )
    instance_id: Mapped[uuid.UUID] = mapped_column(Uuid, index=True, nullable=False)
    step_order: Mapped[int] = mapped_column(Integer, nullable=False)
    agent_type: Mapped[str] = mapped_column(String(64), nullable=False)
    objective: Mapped[str | None] = mapped_column(Text, nullable=True)
    tier: Mapped[str | None] = mapped_column(String(32), nullable=True)
    model: Mapped[str | None] = mapped_column(String(128), nullable=True)
    requires_approval: Mapped[bool] = mapped_column(Boolean, default=False)
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="Pending")
    attempts: Mapped[int] = mapped_column(Integer, default=0)
    output: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    error: Mapped[str | None] = mapped_column(Text, nullable=True)

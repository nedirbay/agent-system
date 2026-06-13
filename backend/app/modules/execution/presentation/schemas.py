from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


# --- Computer-use actions (Faza 7 / AG-008) ---


class ActionIn(BaseModel):
    """A single declarative browser/desktop action."""

    kind: str = Field(description="browser | desktop")
    type: str = Field(description="navigate, write_file, run_process, ...")
    params: dict[str, Any] = Field(default_factory=dict)


class RunPlanRequest(BaseModel):
    actions: list[ActionIn]
    # Stands in for the Workflow Engine's Human Approval Step (SB-004): when
    # true, sensitive actions are permitted to execute.
    approved: bool = False


class RunActionRequest(BaseModel):
    action: ActionIn
    approved: bool = False


class PreviewRequest(BaseModel):
    actions: list[ActionIn]


class ActionOutcomeRead(BaseModel):
    action: str
    kind: str
    type: str
    decision: str
    rule: str
    status: str
    output: dict = Field(default_factory=dict)
    logs: list[str] = Field(default_factory=list)
    screenshot: str | None = None
    error: str | None = None


class ExecutionReportRead(BaseModel):
    run_id: uuid.UUID
    status: str
    outcomes: list[ActionOutcomeRead]


class ExecutionRunCreate(BaseModel):
    task_id: uuid.UUID | None = None
    command: str | None = None
    status: str = "pending"
    output: str | None = None


class ExecutionRunRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    created_at: datetime
    task_id: uuid.UUID | None = None
    command: str | None = None
    status: str | None = None
    output: str | None = None

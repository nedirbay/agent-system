from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict


class WorkflowCreate(BaseModel):
    name: str
    description: str | None = None
    is_active: bool = True


class WorkflowRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    created_at: datetime
    name: str | None = None
    description: str | None = None
    is_active: bool | None = None


# --- Workflow Engine instances (Task 13) ---

class RunWorkflowRequest(BaseModel):
    request: str
    task_id: uuid.UUID | None = None
    context: dict | None = None


class ApprovalRequest(BaseModel):
    approved: bool = True


class WorkflowStepRead(BaseModel):
    id: uuid.UUID
    step_order: int
    agent_type: str
    objective: str
    tier: str | None = None
    model: str | None = None
    requires_approval: bool
    status: str
    attempts: int
    output: dict | None = None
    error: str | None = None


class WorkflowInstanceRead(BaseModel):
    id: uuid.UUID
    created_at: datetime
    task_id: uuid.UUID | None = None
    request: str
    summary: str
    status: str
    current_step: int | None = None
    fallback: bool
    context: dict
    steps: list[WorkflowStepRead]

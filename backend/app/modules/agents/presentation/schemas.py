from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict


class AgentCreate(BaseModel):
    name: str
    type: str | None = None
    description: str | None = None
    is_active: bool = True


class AgentRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    created_at: datetime
    name: str | None = None
    type: str | None = None
    description: str | None = None
    is_active: bool | None = None


# --- Orchestrator (Tasks 11–12) ---

class PlanRequest(BaseModel):
    request: str
    context: str | None = None


class PlannedStepRead(BaseModel):
    step_order: int
    agent_type: str
    objective: str
    tier: str | None = None
    model: str | None = None
    requires_approval: bool = False


class PlanRead(BaseModel):
    request: str
    summary: str
    fallback: bool
    steps: list[PlannedStepRead]


class AgentSpecRead(BaseModel):
    type: str
    description: str
    task_class: str
    tier: str
    capabilities: list[str]
    requires_approval: bool


class DocumentAgentAnalysisRead(BaseModel):
    document_id: uuid.UUID
    file_name: str | None = None
    summary: str
    language: str | None = None
    categories: list[str]
    classification: str
    metadata: dict

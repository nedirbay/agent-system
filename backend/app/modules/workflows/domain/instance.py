"""Workflow instance & step domain (Roadmap Task 13).

A `WorkflowInstance` is one running execution bound to a request/task; it owns
its status, a key-value `context` carried between steps, and an ordered list of
`WorkflowStep`s. Mirrors the lifecycle in WORKFLOW_ENGINE_SPECIFICATION.
"""
from __future__ import annotations

import uuid
from abc import ABC, abstractmethod
from dataclasses import dataclass, field

from app.shared.domain.entity import BaseEntity


# --- Instance status (Workflow Lifecycle) ---
class InstanceStatus:
    CREATED = "Created"
    RUNNING = "Running"
    WAITING = "Waiting"  # paused on human approval / timer / external event
    COMPLETED = "Completed"
    FAILED = "Failed"
    CANCELLED = "Cancelled"


# --- Step status (Step Lifecycle) ---
class StepStatus:
    PENDING = "Pending"
    RUNNING = "Running"
    SUCCEEDED = "Succeeded"
    FAILED = "Failed"
    AWAITING_APPROVAL = "AwaitingApproval"
    SKIPPED = "Skipped"


@dataclass
class WorkflowStep(BaseEntity):
    instance_id: uuid.UUID | None = None
    step_order: int = 0
    agent_type: str = ""
    objective: str = ""
    tier: str | None = None
    model: str | None = None
    requires_approval: bool = False
    status: str = StepStatus.PENDING
    attempts: int = 0
    output: dict | None = None
    error: str | None = None


@dataclass
class WorkflowInstance(BaseEntity):
    task_id: uuid.UUID | None = None
    request: str = ""
    summary: str = ""
    status: str = InstanceStatus.CREATED
    current_step: int | None = None
    context: dict = field(default_factory=dict)
    fallback: bool = False
    steps: list[WorkflowStep] = field(default_factory=list)


class WorkflowInstanceRepository(ABC):
    @abstractmethod
    async def add(self, instance: WorkflowInstance) -> WorkflowInstance:
        """Persist a new instance and its steps."""

    @abstractmethod
    async def get(self, instance_id: uuid.UUID) -> WorkflowInstance | None:
        """Load an instance with its steps (ordered)."""

    @abstractmethod
    async def save(self, instance: WorkflowInstance) -> WorkflowInstance:
        """Persist updates to an instance and all of its steps."""

    @abstractmethod
    async def list(self, *, limit: int = 100, offset: int = 0) -> list[WorkflowInstance]:
        """List instances (without steps) newest-first."""

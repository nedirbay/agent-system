"""Task planning domain (Roadmap Task 11 / AG-001 Orchestrator).

The Orchestrator decomposes a user request into an ordered list of steps, each
targeting one agent type. This is the `WT-002 Dynamic Workflow` plan that the
Workflow Engine materialises into an instance.
"""
from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field


@dataclass
class PlannedStep:
    step_order: int
    agent_type: str
    objective: str
    # Free-form hints the executor/agent can use (e.g. {"query": "..."}).
    inputs: dict = field(default_factory=dict)
    # Assigned by the router; None until routed.
    tier: str | None = None
    model: str | None = None
    requires_approval: bool = False


@dataclass
class Plan:
    request: str
    summary: str
    steps: list[PlannedStep] = field(default_factory=list)
    # True when the plan came from a heuristic fallback, not the LLM.
    fallback: bool = False


class TaskPlanner(ABC):
    """Port: decompose a request into an ordered plan of agent steps."""

    @abstractmethod
    async def plan(self, request: str, *, context: str | None = None) -> Plan:
        ...

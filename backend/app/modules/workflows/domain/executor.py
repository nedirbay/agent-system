"""Step executor port (Roadmap Task 13).

The engine never sequences agents itself beyond ordering; running a single step
is delegated to a `StepExecutor`. In the target architecture (EX-001) this is
event-driven dispatch to a specialized agent; the MVP runs an in-process
executor. Either way the engine code is identical.
"""
from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass


@dataclass
class StepRequest:
    agent_type: str
    objective: str
    model: str | None
    request: str  # the original user request
    context: dict  # accumulated workflow context (read-only for the executor)


@dataclass
class StepResult:
    output: dict


class StepExecutor(ABC):
    @abstractmethod
    async def execute(self, step: StepRequest) -> StepResult:
        """Run one step and return its output (written back into context)."""

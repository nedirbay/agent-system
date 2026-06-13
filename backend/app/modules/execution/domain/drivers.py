"""Driver ports for computer-use actions (Faza 7 Tasks 21/22).

Both ports expose a single ``execute(action)`` method that dispatches on the
action type and returns a :class:`DriverResult` (structured output + logs + an
optional screenshot reference). Concrete adapters live in the infrastructure
layer: a simulated, fully-offline browser and a scratch-confined desktop
driver. Real adapters (Playwright, a remote desktop) drop in behind the same
ports without touching the agent.
"""
from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field

from app.modules.execution.domain.actions import Action


@dataclass(frozen=True)
class DriverResult:
    output: dict
    logs: list[str] = field(default_factory=list)
    screenshot: str | None = None


class BrowserDriver(ABC):
    """Performs browser actions: navigate, fill, click, submit, download."""

    @abstractmethod
    async def execute(self, action: Action) -> DriverResult: ...


class DesktopDriver(ABC):
    """Performs desktop actions: file operations and process execution."""

    @abstractmethod
    async def execute(self, action: Action) -> DriverResult: ...

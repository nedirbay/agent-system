"""Computer-use action model (Faza 7 / AG-008, FR-015).

An :class:`Action` is the atomic unit the Execution Agent runs: a single
browser or desktop operation described declaratively. The Orchestrator hands
the agent an *execution plan* (an ordered list of actions); the agent vets each
one through the sandbox before dispatching it to a driver.

Actions are plain, JSON-serialisable value objects with no behaviour — the
sandbox decides whether they may run and the drivers carry them out.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

# --- Action kinds (which driver handles it) ---
BROWSER = "browser"
DESKTOP = "desktop"
KINDS = frozenset({BROWSER, DESKTOP})

# --- Browser action types (Task 21) ---
NAVIGATE = "navigate"
FILL = "fill"
CLICK = "click"
SUBMIT = "submit"
DOWNLOAD = "download"
SCREENSHOT = "screenshot"
BROWSER_TYPES = frozenset({NAVIGATE, FILL, CLICK, SUBMIT, DOWNLOAD, SCREENSHOT})

# --- Desktop action types (Task 22) ---
READ_FILE = "read_file"
WRITE_FILE = "write_file"
LIST_DIR = "list_dir"
DELETE_FILE = "delete_file"
RUN_PROCESS = "run_process"
DESKTOP_TYPES = frozenset(
    {READ_FILE, WRITE_FILE, LIST_DIR, DELETE_FILE, RUN_PROCESS}
)

_TYPES_BY_KIND = {BROWSER: BROWSER_TYPES, DESKTOP: DESKTOP_TYPES}


@dataclass(frozen=True)
class Action:
    """A single declarative computer-use operation."""

    kind: str
    type: str
    params: dict[str, Any] = field(default_factory=dict)

    def is_valid(self) -> bool:
        return self.type in _TYPES_BY_KIND.get(self.kind, frozenset())

    def describe(self) -> str:
        target = self.params.get("url") or self.params.get("path") or self.params.get(
            "command"
        )
        return f"{self.kind}:{self.type}" + (f" {target}" if target else "")

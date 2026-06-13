"""Sandbox policy & rulings (Faza 7 Task 23 / SECURITY_ARCHITECTURE SB-001..008).

This module holds the *policy* (what a task is allowed to touch) and the
*ruling* types produced when an action is evaluated against it. The enforcement
logic lives in the application layer (`SafeExecutionSandbox`); keeping the data
here makes the policy framework-agnostic and easy to construct in tests.
"""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from pathlib import Path

from app.core.exceptions import AppError


class Decision(str, Enum):
    """Outcome of classifying an action against the sandbox policy."""

    ALLOW = "allow"
    REQUIRE_APPROVAL = "require_approval"  # SB-004 human-approval gate
    DENY = "deny"  # policy violation or forbidden op


@dataclass(frozen=True)
class SandboxPolicy:
    """Capabilities granted to a single Execution Agent task (SB-002/003).

    Everything is default-deny: a task may only write under ``scratch_dir``,
    reach hosts in ``egress_allowlist``, and run executables in
    ``command_allowlist``. All else is denied.
    """

    scratch_dir: Path
    egress_allowlist: frozenset[str] = frozenset()
    command_allowlist: frozenset[str] = frozenset()
    process_timeout_seconds: float = 10.0
    max_output_chars: int = 10_000


@dataclass(frozen=True)
class SandboxRuling:
    """The sandbox's verdict on one action, with the rule that produced it."""

    decision: Decision
    rule: str  # e.g. "SB-005", "SB-008"
    reason: str


class SafeExecutionError(AppError):
    """A hard sandbox failure raised during execution (e.g. timeout, escape)."""

    status_code = 422
    code = "sandbox_violation"

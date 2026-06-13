"""Safe execution sandbox (Faza 7 Task 23 / SECURITY_ARCHITECTURE SB-001..008).

The sandbox is the policy gate every action passes through before a driver
touches anything. It classifies an action into one of three rulings:

* ``DENY``  — a policy violation (egress not allowlisted, path escapes scratch,
  command not granted) or a forbidden operation (unscoped delete, AG-008/SB-005).
  Denied actions never run, regardless of approval.
* ``REQUIRE_APPROVAL`` — a sensitive action (download, form submit, file write,
  process execution, sending email/external integrations). It runs only after
  the human-approval gate (SB-004) has cleared it.
* ``ALLOW`` — a read-only / in-scope action that runs immediately.

The same path/egress/command checks are also re-applied physically inside the
desktop driver (defence in depth) — this layer is the *policy* decision, the
driver is the *mechanism*.
"""
from __future__ import annotations

from pathlib import Path
from urllib.parse import urlparse

from app.modules.execution.domain import actions as A
from app.modules.execution.domain.sandbox import (
    Decision,
    SandboxPolicy,
    SandboxRuling,
)

# Sensitive actions require human approval before execution (SB-004 / FR-015).
_SENSITIVE = frozenset(
    {A.DOWNLOAD, A.SUBMIT, A.WRITE_FILE, A.RUN_PROCESS}
)
# Forbidden outright (AG-008 "direct delete forbidden" / SB-005), even if approved.
_FORBIDDEN = frozenset({A.DELETE_FILE})
# Browser actions that open a network connection and so are egress-controlled.
_NETWORK_BROWSER = frozenset({A.NAVIGATE, A.SUBMIT, A.DOWNLOAD, A.CLICK})
# Desktop actions that resolve a filesystem path inside the scratch volume.
_PATH_DESKTOP = frozenset({A.READ_FILE, A.WRITE_FILE, A.LIST_DIR, A.DELETE_FILE})


class SafeExecutionSandbox:
    def __init__(self, policy: SandboxPolicy) -> None:
        self._policy = policy

    @property
    def policy(self) -> SandboxPolicy:
        return self._policy

    def classify(self, action: A.Action) -> SandboxRuling:
        # 1. Forbidden operations are rejected before anything else (SB-005).
        if action.type in _FORBIDDEN:
            return SandboxRuling(
                Decision.DENY,
                "SB-005",
                "Direct delete operations are forbidden; use a reversible "
                "compensating workflow instead (AG-008).",
            )

        # 2. Default-deny policy checks (egress / scratch / capability).
        if action.kind == A.BROWSER and action.type in _NETWORK_BROWSER:
            violation = self._check_egress(action)
            if violation is not None:
                return violation
        if action.kind == A.DESKTOP and action.type in _PATH_DESKTOP:
            violation = self._check_path(action)
            if violation is not None:
                return violation
        if action.kind == A.DESKTOP and action.type == A.RUN_PROCESS:
            violation = self._check_command(action)
            if violation is not None:
                return violation

        # 3. Sensitive actions need the human-approval gate (SB-004).
        if action.type in _SENSITIVE:
            return SandboxRuling(
                Decision.REQUIRE_APPROVAL,
                "SB-004",
                f"'{action.type}' is a sensitive action and requires human approval.",
            )

        # 4. Otherwise in-scope and read-only — allowed.
        return SandboxRuling(Decision.ALLOW, "SB-003", "Within granted capabilities.")

    # --- policy checks -------------------------------------------------- #

    def _check_egress(self, action: A.Action) -> SandboxRuling | None:
        url = action.params.get("url")
        host = urlparse(url).hostname if url else None
        if not host:
            return SandboxRuling(
                Decision.DENY, "SB-008", "Browser action is missing a target URL."
            )
        if host not in self._policy.egress_allowlist:
            return SandboxRuling(
                Decision.DENY,
                "SB-008",
                f"Egress to '{host}' is not on the approved allowlist.",
            )
        return None

    def _check_path(self, action: A.Action) -> SandboxRuling | None:
        path = action.params.get("path")
        if not path:
            return SandboxRuling(
                Decision.DENY, "SB-002", "File action is missing a path."
            )
        if self.resolve_in_scratch(path) is None:
            return SandboxRuling(
                Decision.DENY,
                "SB-002",
                f"Path '{path}' escapes the sandbox scratch volume.",
            )
        return None

    def _check_command(self, action: A.Action) -> SandboxRuling | None:
        command = action.params.get("command")
        if not command:
            return SandboxRuling(
                Decision.DENY, "SB-003", "Process action is missing a command."
            )
        if Path(command).name not in self._policy.command_allowlist:
            return SandboxRuling(
                Decision.DENY,
                "SB-003",
                f"Command '{command}' is not on the granted allowlist.",
            )
        return None

    def resolve_in_scratch(self, path: str) -> Path | None:
        """Resolve ``path`` under the scratch root, or ``None`` if it escapes.

        Absolute paths and ``..`` traversal that land outside the scratch dir
        are rejected (SB-002). Returned paths are always inside scratch.
        """
        root = self._policy.scratch_dir.resolve()
        candidate = (root / path).resolve()
        if candidate == root or root in candidate.parents:
            return candidate
        return None

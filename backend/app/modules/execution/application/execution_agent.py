"""Execution Agent — computer use (Faza 7 / AG-008, FR-015).

The Execution Agent runs an execution plan (an ordered list of browser/desktop
actions) one action at a time. Every action passes through the
:class:`SafeExecutionSandbox` first:

* denied actions never run;
* sensitive actions run only when the human-approval gate has cleared them
  (``approved=True``, set by the Workflow Engine's Human Approval Step);
* allowed actions run immediately.

Execution stops at the first action that is blocked, awaiting approval, or
fails — the plan is fail-closed. Every run is recorded as an ``ExecutionRun``
(SB-007: commands, outputs, logs and screenshot references are persisted for
audit and replay).
"""
from __future__ import annotations

import json
import uuid
from dataclasses import asdict, dataclass, field

from app.core.exceptions import AppError, NotFoundError
from app.core.logging import get_logger
from app.modules.execution.application.sandbox import SafeExecutionSandbox
from app.modules.execution.domain.actions import Action
from app.modules.execution.domain.drivers import BrowserDriver, DesktopDriver
from app.modules.execution.domain.entities import ExecutionRun
from app.modules.execution.domain.repositories import ExecutionRunRepository
from app.modules.execution.domain.sandbox import Decision, SafeExecutionError

_logger = get_logger("execution.agent")

# Run-level status derived from the outcome that stopped the plan.
COMPLETED = "completed"
BLOCKED = "blocked"
AWAITING_APPROVAL = "awaiting_approval"
FAILED = "failed"


@dataclass(frozen=True)
class ActionOutcome:
    action: str
    kind: str
    type: str
    decision: str
    rule: str
    status: str  # completed / denied / awaiting_approval / failed
    output: dict = field(default_factory=dict)
    logs: list[str] = field(default_factory=list)
    screenshot: str | None = None
    error: str | None = None


@dataclass(frozen=True)
class ExecutionReport:
    run_id: uuid.UUID
    status: str
    outcomes: list[ActionOutcome]


class ExecutionAgentService:
    def __init__(
        self,
        *,
        runs: ExecutionRunRepository,
        sandbox: SafeExecutionSandbox,
        browser: BrowserDriver,
        desktop: DesktopDriver,
        task_id: uuid.UUID | None = None,
    ) -> None:
        self._runs = runs
        self._sandbox = sandbox
        self._browser = browser
        self._desktop = desktop
        self._task_id = task_id

    # --- public API ----------------------------------------------------- #

    def preview(self, actions: list[Action]) -> list[ActionOutcome]:
        """Dry-run: classify every action without executing anything."""
        plan = self._parse(actions)
        outcomes: list[ActionOutcome] = []
        for action in plan:
            ruling = self._sandbox.classify(action)
            outcomes.append(
                ActionOutcome(
                    action=action.describe(),
                    kind=action.kind,
                    type=action.type,
                    decision=ruling.decision.value,
                    rule=ruling.rule,
                    status="preview",
                )
            )
        return outcomes

    async def run_action(self, action: Action, *, approved: bool = False) -> ExecutionReport:
        return await self.run_plan([action], approved=approved)

    async def run_plan(
        self, actions: list[Action], *, approved: bool = False
    ) -> ExecutionReport:
        plan = self._parse(actions)
        outcomes: list[ActionOutcome] = []
        status = COMPLETED

        for action in plan:
            ruling = self._sandbox.classify(action)

            if ruling.decision is Decision.DENY:
                outcomes.append(self._stop_outcome(action, ruling, "denied"))
                _logger.warning(
                    "execution.denied", action=action.describe(), rule=ruling.rule
                )
                status = BLOCKED
                break

            if ruling.decision is Decision.REQUIRE_APPROVAL and not approved:
                outcomes.append(self._stop_outcome(action, ruling, "awaiting_approval"))
                _logger.info(
                    "execution.awaiting_approval", action=action.describe()
                )
                status = AWAITING_APPROVAL
                break

            try:
                result = await self._dispatch(action)
            except SafeExecutionError as exc:
                outcomes.append(self._stop_outcome(action, ruling, "failed", str(exc)))
                _logger.warning(
                    "execution.failed", action=action.describe(), error=str(exc)
                )
                status = FAILED
                break

            outcomes.append(
                ActionOutcome(
                    action=action.describe(),
                    kind=action.kind,
                    type=action.type,
                    decision=ruling.decision.value,
                    rule=ruling.rule,
                    status="completed",
                    output=result.output,
                    logs=result.logs,
                    screenshot=result.screenshot,
                )
            )

        run = await self._record(plan, status, outcomes)
        return ExecutionReport(run_id=run.id, status=status, outcomes=outcomes)

    # --- internals ------------------------------------------------------ #

    def _parse(self, actions: list[Action]) -> list[Action]:
        if not actions:
            raise AppError("An execution plan requires at least one action")
        for action in actions:
            if not isinstance(action, Action) or not action.is_valid():
                raise AppError(
                    f"Unknown action '{getattr(action, 'kind', '?')}:"
                    f"{getattr(action, 'type', '?')}'"
                )
        return actions

    async def _dispatch(self, action: Action):
        driver = self._browser if action.kind == "browser" else self._desktop
        return await driver.execute(action)

    @staticmethod
    def _stop_outcome(
        action: Action, ruling, status: str, error: str | None = None
    ) -> ActionOutcome:
        return ActionOutcome(
            action=action.describe(),
            kind=action.kind,
            type=action.type,
            decision=ruling.decision.value,
            rule=ruling.rule,
            status=status,
            error=error or ruling.reason,
        )

    async def _record(
        self, plan: list[Action], status: str, outcomes: list[ActionOutcome]
    ) -> ExecutionRun:
        summary = "; ".join(a.describe() for a in plan)
        payload = {
            "status": status,
            "outcomes": [asdict(o) for o in outcomes],
        }
        return await self._runs.add(
            ExecutionRun(
                task_id=self._task_id,
                command=summary,
                status=status,
                output=json.dumps(payload),
            )
        )

    async def get_run(self, run_id: uuid.UUID) -> ExecutionRun:
        run = await self._runs.get(run_id)
        if run is None:
            raise NotFoundError("ExecutionRun not found")
        return run

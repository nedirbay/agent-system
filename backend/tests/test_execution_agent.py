from __future__ import annotations

import uuid
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.core.exceptions import AppError
from app.main import app
from app.modules.execution.application.execution_agent import ExecutionAgentService
from app.modules.execution.application.sandbox import SafeExecutionSandbox
from app.modules.execution.domain import actions as A
from app.modules.execution.domain.actions import Action
from app.modules.execution.domain.entities import ExecutionRun
from app.modules.execution.domain.repositories import ExecutionRunRepository
from app.modules.execution.domain.sandbox import Decision, SandboxPolicy
from app.modules.execution.infrastructure.browser_driver import SimulatedBrowserDriver
from app.modules.execution.infrastructure.desktop_driver import LocalSandboxDesktopDriver
from app.modules.execution.presentation.dependencies import get_execution_agent_service


# --------------------------------------------------------------------------- #
# Fakes / helpers
# --------------------------------------------------------------------------- #


class ExecutionRunRepo(ExecutionRunRepository):
    def __init__(self) -> None:
        self.items: dict[uuid.UUID, ExecutionRun] = {}

    async def add(self, entity: ExecutionRun) -> ExecutionRun:
        self.items[entity.id] = entity
        return entity

    async def get(self, entity_id: uuid.UUID) -> ExecutionRun | None:
        return self.items.get(entity_id)

    async def list(self, *, limit: int = 100, offset: int = 0) -> list[ExecutionRun]:
        return list(self.items.values())[offset : offset + limit]


def _policy(scratch: Path) -> SandboxPolicy:
    return SandboxPolicy(
        scratch_dir=scratch,
        egress_allowlist=frozenset({"example.com"}),
        command_allowlist=frozenset({"echo", "true"}),
        process_timeout_seconds=5.0,
        max_output_chars=10_000,
    )


def _agent(scratch: Path) -> tuple[ExecutionAgentService, ExecutionRunRepo]:
    policy = _policy(scratch)
    runs = ExecutionRunRepo()
    agent = ExecutionAgentService(
        runs=runs,
        sandbox=SafeExecutionSandbox(policy),
        browser=SimulatedBrowserDriver(),
        desktop=LocalSandboxDesktopDriver(policy),
    )
    return agent, runs


# --------------------------------------------------------------------------- #
# Task 23 — Sandbox classification
# --------------------------------------------------------------------------- #


def test_sandbox_classifies_each_rule(tmp_path: Path) -> None:
    sandbox = SafeExecutionSandbox(_policy(tmp_path))

    allow = sandbox.classify(Action(A.DESKTOP, A.READ_FILE, {"path": "a.txt"}))
    assert allow.decision is Decision.ALLOW

    approval = sandbox.classify(Action(A.DESKTOP, A.WRITE_FILE, {"path": "a.txt", "content": "x"}))
    assert approval.decision is Decision.REQUIRE_APPROVAL and approval.rule == "SB-004"

    forbidden = sandbox.classify(Action(A.DESKTOP, A.DELETE_FILE, {"path": "a.txt"}))
    assert forbidden.decision is Decision.DENY and forbidden.rule == "SB-005"

    egress = sandbox.classify(Action(A.BROWSER, A.NAVIGATE, {"url": "https://evil.test/x"}))
    assert egress.decision is Decision.DENY and egress.rule == "SB-008"

    escape = sandbox.classify(Action(A.DESKTOP, A.READ_FILE, {"path": "../../etc/passwd"}))
    assert escape.decision is Decision.DENY and escape.rule == "SB-002"

    bad_cmd = sandbox.classify(Action(A.DESKTOP, A.RUN_PROCESS, {"command": "rm"}))
    assert bad_cmd.decision is Decision.DENY and bad_cmd.rule == "SB-003"

    nav_ok = sandbox.classify(Action(A.BROWSER, A.NAVIGATE, {"url": "https://example.com/p"}))
    assert nav_ok.decision is Decision.ALLOW


# --------------------------------------------------------------------------- #
# Task 21 — Browser operations
# --------------------------------------------------------------------------- #


@pytest.mark.asyncio
async def test_browser_navigate_runs_and_records(tmp_path: Path) -> None:
    agent, runs = _agent(tmp_path)
    report = await agent.run_action(Action(A.BROWSER, A.NAVIGATE, {"url": "https://example.com/docs"}))

    assert report.status == "completed"
    assert report.outcomes[0].output["status"] == 200
    assert report.outcomes[0].screenshot is not None
    # Recorded for audit (SB-007).
    assert runs.items[report.run_id].status == "completed"


@pytest.mark.asyncio
async def test_browser_download_requires_then_runs_with_approval(tmp_path: Path) -> None:
    agent, _ = _agent(tmp_path)
    action = Action(A.BROWSER, A.DOWNLOAD, {"url": "https://example.com/file.pdf"})

    pending = await agent.run_action(action)
    assert pending.status == "awaiting_approval"
    assert pending.outcomes[0].status == "awaiting_approval"

    approved = await agent.run_action(action, approved=True)
    assert approved.status == "completed"
    assert approved.outcomes[0].output["saved_as"] == "file.pdf"


# --------------------------------------------------------------------------- #
# Task 22 — Desktop operations
# --------------------------------------------------------------------------- #


@pytest.mark.asyncio
async def test_desktop_write_read_and_list(tmp_path: Path) -> None:
    agent, _ = _agent(tmp_path)

    write = await agent.run_action(
        Action(A.DESKTOP, A.WRITE_FILE, {"path": "notes/todo.txt", "content": "hello"}),
        approved=True,
    )
    assert write.status == "completed"
    assert (tmp_path / "notes" / "todo.txt").read_text() == "hello"

    read = await agent.run_action(Action(A.DESKTOP, A.READ_FILE, {"path": "notes/todo.txt"}))
    assert read.outcomes[0].output["content"] == "hello"

    listing = await agent.run_action(Action(A.DESKTOP, A.LIST_DIR, {"path": "notes"}))
    assert "todo.txt" in listing.outcomes[0].output["entries"]


@pytest.mark.asyncio
async def test_desktop_run_process_executes_allowlisted_command(tmp_path: Path) -> None:
    agent, _ = _agent(tmp_path)
    report = await agent.run_action(
        Action(A.DESKTOP, A.RUN_PROCESS, {"command": "echo", "args": ["sandboxed"]}),
        approved=True,
    )
    assert report.status == "completed"
    assert report.outcomes[0].output["returncode"] == 0
    assert "sandboxed" in report.outcomes[0].output["stdout"]


@pytest.mark.asyncio
async def test_desktop_delete_is_forbidden(tmp_path: Path) -> None:
    agent, _ = _agent(tmp_path)
    report = await agent.run_action(
        Action(A.DESKTOP, A.DELETE_FILE, {"path": "todo.txt"}), approved=True
    )
    assert report.status == "blocked"
    assert report.outcomes[0].status == "denied"
    assert report.outcomes[0].rule == "SB-005"


# --------------------------------------------------------------------------- #
# Plan-level behaviour
# --------------------------------------------------------------------------- #


@pytest.mark.asyncio
async def test_plan_stops_at_first_action_needing_approval(tmp_path: Path) -> None:
    agent, _ = _agent(tmp_path)
    report = await agent.run_plan(
        [
            Action(A.BROWSER, A.NAVIGATE, {"url": "https://example.com/a"}),
            Action(A.DESKTOP, A.WRITE_FILE, {"path": "x.txt", "content": "y"}),
            Action(A.BROWSER, A.NAVIGATE, {"url": "https://example.com/b"}),
        ]
    )
    assert report.status == "awaiting_approval"
    # First ran, second paused, third never reached.
    assert len(report.outcomes) == 2
    assert report.outcomes[0].status == "completed"
    assert report.outcomes[1].status == "awaiting_approval"


@pytest.mark.asyncio
async def test_plan_blocks_on_egress_violation(tmp_path: Path) -> None:
    agent, _ = _agent(tmp_path)
    report = await agent.run_plan(
        [Action(A.BROWSER, A.NAVIGATE, {"url": "https://evil.test/x"})], approved=True
    )
    assert report.status == "blocked"
    assert report.outcomes[0].rule == "SB-008"


def test_preview_classifies_without_executing(tmp_path: Path) -> None:
    agent, runs = _agent(tmp_path)
    outcomes = agent.preview(
        [
            Action(A.DESKTOP, A.READ_FILE, {"path": "a.txt"}),
            Action(A.DESKTOP, A.WRITE_FILE, {"path": "a.txt", "content": "x"}),
        ]
    )
    assert [o.decision for o in outcomes] == ["allow", "require_approval"]
    assert all(o.status == "preview" for o in outcomes)
    assert runs.items == {}  # nothing executed or recorded


@pytest.mark.asyncio
async def test_validation_rejects_empty_and_unknown(tmp_path: Path) -> None:
    agent, _ = _agent(tmp_path)
    with pytest.raises(AppError):
        await agent.run_plan([])
    with pytest.raises(AppError):
        await agent.run_action(Action("browser", "teleport", {}))


# --------------------------------------------------------------------------- #
# Endpoints
# --------------------------------------------------------------------------- #


def test_execution_endpoints(tmp_path: Path) -> None:
    agent, _ = _agent(tmp_path)
    app.dependency_overrides[get_execution_agent_service] = lambda: agent
    try:
        client = TestClient(app)

        # Preview
        r = client.post(
            "/api/v1/execution/preview",
            json={"actions": [{"kind": "desktop", "type": "delete_file", "params": {"path": "a"}}]},
        )
        assert r.status_code == 200, r.text
        assert r.json()[0]["decision"] == "deny"

        # Run an allowed browser action
        r = client.post(
            "/api/v1/execution/actions",
            json={"action": {"kind": "browser", "type": "navigate", "params": {"url": "https://example.com"}}},
        )
        assert r.status_code == 200, r.text
        assert r.json()["status"] == "completed"

        # Sensitive action without approval is held at the gate
        r = client.post(
            "/api/v1/execution/plan",
            json={"actions": [{"kind": "desktop", "type": "write_file", "params": {"path": "f.txt", "content": "x"}}]},
        )
        assert r.status_code == 200, r.text
        assert r.json()["status"] == "awaiting_approval"
    finally:
        app.dependency_overrides.clear()

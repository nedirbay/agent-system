from __future__ import annotations

from pathlib import Path

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.core.database import get_session
from app.modules.execution.application.execution_agent import ExecutionAgentService
from app.modules.execution.application.sandbox import SafeExecutionSandbox
from app.modules.execution.application.services import ExecutionRunService
from app.modules.execution.domain.sandbox import SandboxPolicy
from app.modules.execution.infrastructure.browser_driver import SimulatedBrowserDriver
from app.modules.execution.infrastructure.desktop_driver import LocalSandboxDesktopDriver
from app.modules.execution.infrastructure.repositories import SqlAlchemyExecutionRunRepository


def get_executionrun_service(session: AsyncSession = Depends(get_session)) -> ExecutionRunService:
    return ExecutionRunService(SqlAlchemyExecutionRunRepository(session))


def build_sandbox_policy() -> SandboxPolicy:
    """Construct the per-task sandbox policy from configured grants (SB-002/003/008)."""
    settings = get_settings()
    return SandboxPolicy(
        scratch_dir=Path(settings.execution_scratch_dir),
        egress_allowlist=frozenset(settings.execution_egress_allowlist),
        command_allowlist=frozenset(settings.execution_command_allowlist),
        process_timeout_seconds=settings.execution_process_timeout_seconds,
        max_output_chars=settings.execution_max_output_chars,
    )


def get_execution_agent_service(
    session: AsyncSession = Depends(get_session),
) -> ExecutionAgentService:
    policy = build_sandbox_policy()
    return ExecutionAgentService(
        runs=SqlAlchemyExecutionRunRepository(session),
        sandbox=SafeExecutionSandbox(policy),
        browser=SimulatedBrowserDriver(),
        desktop=LocalSandboxDesktopDriver(policy),
    )

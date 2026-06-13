"""Monitoring service (Faza 9 Task 28 / SYSTEM_REQUIREMENTS §11).

Assembles the Section-11 metrics summary: the live request/processing-time/
error-rate metrics from the in-process registry, plus the database-derived
gauges (active users, active agents, task count) computed at read time so they
always reflect the current system state.
"""
from __future__ import annotations

from sqlalchemy import func, select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.logging import get_logger
from app.core.metrics import get_metrics
from app.modules.agents.infrastructure.models import AgentModel
from app.modules.auth.infrastructure.models import UserModel
from app.modules.execution.infrastructure.models import ExecutionRunModel
from app.modules.qa.infrastructure.models import QaConversationModel
from app.modules.workflows.infrastructure.instance_models import WorkflowInstanceModel

_logger = get_logger("monitoring")


class MonitoringService:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def _count(self, statement) -> int:
        result = await self._session.execute(statement)
        return int(result.scalar_one())

    async def gauges(self) -> dict[str, int]:
        """Live gauges from the database. Degrades to zeros if the DB is down."""
        try:
            active_users = await self._count(
                select(func.count())
                .select_from(UserModel)
                .where(UserModel.status == "active")
            )
            total_users = await self._count(select(func.count()).select_from(UserModel))
            active_agents = await self._count(
                select(func.count())
                .select_from(AgentModel)
                .where(AgentModel.is_active.is_(True))
            )
            # "Task count" proxy: workflow instances + execution runs + Q&A threads.
            workflows = await self._count(
                select(func.count()).select_from(WorkflowInstanceModel)
            )
            executions = await self._count(
                select(func.count()).select_from(ExecutionRunModel)
            )
            conversations = await self._count(
                select(func.count()).select_from(QaConversationModel)
            )
        except SQLAlchemyError:
            _logger.warning("monitoring.gauges_degraded")
            return {
                "active_users": 0,
                "total_users": 0,
                "active_agents": 0,
                "task_count": 0,
            }

        return {
            "active_users": active_users,
            "total_users": total_users,
            "active_agents": active_agents,
            "task_count": workflows + executions + conversations,
        }

    async def summary(self) -> dict:
        snapshot = get_metrics().snapshot()
        gauges = await self.gauges()
        return {**snapshot, **gauges}

    async def prometheus(self) -> str:
        gauges = await self.gauges()
        return get_metrics().prometheus_text(
            gauges={k: float(v) for k, v in gauges.items()}
        )

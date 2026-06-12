"""Orchestrator application service (Roadmap Tasks 11–12 / AG-001).

Plans a request into ordered agent steps (Task 11) and routes each step to a
model tier (Task 12). The resulting routed Plan is what the Workflow Engine
(Task 13) materialises and executes.
"""
from __future__ import annotations

from app.modules.agents.domain.planning import Plan, TaskPlanner
from app.modules.agents.domain.routing import AgentRouter


class OrchestratorService:
    def __init__(self, *, planner: TaskPlanner, router: AgentRouter) -> None:
        self._planner = planner
        self._router = router

    async def plan(self, request: str, *, context: str | None = None) -> Plan:
        plan = await self._planner.plan(request, context=context)
        return self._router.route(plan)

from __future__ import annotations

import uuid

import pytest

from app.modules.agents.application.orchestrator import OrchestratorService
from app.modules.agents.domain.planning import Plan, PlannedStep, TaskPlanner
from app.modules.agents.domain.routing import AgentRouter
from app.modules.workflows.application.engine import WorkflowEngine
from app.modules.workflows.domain.executor import StepExecutor, StepRequest, StepResult
from app.modules.workflows.domain.instance import (
    InstanceStatus,
    StepStatus,
    WorkflowInstance,
    WorkflowInstanceRepository,
)


class StaticPlanner(TaskPlanner):
    def __init__(self, steps: list[PlannedStep], *, fallback: bool = False) -> None:
        self._steps = steps
        self._fallback = fallback

    async def plan(self, request: str, *, context: str | None = None) -> Plan:
        return Plan(
            request=request,
            summary="Test workflow",
            steps=list(self._steps),
            fallback=self._fallback,
        )


class PassthroughRouter(AgentRouter):
    def route(self, plan: Plan) -> Plan:
        for step in plan.steps:
            step.tier = step.tier or "light"
            step.model = step.model or "test-model"
        return plan

    def resolve_model(self, agent_type: str) -> str:
        return "test-model"


class MemoryWorkflowRepository(WorkflowInstanceRepository):
    def __init__(self) -> None:
        self.items: dict[uuid.UUID, WorkflowInstance] = {}
        self.save_count = 0

    async def add(self, instance: WorkflowInstance) -> WorkflowInstance:
        self.items[instance.id] = instance
        return instance

    async def get(self, instance_id: uuid.UUID) -> WorkflowInstance | None:
        return self.items.get(instance_id)

    async def save(self, instance: WorkflowInstance) -> WorkflowInstance:
        self.save_count += 1
        self.items[instance.id] = instance
        return instance

    async def list(self, *, limit: int = 100, offset: int = 0) -> list[WorkflowInstance]:
        return list(self.items.values())[offset : offset + limit]


class RecordingExecutor(StepExecutor):
    def __init__(self, *, fail_first_for: set[int] | None = None) -> None:
        self.calls: list[StepRequest] = []
        self._fail_first_for = fail_first_for or set()
        self._attempts_by_order: dict[int, int] = {}

    async def execute(self, step: StepRequest) -> StepResult:
        order = len(self.calls) + 1
        self.calls.append(step)
        step_order = self._step_order(step.objective)
        self._attempts_by_order[step_order] = self._attempts_by_order.get(step_order, 0) + 1
        if step_order in self._fail_first_for and self._attempts_by_order[step_order] == 1:
            raise RuntimeError("temporary failure")
        return StepResult(output={"result": f"{step.agent_type}: {step.objective}"})

    @staticmethod
    def _step_order(objective: str) -> int:
        return int(objective.split(":", 1)[0])


def _engine(
    steps: list[PlannedStep],
    *,
    executor: RecordingExecutor | None = None,
) -> tuple[WorkflowEngine, MemoryWorkflowRepository, RecordingExecutor]:
    repo = MemoryWorkflowRepository()
    runner = executor or RecordingExecutor()
    orchestrator = OrchestratorService(
        planner=StaticPlanner(steps),
        router=PassthroughRouter(),
    )
    return (
        WorkflowEngine(orchestrator=orchestrator, repository=repo, executor=runner),
        repo,
        runner,
    )


@pytest.mark.asyncio
async def test_workflow_run_executes_steps_in_order_and_carries_context() -> None:
    engine, repo, executor = _engine(
        [
            PlannedStep(1, "DocumentAgent", "1: extract summary"),
            PlannedStep(2, "ReportAgent", "2: write report"),
        ]
    )

    result = await engine.run("Analyze the uploaded document", context={"user": "alice"})

    assert result.status == InstanceStatus.COMPLETED
    assert result.current_step is None
    assert [s.status for s in result.steps] == [StepStatus.SUCCEEDED, StepStatus.SUCCEEDED]
    assert [s.attempts for s in result.steps] == [1, 1]
    assert [c.agent_type for c in executor.calls] == ["DocumentAgent", "ReportAgent"]
    assert executor.calls[1].context["step1_DocumentAgent"]["result"] == (
        "DocumentAgent: 1: extract summary"
    )
    assert result.context["user"] == "alice"
    assert result.context["step2_ReportAgent"]["result"] == "ReportAgent: 2: write report"
    assert repo.save_count >= 3


@pytest.mark.asyncio
async def test_workflow_retries_a_failed_step_before_advancing() -> None:
    engine, _repo, executor = _engine(
        [PlannedStep(1, "AnalysisAgent", "1: analyze data")],
        executor=RecordingExecutor(fail_first_for={1}),
    )

    result = await engine.run("Analyze data")

    assert result.status == InstanceStatus.COMPLETED
    assert result.steps[0].status == StepStatus.SUCCEEDED
    assert result.steps[0].attempts == 2
    assert len(executor.calls) == 2


@pytest.mark.asyncio
async def test_workflow_waits_for_human_approval_then_resumes() -> None:
    engine, _repo, executor = _engine(
        [
            PlannedStep(
                1,
                "ExecutionAgent",
                "1: run sensitive action",
                requires_approval=True,
            ),
            PlannedStep(2, "ReportAgent", "2: report result"),
        ]
    )

    waiting = await engine.run("Run a sensitive workflow")

    assert waiting.status == InstanceStatus.WAITING
    assert waiting.current_step == 1
    assert waiting.steps[0].status == StepStatus.AWAITING_APPROVAL
    assert executor.calls == []

    completed = await engine.resume(waiting.id, approved=True)

    assert completed.status == InstanceStatus.COMPLETED
    assert [s.status for s in completed.steps] == [StepStatus.SUCCEEDED, StepStatus.SUCCEEDED]
    assert [c.agent_type for c in executor.calls] == ["ExecutionAgent", "ReportAgent"]


@pytest.mark.asyncio
async def test_workflow_rejection_cancels_pending_approval() -> None:
    engine, _repo, executor = _engine(
        [
            PlannedStep(
                1,
                "ExecutionAgent",
                "1: delete external resource",
                requires_approval=True,
            )
        ]
    )

    waiting = await engine.run("Delete an external resource")
    cancelled = await engine.resume(waiting.id, approved=False)

    assert cancelled.status == InstanceStatus.CANCELLED
    assert cancelled.steps[0].status == StepStatus.FAILED
    assert cancelled.steps[0].error == "Rejected by approver"
    assert executor.calls == []

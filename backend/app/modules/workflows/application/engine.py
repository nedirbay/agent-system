"""Workflow Engine (Roadmap Task 13).

Turns an Orchestrator plan into a persisted, observable instance and executes
its steps in order, carrying a context between them (EX-003), applying per-step
retries (EH-001) and pausing on human-approval steps (HA-001). The MVP runs
steps in-process; the event-driven dispatch model (EX-001) slots in behind the
same `StepExecutor` port without changing this code.
"""
from __future__ import annotations

import uuid
from typing import Awaitable, Callable

from app.core.config import get_settings
from app.core.exceptions import AppError, NotFoundError
from app.modules.agents.application.orchestrator import OrchestratorService
from app.modules.workflows.domain.executor import StepExecutor, StepRequest
from app.modules.workflows.domain.instance import (
    InstanceStatus,
    StepStatus,
    WorkflowInstance,
    WorkflowInstanceRepository,
    WorkflowStep,
)

# Progress callback: receives a JSON-serialisable event dict (real-time UI).
ProgressHook = Callable[[dict], Awaitable[None]]

# Cap streamed step results so the SSE frame stays bounded, but generous enough
# that the Chat UI can show a full agent answer (not just a snippet).
_RESULT_PREVIEW = 4000


async def _emit(on_event: ProgressHook | None, event: dict) -> None:
    if on_event is not None:
        await on_event(event)


class WorkflowEngine:
    def __init__(
        self,
        *,
        orchestrator: OrchestratorService,
        repository: WorkflowInstanceRepository,
        executor: StepExecutor,
    ) -> None:
        self._orchestrator = orchestrator
        self._repo = repository
        self._executor = executor
        settings = get_settings()
        self._max_attempts = settings.workflow_max_attempts

    async def run(
        self,
        request: str,
        *,
        task_id: uuid.UUID | None = None,
        context: dict | None = None,
        on_event: ProgressHook | None = None,
    ) -> WorkflowInstance:
        """Plan, materialise, persist and execute a workflow for a request."""
        await _emit(on_event, {"type": "planning", "request": request})
        plan = await self._orchestrator.plan(request)
        instance = WorkflowInstance(
            task_id=task_id,
            request=request,
            summary=plan.summary,
            status=InstanceStatus.RUNNING,
            context=dict(context or {}),
            fallback=plan.fallback,
            steps=[
                WorkflowStep(
                    instance_id=None,  # set on persist
                    step_order=s.step_order,
                    agent_type=s.agent_type,
                    objective=s.objective,
                    tier=s.tier,
                    model=s.model,
                    requires_approval=s.requires_approval,
                )
                for s in plan.steps
            ],
        )
        for step in instance.steps:
            step.instance_id = instance.id
        await self._repo.add(instance)
        await _emit(
            on_event,
            {
                "type": "plan",
                "instance_id": str(instance.id),
                "summary": instance.summary,
                "fallback": instance.fallback,
                "steps": [
                    {
                        "order": s.step_order,
                        "agent_type": s.agent_type,
                        "objective": s.objective,
                        "requires_approval": s.requires_approval,
                    }
                    for s in instance.steps
                ],
            },
        )
        return await self._drive(instance, on_event=on_event)

    async def get(self, instance_id: uuid.UUID) -> WorkflowInstance:
        instance = await self._repo.get(instance_id)
        if instance is None:
            raise NotFoundError("Workflow instance not found")
        return instance

    async def list(self, *, limit: int = 100, offset: int = 0) -> list[WorkflowInstance]:
        return await self._repo.list(limit=limit, offset=offset)

    async def resume(
        self,
        instance_id: uuid.UUID,
        *,
        approved: bool,
        on_event: ProgressHook | None = None,
    ) -> WorkflowInstance:
        """Approve/reject the pending step of a Waiting instance (HA-002)."""
        instance = await self.get(instance_id)
        if instance.status != InstanceStatus.WAITING:
            raise AppError("Workflow is not waiting for approval")
        pending = next(
            (s for s in instance.steps if s.status == StepStatus.AWAITING_APPROVAL), None
        )
        if pending is None:
            raise AppError("No step is awaiting approval")
        if not approved:
            pending.status = StepStatus.FAILED
            pending.error = "Rejected by approver"
            instance.status = InstanceStatus.CANCELLED
            await self._repo.save(instance)
            return instance
        pending.requires_approval = False  # cleared by approval
        instance.status = InstanceStatus.RUNNING
        await self._repo.save(instance)
        return await self._drive(instance, on_event=on_event)

    # --- core execution loop (EX-004 advancement) ---
    async def _drive(
        self, instance: WorkflowInstance, *, on_event: ProgressHook | None = None
    ) -> WorkflowInstance:
        for step in instance.steps:
            if step.status in (StepStatus.SUCCEEDED, StepStatus.SKIPPED):
                continue

            # Human Approval gate (HA-001/HA-003).
            if step.requires_approval:
                step.status = StepStatus.AWAITING_APPROVAL
                instance.status = InstanceStatus.WAITING
                instance.current_step = step.step_order
                await self._repo.save(instance)
                await _emit(
                    on_event,
                    {
                        "type": "awaiting_approval",
                        "order": step.step_order,
                        "agent_type": step.agent_type,
                        "objective": step.objective,
                    },
                )
                return instance

            instance.current_step = step.step_order
            await _emit(
                on_event,
                {
                    "type": "step_started",
                    "order": step.step_order,
                    "agent_type": step.agent_type,
                    "objective": step.objective,
                },
            )
            ok = await self._run_step(instance, step)
            await self._repo.save(instance)
            if not ok:
                instance.status = InstanceStatus.FAILED
                await self._repo.save(instance)
                await _emit(
                    on_event,
                    {
                        "type": "step_failed",
                        "order": step.step_order,
                        "agent_type": step.agent_type,
                        "attempts": step.attempts,
                        "error": step.error,
                    },
                )
                await _emit(
                    on_event,
                    {
                        "type": "failed",
                        "instance_id": str(instance.id),
                        "status": instance.status,
                    },
                )
                return instance

            await _emit(on_event, self._step_completed_event(step))

        instance.status = InstanceStatus.COMPLETED
        instance.current_step = None
        await self._repo.save(instance)
        await _emit(
            on_event,
            {
                "type": "completed",
                "instance_id": str(instance.id),
                "status": instance.status,
            },
        )
        return instance

    @staticmethod
    def _step_completed_event(step: WorkflowStep) -> dict:
        output = step.output if isinstance(step.output, dict) else {}
        result = str(output.get("result") or "")
        if len(result) > _RESULT_PREVIEW:
            result = result[:_RESULT_PREVIEW].rstrip() + "…"
        return {
            "type": "step_completed",
            "order": step.step_order,
            "agent_type": step.agent_type,
            "attempts": step.attempts,
            # "agent" is set only when a real specialized agent ran (vs LLM fallback).
            "executed_by": output.get("agent") or "llm-roleplay",
            "result": result,
        }

    async def _run_step(self, instance: WorkflowInstance, step: WorkflowStep) -> bool:
        step.status = StepStatus.RUNNING
        last_error = ""
        while step.attempts < self._max_attempts:
            step.attempts += 1
            try:
                result = await self._executor.execute(
                    StepRequest(
                        agent_type=step.agent_type,
                        objective=step.objective,
                        model=step.model,
                        request=instance.request,
                        context=instance.context,
                    )
                )
                step.output = result.output
                step.status = StepStatus.SUCCEEDED
                step.error = None
                # outputMapping: write this step's output into the context (EX-003).
                key = f"step{step.step_order}_{step.agent_type}"
                instance.context[key] = result.output
                return True
            except Exception as exc:  # retry within budget (EH-001)
                last_error = f"{type(exc).__name__}: {exc}"
        step.status = StepStatus.FAILED
        step.error = last_error
        return False

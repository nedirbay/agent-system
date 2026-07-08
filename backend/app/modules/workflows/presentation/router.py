from __future__ import annotations

import asyncio
import json
import uuid

from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse

from app.modules.workflows.application.commands import CreateWorkflowCommand
from app.modules.workflows.application.engine import WorkflowEngine
from app.modules.workflows.application.services import WorkflowService
from app.modules.workflows.domain.instance import WorkflowInstance
from app.modules.workflows.presentation.dependencies import (
    get_workflow_engine,
    get_workflow_service,
)
from app.modules.workflows.presentation.schemas import (
    ApprovalRequest,
    RunWorkflowRequest,
    WorkflowCreate,
    WorkflowInstanceRead,
    WorkflowRead,
    WorkflowStepRead,
)

router = APIRouter(prefix="/workflows", tags=["Workflows"])


def _to_instance_read(instance: WorkflowInstance) -> WorkflowInstanceRead:
    return WorkflowInstanceRead(
        id=instance.id,
        created_at=instance.created_at,
        task_id=instance.task_id,
        request=instance.request,
        summary=instance.summary,
        status=instance.status,
        current_step=instance.current_step,
        fallback=instance.fallback,
        context=instance.context,
        steps=[
            WorkflowStepRead(
                id=s.id,
                step_order=s.step_order,
                agent_type=s.agent_type,
                objective=s.objective,
                tier=s.tier,
                model=s.model,
                requires_approval=s.requires_approval,
                status=s.status,
                attempts=s.attempts,
                output=s.output,
                error=s.error,
            )
            for s in instance.steps
        ],
    )


@router.post("/run", response_model=WorkflowInstanceRead)
async def run_workflow(
    payload: RunWorkflowRequest,
    engine: WorkflowEngine = Depends(get_workflow_engine),
) -> WorkflowInstanceRead:
    """Plan, route and execute a dynamic workflow for a request (Tasks 11–13)."""
    instance = await engine.run(
        payload.request, task_id=payload.task_id, context=payload.context
    )
    return _to_instance_read(instance)


@router.post("/run/stream")
async def run_workflow_stream(
    payload: RunWorkflowRequest,
    engine: WorkflowEngine = Depends(get_workflow_engine),
) -> StreamingResponse:
    """Run a workflow and stream per-step progress as Server-Sent Events.

    Emits one ``data: {json}`` line per event (planning, plan, step_started,
    step_completed/step_failed, awaiting_approval, completed/failed) so the UI
    can render the agents working in real time.
    """
    queue: asyncio.Queue[dict | None] = asyncio.Queue()

    async def emit(event: dict) -> None:
        await queue.put(event)

    async def runner() -> None:
        try:
            await engine.run(
                payload.request,
                task_id=payload.task_id,
                context=payload.context,
                on_event=emit,
            )
        except Exception as exc:  # surface failures to the client, then close
            await queue.put({"type": "error", "message": str(exc)})
        finally:
            await queue.put(None)  # sentinel: end of stream

    async def event_stream():
        task = asyncio.create_task(runner())
        try:
            while True:
                event = await queue.get()
                if event is None:
                    break
                yield f"data: {json.dumps(event)}\n\n"
        finally:
            await task

    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )


@router.get("/instances", response_model=list[WorkflowInstanceRead])
async def list_instances(
    limit: int = 50,
    offset: int = 0,
    engine: WorkflowEngine = Depends(get_workflow_engine),
) -> list[WorkflowInstanceRead]:
    items = await engine.list(limit=limit, offset=offset)
    return [_to_instance_read(i) for i in items]


@router.get("/instances/{instance_id}", response_model=WorkflowInstanceRead)
async def get_instance(
    instance_id: uuid.UUID,
    engine: WorkflowEngine = Depends(get_workflow_engine),
) -> WorkflowInstanceRead:
    return _to_instance_read(await engine.get(instance_id))


@router.post("/instances/{instance_id}/approve", response_model=WorkflowInstanceRead)
async def approve_instance(
    instance_id: uuid.UUID,
    payload: ApprovalRequest,
    engine: WorkflowEngine = Depends(get_workflow_engine),
) -> WorkflowInstanceRead:
    """Approve/reject a Waiting instance's pending step and resume it (HA-002)."""
    instance = await engine.resume(instance_id, approved=payload.approved)
    return _to_instance_read(instance)


@router.post("", response_model=WorkflowRead, status_code=201)
async def create_workflow(
    payload: WorkflowCreate,
    service: WorkflowService = Depends(get_workflow_service),
) -> WorkflowRead:
    command = CreateWorkflowCommand(**payload.model_dump())
    entity = await service.create(command)
    return WorkflowRead.model_validate(entity)


@router.get("", response_model=list[WorkflowRead])
async def list_workflow(
    limit: int = 100,
    offset: int = 0,
    service: WorkflowService = Depends(get_workflow_service),
) -> list[WorkflowRead]:
    items = await service.list(limit=limit, offset=offset)
    return [WorkflowRead.model_validate(i) for i in items]


@router.get("/{item_id}", response_model=WorkflowRead)
async def get_workflow(
    item_id: uuid.UUID,
    service: WorkflowService = Depends(get_workflow_service),
) -> WorkflowRead:
    entity = await service.get(item_id)
    return WorkflowRead.model_validate(entity)

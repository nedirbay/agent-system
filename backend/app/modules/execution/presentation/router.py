from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends

from app.modules.execution.application.commands import CreateExecutionRunCommand
from app.modules.execution.application.execution_agent import (
    ExecutionAgentService,
    ExecutionReport,
)
from app.modules.execution.application.services import ExecutionRunService
from app.modules.execution.domain.actions import Action
from app.modules.execution.presentation.dependencies import (
    get_execution_agent_service,
    get_executionrun_service,
)
from app.modules.execution.presentation.schemas import (
    ActionIn,
    ActionOutcomeRead,
    ExecutionReportRead,
    ExecutionRunCreate,
    ExecutionRunRead,
    PreviewRequest,
    RunActionRequest,
    RunPlanRequest,
)

router = APIRouter(prefix="/execution", tags=["Execution"])


# --- Computer Use / Execution Agent (Faza 7 / AG-008, FR-015) ---


def _to_action(payload: ActionIn) -> Action:
    return Action(kind=payload.kind, type=payload.type, params=payload.params)


def _report_read(report: ExecutionReport) -> ExecutionReportRead:
    return ExecutionReportRead(
        run_id=report.run_id,
        status=report.status,
        outcomes=[ActionOutcomeRead(**vars(o)) for o in report.outcomes],
    )


@router.post("/preview", response_model=list[ActionOutcomeRead])
async def preview_plan(
    payload: PreviewRequest,
    service: ExecutionAgentService = Depends(get_execution_agent_service),
) -> list[ActionOutcomeRead]:
    """Classify each action against the sandbox without executing anything."""
    outcomes = service.preview([_to_action(a) for a in payload.actions])
    return [ActionOutcomeRead(**vars(o)) for o in outcomes]


@router.post("/actions", response_model=ExecutionReportRead)
async def run_action(
    payload: RunActionRequest,
    service: ExecutionAgentService = Depends(get_execution_agent_service),
) -> ExecutionReportRead:
    report = await service.run_action(_to_action(payload.action), approved=payload.approved)
    return _report_read(report)


@router.post("/plan", response_model=ExecutionReportRead)
async def run_plan(
    payload: RunPlanRequest,
    service: ExecutionAgentService = Depends(get_execution_agent_service),
) -> ExecutionReportRead:
    report = await service.run_plan(
        [_to_action(a) for a in payload.actions], approved=payload.approved
    )
    return _report_read(report)


# --- CRUD (scaffold) ---


@router.post("", response_model=ExecutionRunRead, status_code=201)
async def create_executionrun(
    payload: ExecutionRunCreate,
    service: ExecutionRunService = Depends(get_executionrun_service),
) -> ExecutionRunRead:
    command = CreateExecutionRunCommand(**payload.model_dump())
    entity = await service.create(command)
    return ExecutionRunRead.model_validate(entity)


@router.get("", response_model=list[ExecutionRunRead])
async def list_executionrun(
    limit: int = 100,
    offset: int = 0,
    service: ExecutionRunService = Depends(get_executionrun_service),
) -> list[ExecutionRunRead]:
    items = await service.list(limit=limit, offset=offset)
    return [ExecutionRunRead.model_validate(i) for i in items]


@router.get("/{item_id}", response_model=ExecutionRunRead)
async def get_executionrun(
    item_id: uuid.UUID,
    service: ExecutionRunService = Depends(get_executionrun_service),
) -> ExecutionRunRead:
    entity = await service.get(item_id)
    return ExecutionRunRead.model_validate(entity)

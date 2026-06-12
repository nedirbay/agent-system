from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends

from app.modules.workflows.application.commands import CreateWorkflowCommand
from app.modules.workflows.application.services import WorkflowService
from app.modules.workflows.presentation.dependencies import get_workflow_service
from app.modules.workflows.presentation.schemas import WorkflowCreate, WorkflowRead

router = APIRouter(prefix="/workflows", tags=["Workflows"])


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

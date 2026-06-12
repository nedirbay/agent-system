from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends

from app.modules.execution.application.commands import CreateExecutionRunCommand
from app.modules.execution.application.services import ExecutionRunService
from app.modules.execution.presentation.dependencies import get_executionrun_service
from app.modules.execution.presentation.schemas import ExecutionRunCreate, ExecutionRunRead

router = APIRouter(prefix="/execution", tags=["Execution"])


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

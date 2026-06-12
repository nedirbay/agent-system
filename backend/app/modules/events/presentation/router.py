from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends

from app.modules.events.application.commands import CreateSystemEventCommand
from app.modules.events.application.services import SystemEventService
from app.modules.events.presentation.dependencies import get_systemevent_service
from app.modules.events.presentation.schemas import SystemEventCreate, SystemEventRead

router = APIRouter(prefix="/events", tags=["Events"])


@router.post("", response_model=SystemEventRead, status_code=201)
async def create_systemevent(
    payload: SystemEventCreate,
    service: SystemEventService = Depends(get_systemevent_service),
) -> SystemEventRead:
    command = CreateSystemEventCommand(**payload.model_dump())
    entity = await service.create(command)
    return SystemEventRead.model_validate(entity)


@router.get("", response_model=list[SystemEventRead])
async def list_systemevent(
    limit: int = 100,
    offset: int = 0,
    service: SystemEventService = Depends(get_systemevent_service),
) -> list[SystemEventRead]:
    items = await service.list(limit=limit, offset=offset)
    return [SystemEventRead.model_validate(i) for i in items]


@router.get("/{item_id}", response_model=SystemEventRead)
async def get_systemevent(
    item_id: uuid.UUID,
    service: SystemEventService = Depends(get_systemevent_service),
) -> SystemEventRead:
    entity = await service.get(item_id)
    return SystemEventRead.model_validate(entity)

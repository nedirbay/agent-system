from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends

from app.modules.memory.application.commands import CreateMemoryItemCommand
from app.modules.memory.application.services import MemoryItemService
from app.modules.memory.presentation.dependencies import get_memoryitem_service
from app.modules.memory.presentation.schemas import MemoryItemCreate, MemoryItemRead

router = APIRouter(prefix="/memory", tags=["Memory"])


@router.post("", response_model=MemoryItemRead, status_code=201)
async def create_memoryitem(
    payload: MemoryItemCreate,
    service: MemoryItemService = Depends(get_memoryitem_service),
) -> MemoryItemRead:
    command = CreateMemoryItemCommand(**payload.model_dump())
    entity = await service.create(command)
    return MemoryItemRead.model_validate(entity)


@router.get("", response_model=list[MemoryItemRead])
async def list_memoryitem(
    limit: int = 100,
    offset: int = 0,
    service: MemoryItemService = Depends(get_memoryitem_service),
) -> list[MemoryItemRead]:
    items = await service.list(limit=limit, offset=offset)
    return [MemoryItemRead.model_validate(i) for i in items]


@router.get("/{item_id}", response_model=MemoryItemRead)
async def get_memoryitem(
    item_id: uuid.UUID,
    service: MemoryItemService = Depends(get_memoryitem_service),
) -> MemoryItemRead:
    entity = await service.get(item_id)
    return MemoryItemRead.model_validate(entity)

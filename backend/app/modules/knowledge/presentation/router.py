from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends

from app.modules.knowledge.application.commands import CreateKnowledgeItemCommand
from app.modules.knowledge.application.services import KnowledgeItemService
from app.modules.knowledge.presentation.dependencies import get_knowledgeitem_service
from app.modules.knowledge.presentation.schemas import KnowledgeItemCreate, KnowledgeItemRead

router = APIRouter(prefix="/knowledge", tags=["Knowledge"])


@router.post("", response_model=KnowledgeItemRead, status_code=201)
async def create_knowledgeitem(
    payload: KnowledgeItemCreate,
    service: KnowledgeItemService = Depends(get_knowledgeitem_service),
) -> KnowledgeItemRead:
    command = CreateKnowledgeItemCommand(**payload.model_dump())
    entity = await service.create(command)
    return KnowledgeItemRead.model_validate(entity)


@router.get("", response_model=list[KnowledgeItemRead])
async def list_knowledgeitem(
    limit: int = 100,
    offset: int = 0,
    service: KnowledgeItemService = Depends(get_knowledgeitem_service),
) -> list[KnowledgeItemRead]:
    items = await service.list(limit=limit, offset=offset)
    return [KnowledgeItemRead.model_validate(i) for i in items]


@router.get("/{item_id}", response_model=KnowledgeItemRead)
async def get_knowledgeitem(
    item_id: uuid.UUID,
    service: KnowledgeItemService = Depends(get_knowledgeitem_service),
) -> KnowledgeItemRead:
    entity = await service.get(item_id)
    return KnowledgeItemRead.model_validate(entity)

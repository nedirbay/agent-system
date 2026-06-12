from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends

from app.modules.qa.application.commands import CreateQaConversationCommand
from app.modules.qa.application.services import QaConversationService
from app.modules.qa.presentation.dependencies import get_qaconversation_service
from app.modules.qa.presentation.schemas import QaConversationCreate, QaConversationRead

router = APIRouter(prefix="/qa", tags=["Q&A"])


@router.post("", response_model=QaConversationRead, status_code=201)
async def create_qaconversation(
    payload: QaConversationCreate,
    service: QaConversationService = Depends(get_qaconversation_service),
) -> QaConversationRead:
    command = CreateQaConversationCommand(**payload.model_dump())
    entity = await service.create(command)
    return QaConversationRead.model_validate(entity)


@router.get("", response_model=list[QaConversationRead])
async def list_qaconversation(
    limit: int = 100,
    offset: int = 0,
    service: QaConversationService = Depends(get_qaconversation_service),
) -> list[QaConversationRead]:
    items = await service.list(limit=limit, offset=offset)
    return [QaConversationRead.model_validate(i) for i in items]


@router.get("/{item_id}", response_model=QaConversationRead)
async def get_qaconversation(
    item_id: uuid.UUID,
    service: QaConversationService = Depends(get_qaconversation_service),
) -> QaConversationRead:
    entity = await service.get(item_id)
    return QaConversationRead.model_validate(entity)

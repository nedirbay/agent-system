from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends

from app.modules.notifications.application.commands import CreateNotificationCommand
from app.modules.notifications.application.services import NotificationService
from app.modules.notifications.presentation.dependencies import get_notification_service
from app.modules.notifications.presentation.schemas import NotificationCreate, NotificationRead

router = APIRouter(prefix="/notifications", tags=["Notifications"])


@router.post("", response_model=NotificationRead, status_code=201)
async def create_notification(
    payload: NotificationCreate,
    service: NotificationService = Depends(get_notification_service),
) -> NotificationRead:
    command = CreateNotificationCommand(**payload.model_dump())
    entity = await service.create(command)
    return NotificationRead.model_validate(entity)


@router.get("", response_model=list[NotificationRead])
async def list_notification(
    limit: int = 100,
    offset: int = 0,
    service: NotificationService = Depends(get_notification_service),
) -> list[NotificationRead]:
    items = await service.list(limit=limit, offset=offset)
    return [NotificationRead.model_validate(i) for i in items]


@router.get("/{item_id}", response_model=NotificationRead)
async def get_notification(
    item_id: uuid.UUID,
    service: NotificationService = Depends(get_notification_service),
) -> NotificationRead:
    entity = await service.get(item_id)
    return NotificationRead.model_validate(entity)

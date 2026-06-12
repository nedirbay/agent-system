from __future__ import annotations

import uuid

from app.core.exceptions import NotFoundError
from app.modules.notifications.domain.entities import Notification
from app.modules.notifications.domain.repositories import NotificationRepository
from app.modules.notifications.application.commands import CreateNotificationCommand


class NotificationService:
    """Application service orchestrating Notification use cases."""

    def __init__(self, repository: NotificationRepository) -> None:
        self._repo = repository

    async def create(self, command: CreateNotificationCommand) -> Notification:
        entity = Notification(user_id=command.user_id, title=command.title, message=command.message, is_read=command.is_read)
        return await self._repo.add(entity)

    async def get(self, entity_id: uuid.UUID) -> Notification:
        entity = await self._repo.get(entity_id)
        if entity is None:
            raise NotFoundError("Notification not found")
        return entity

    async def list(self, *, limit: int = 100, offset: int = 0) -> list[Notification]:
        return await self._repo.list(limit=limit, offset=offset)

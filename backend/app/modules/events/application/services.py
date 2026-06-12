from __future__ import annotations

import uuid

from app.core.exceptions import NotFoundError
from app.modules.events.domain.entities import SystemEvent
from app.modules.events.domain.repositories import SystemEventRepository
from app.modules.events.application.commands import CreateSystemEventCommand


class SystemEventService:
    """Application service orchestrating SystemEvent use cases."""

    def __init__(self, repository: SystemEventRepository) -> None:
        self._repo = repository

    async def create(self, command: CreateSystemEventCommand) -> SystemEvent:
        entity = SystemEvent(event_type=command.event_type, task_id=command.task_id, payload=command.payload, status=command.status)
        return await self._repo.add(entity)

    async def get(self, entity_id: uuid.UUID) -> SystemEvent:
        entity = await self._repo.get(entity_id)
        if entity is None:
            raise NotFoundError("SystemEvent not found")
        return entity

    async def list(self, *, limit: int = 100, offset: int = 0) -> list[SystemEvent]:
        return await self._repo.list(limit=limit, offset=offset)

from __future__ import annotations

import uuid

from app.core.exceptions import NotFoundError
from app.modules.memory.domain.entities import MemoryItem
from app.modules.memory.domain.repositories import MemoryItemRepository
from app.modules.memory.application.commands import CreateMemoryItemCommand


class MemoryItemService:
    """Application service orchestrating MemoryItem use cases."""

    def __init__(self, repository: MemoryItemRepository) -> None:
        self._repo = repository

    async def create(self, command: CreateMemoryItemCommand) -> MemoryItem:
        entity = MemoryItem(memory_type=command.memory_type, content=command.content, importance_score=command.importance_score)
        return await self._repo.add(entity)

    async def get(self, entity_id: uuid.UUID) -> MemoryItem:
        entity = await self._repo.get(entity_id)
        if entity is None:
            raise NotFoundError("MemoryItem not found")
        return entity

    async def list(self, *, limit: int = 100, offset: int = 0) -> list[MemoryItem]:
        return await self._repo.list(limit=limit, offset=offset)

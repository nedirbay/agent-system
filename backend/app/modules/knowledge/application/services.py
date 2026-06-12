from __future__ import annotations

import uuid

from app.core.exceptions import NotFoundError
from app.modules.knowledge.domain.entities import KnowledgeItem
from app.modules.knowledge.domain.repositories import KnowledgeItemRepository
from app.modules.knowledge.application.commands import CreateKnowledgeItemCommand


class KnowledgeItemService:
    """Application service orchestrating KnowledgeItem use cases."""

    def __init__(self, repository: KnowledgeItemRepository) -> None:
        self._repo = repository

    async def create(self, command: CreateKnowledgeItemCommand) -> KnowledgeItem:
        entity = KnowledgeItem(source_type=command.source_type, source_id=command.source_id, title=command.title, content=command.content)
        return await self._repo.add(entity)

    async def get(self, entity_id: uuid.UUID) -> KnowledgeItem:
        entity = await self._repo.get(entity_id)
        if entity is None:
            raise NotFoundError("KnowledgeItem not found")
        return entity

    async def list(self, *, limit: int = 100, offset: int = 0) -> list[KnowledgeItem]:
        return await self._repo.list(limit=limit, offset=offset)

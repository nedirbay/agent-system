from __future__ import annotations

import uuid

from app.core.exceptions import NotFoundError
from app.modules.qa.domain.entities import QaConversation
from app.modules.qa.domain.repositories import QaConversationRepository
from app.modules.qa.application.commands import CreateQaConversationCommand


class QaConversationService:
    """Application service orchestrating QaConversation use cases."""

    def __init__(self, repository: QaConversationRepository) -> None:
        self._repo = repository

    async def create(self, command: CreateQaConversationCommand) -> QaConversation:
        entity = QaConversation(user_id=command.user_id, title=command.title)
        return await self._repo.add(entity)

    async def get(self, entity_id: uuid.UUID) -> QaConversation:
        entity = await self._repo.get(entity_id)
        if entity is None:
            raise NotFoundError("QaConversation not found")
        return entity

    async def list(self, *, limit: int = 100, offset: int = 0) -> list[QaConversation]:
        return await self._repo.list(limit=limit, offset=offset)

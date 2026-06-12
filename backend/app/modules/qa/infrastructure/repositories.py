from __future__ import annotations

import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.qa.domain.entities import QaConversation
from app.modules.qa.domain.repositories import QaConversationRepository
from app.modules.qa.infrastructure.models import QaConversationModel


def _to_entity(model: QaConversationModel) -> QaConversation:
    return QaConversation(
        id=model.id,
        created_at=model.created_at,
        user_id=model.user_id,
        title=model.title,
    )


class SqlAlchemyQaConversationRepository(QaConversationRepository):
    """SQLAlchemy adapter implementing the QaConversation port."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def add(self, entity: QaConversation) -> QaConversation:
        model = QaConversationModel(
            id=entity.id,
            created_at=entity.created_at,
            user_id=entity.user_id,
            title=entity.title,
        )
        self._session.add(model)
        await self._session.flush()
        return _to_entity(model)

    async def get(self, entity_id: uuid.UUID) -> QaConversation | None:
        model = await self._session.get(QaConversationModel, entity_id)
        return _to_entity(model) if model else None

    async def list(self, *, limit: int = 100, offset: int = 0) -> list[QaConversation]:
        result = await self._session.execute(
            select(QaConversationModel).limit(limit).offset(offset)
        )
        return [_to_entity(m) for m in result.scalars().all()]

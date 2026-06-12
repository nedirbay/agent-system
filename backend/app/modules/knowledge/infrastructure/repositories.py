from __future__ import annotations

import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.knowledge.domain.entities import KnowledgeItem
from app.modules.knowledge.domain.repositories import KnowledgeItemRepository
from app.modules.knowledge.infrastructure.models import KnowledgeItemModel


def _to_entity(model: KnowledgeItemModel) -> KnowledgeItem:
    return KnowledgeItem(
        id=model.id,
        created_at=model.created_at,
        source_type=model.source_type,
        source_id=model.source_id,
        title=model.title,
        content=model.content,
    )


class SqlAlchemyKnowledgeItemRepository(KnowledgeItemRepository):
    """SQLAlchemy adapter implementing the KnowledgeItem port."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def add(self, entity: KnowledgeItem) -> KnowledgeItem:
        model = KnowledgeItemModel(
            id=entity.id,
            created_at=entity.created_at,
            source_type=entity.source_type,
            source_id=entity.source_id,
            title=entity.title,
            content=entity.content,
        )
        self._session.add(model)
        await self._session.flush()
        return _to_entity(model)

    async def get(self, entity_id: uuid.UUID) -> KnowledgeItem | None:
        model = await self._session.get(KnowledgeItemModel, entity_id)
        return _to_entity(model) if model else None

    async def list(self, *, limit: int = 100, offset: int = 0) -> list[KnowledgeItem]:
        result = await self._session.execute(
            select(KnowledgeItemModel).limit(limit).offset(offset)
        )
        return [_to_entity(m) for m in result.scalars().all()]

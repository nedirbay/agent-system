from __future__ import annotations

import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.memory.domain.entities import MemoryItem
from app.modules.memory.domain.repositories import MemoryItemRepository
from app.modules.memory.infrastructure.models import MemoryItemModel


def _to_entity(model: MemoryItemModel) -> MemoryItem:
    return MemoryItem(
        id=model.id,
        created_at=model.created_at,
        memory_type=model.memory_type,
        content=model.content,
        importance_score=model.importance_score,
    )


class SqlAlchemyMemoryItemRepository(MemoryItemRepository):
    """SQLAlchemy adapter implementing the MemoryItem port."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def add(self, entity: MemoryItem) -> MemoryItem:
        model = MemoryItemModel(
            id=entity.id,
            created_at=entity.created_at,
            memory_type=entity.memory_type,
            content=entity.content,
            importance_score=entity.importance_score,
        )
        self._session.add(model)
        await self._session.flush()
        return _to_entity(model)

    async def get(self, entity_id: uuid.UUID) -> MemoryItem | None:
        model = await self._session.get(MemoryItemModel, entity_id)
        return _to_entity(model) if model else None

    async def list(self, *, limit: int = 100, offset: int = 0) -> list[MemoryItem]:
        result = await self._session.execute(
            select(MemoryItemModel).limit(limit).offset(offset)
        )
        return [_to_entity(m) for m in result.scalars().all()]

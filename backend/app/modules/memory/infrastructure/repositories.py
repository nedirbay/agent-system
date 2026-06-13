from __future__ import annotations

import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.memory.domain.entities import MemoryItem, MemoryReference
from app.modules.memory.domain.repositories import (
    MemoryItemRepository,
    MemoryReferenceRepository,
)
from app.modules.memory.infrastructure.models import (
    MemoryItemModel,
    MemoryReferenceModel,
)


def _to_entity(model: MemoryItemModel) -> MemoryItem:
    return MemoryItem(
        id=model.id,
        created_at=model.created_at,
        memory_type=model.memory_type,
        content=model.content,
        importance_score=model.importance_score,
    )


def _ref_to_entity(model: MemoryReferenceModel) -> MemoryReference:
    return MemoryReference(
        id=model.id,
        created_at=model.created_at,
        memory_id=model.memory_id,
        related_entity_type=model.related_entity_type,
        related_entity_id=model.related_entity_id,
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

    async def list_recent(
        self, *, memory_type: str | None = None, limit: int = 20
    ) -> list[MemoryItem]:
        stmt = select(MemoryItemModel).order_by(MemoryItemModel.created_at.desc())
        if memory_type is not None:
            stmt = stmt.where(MemoryItemModel.memory_type == memory_type)
        result = await self._session.execute(stmt.limit(limit))
        return [_to_entity(m) for m in result.scalars().all()]


class SqlAlchemyMemoryReferenceRepository(MemoryReferenceRepository):
    """SQLAlchemy adapter implementing the MemoryReference port."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def add(self, entity: MemoryReference) -> MemoryReference:
        model = MemoryReferenceModel(
            id=entity.id,
            created_at=entity.created_at,
            memory_id=entity.memory_id,
            related_entity_type=entity.related_entity_type,
            related_entity_id=entity.related_entity_id,
        )
        self._session.add(model)
        await self._session.flush()
        return _ref_to_entity(model)

    async def get(self, entity_id: uuid.UUID) -> MemoryReference | None:
        model = await self._session.get(MemoryReferenceModel, entity_id)
        return _ref_to_entity(model) if model else None

    async def list(self, *, limit: int = 100, offset: int = 0) -> list[MemoryReference]:
        result = await self._session.execute(
            select(MemoryReferenceModel).limit(limit).offset(offset)
        )
        return [_ref_to_entity(m) for m in result.scalars().all()]

    async def list_for_memory(self, memory_id: uuid.UUID) -> list[MemoryReference]:
        result = await self._session.execute(
            select(MemoryReferenceModel).where(
                MemoryReferenceModel.memory_id == memory_id
            )
        )
        return [_ref_to_entity(m) for m in result.scalars().all()]

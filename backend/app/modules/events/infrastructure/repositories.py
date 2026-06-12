from __future__ import annotations

import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.events.domain.entities import SystemEvent
from app.modules.events.domain.repositories import SystemEventRepository
from app.modules.events.infrastructure.models import SystemEventModel


def _to_entity(model: SystemEventModel) -> SystemEvent:
    return SystemEvent(
        id=model.id,
        created_at=model.created_at,
        event_type=model.event_type,
        task_id=model.task_id,
        payload=model.payload,
        status=model.status,
    )


class SqlAlchemySystemEventRepository(SystemEventRepository):
    """SQLAlchemy adapter implementing the SystemEvent port."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def add(self, entity: SystemEvent) -> SystemEvent:
        model = SystemEventModel(
            id=entity.id,
            created_at=entity.created_at,
            event_type=entity.event_type,
            task_id=entity.task_id,
            payload=entity.payload,
            status=entity.status,
        )
        self._session.add(model)
        await self._session.flush()
        return _to_entity(model)

    async def get(self, entity_id: uuid.UUID) -> SystemEvent | None:
        model = await self._session.get(SystemEventModel, entity_id)
        return _to_entity(model) if model else None

    async def list(self, *, limit: int = 100, offset: int = 0) -> list[SystemEvent]:
        result = await self._session.execute(
            select(SystemEventModel).limit(limit).offset(offset)
        )
        return [_to_entity(m) for m in result.scalars().all()]

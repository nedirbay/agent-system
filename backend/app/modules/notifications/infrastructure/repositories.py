from __future__ import annotations

import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.notifications.domain.entities import Notification
from app.modules.notifications.domain.repositories import NotificationRepository
from app.modules.notifications.infrastructure.models import NotificationModel


def _to_entity(model: NotificationModel) -> Notification:
    return Notification(
        id=model.id,
        created_at=model.created_at,
        user_id=model.user_id,
        title=model.title,
        message=model.message,
        is_read=model.is_read,
    )


class SqlAlchemyNotificationRepository(NotificationRepository):
    """SQLAlchemy adapter implementing the Notification port."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def add(self, entity: Notification) -> Notification:
        model = NotificationModel(
            id=entity.id,
            created_at=entity.created_at,
            user_id=entity.user_id,
            title=entity.title,
            message=entity.message,
            is_read=entity.is_read,
        )
        self._session.add(model)
        await self._session.flush()
        return _to_entity(model)

    async def get(self, entity_id: uuid.UUID) -> Notification | None:
        model = await self._session.get(NotificationModel, entity_id)
        return _to_entity(model) if model else None

    async def list(self, *, limit: int = 100, offset: int = 0) -> list[Notification]:
        result = await self._session.execute(
            select(NotificationModel).limit(limit).offset(offset)
        )
        return [_to_entity(m) for m in result.scalars().all()]

from __future__ import annotations

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_session
from app.modules.notifications.application.services import NotificationService
from app.modules.notifications.infrastructure.repositories import SqlAlchemyNotificationRepository


def get_notification_service(session: AsyncSession = Depends(get_session)) -> NotificationService:
    return NotificationService(SqlAlchemyNotificationRepository(session))

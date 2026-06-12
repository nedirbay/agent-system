from __future__ import annotations

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_session
from app.modules.events.application.services import SystemEventService
from app.modules.events.infrastructure.repositories import SqlAlchemySystemEventRepository


def get_systemevent_service(session: AsyncSession = Depends(get_session)) -> SystemEventService:
    return SystemEventService(SqlAlchemySystemEventRepository(session))

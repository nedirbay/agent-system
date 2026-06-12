from __future__ import annotations

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_session
from app.modules.memory.application.services import MemoryItemService
from app.modules.memory.infrastructure.repositories import SqlAlchemyMemoryItemRepository


def get_memoryitem_service(session: AsyncSession = Depends(get_session)) -> MemoryItemService:
    return MemoryItemService(SqlAlchemyMemoryItemRepository(session))

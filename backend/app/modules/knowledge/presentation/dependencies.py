from __future__ import annotations

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_session
from app.modules.knowledge.application.services import KnowledgeItemService
from app.modules.knowledge.infrastructure.repositories import SqlAlchemyKnowledgeItemRepository


def get_knowledgeitem_service(session: AsyncSession = Depends(get_session)) -> KnowledgeItemService:
    return KnowledgeItemService(SqlAlchemyKnowledgeItemRepository(session))

from __future__ import annotations

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_session
from app.modules.qa.application.services import QaConversationService
from app.modules.qa.infrastructure.repositories import SqlAlchemyQaConversationRepository


def get_qaconversation_service(session: AsyncSession = Depends(get_session)) -> QaConversationService:
    return QaConversationService(SqlAlchemyQaConversationRepository(session))

from __future__ import annotations

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_session
from app.modules.agents.application.services import AgentService
from app.modules.agents.infrastructure.repositories import SqlAlchemyAgentRepository


def get_agent_service(session: AsyncSession = Depends(get_session)) -> AgentService:
    return AgentService(SqlAlchemyAgentRepository(session))

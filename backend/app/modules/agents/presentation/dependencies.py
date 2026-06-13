from __future__ import annotations

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_session
from app.modules.agents.application.document_agent import DocumentAgentService
from app.modules.agents.application.orchestrator import OrchestratorService
from app.modules.agents.application.services import AgentService
from app.modules.agents.infrastructure.llm_planner import LlmTaskPlanner
from app.modules.agents.infrastructure.repositories import SqlAlchemyAgentRepository
from app.modules.agents.infrastructure.router import RegistryAgentRouter
from app.modules.documents.infrastructure.repositories import SqlAlchemyDocumentRepository
from app.shared.llm import get_llm_provider


def get_agent_service(session: AsyncSession = Depends(get_session)) -> AgentService:
    return AgentService(SqlAlchemyAgentRepository(session))


def get_orchestrator_service() -> OrchestratorService:
    return OrchestratorService(
        planner=LlmTaskPlanner(get_llm_provider()),
        router=RegistryAgentRouter(),
    )


def get_document_agent_service(
    session: AsyncSession = Depends(get_session),
) -> DocumentAgentService:
    return DocumentAgentService(SqlAlchemyDocumentRepository(session))

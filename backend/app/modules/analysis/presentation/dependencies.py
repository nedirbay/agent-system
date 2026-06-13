from __future__ import annotations

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_session
from app.modules.analysis.application.analysis_agent import AnalysisAgentService
from app.modules.analysis.application.services import AnalysisJobService
from app.modules.analysis.infrastructure.repositories import SqlAlchemyAnalysisJobRepository
from app.modules.documents.infrastructure.repositories import SqlAlchemyDocumentRepository


def get_analysisjob_service(session: AsyncSession = Depends(get_session)) -> AnalysisJobService:
    return AnalysisJobService(SqlAlchemyAnalysisJobRepository(session))


def get_analysis_agent_service(
    session: AsyncSession = Depends(get_session),
) -> AnalysisAgentService:
    return AnalysisAgentService(
        documents=SqlAlchemyDocumentRepository(session),
        jobs=SqlAlchemyAnalysisJobRepository(session),
    )

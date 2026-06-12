from __future__ import annotations

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_session
from app.modules.analysis.application.services import AnalysisJobService
from app.modules.analysis.infrastructure.repositories import SqlAlchemyAnalysisJobRepository


def get_analysisjob_service(session: AsyncSession = Depends(get_session)) -> AnalysisJobService:
    return AnalysisJobService(SqlAlchemyAnalysisJobRepository(session))

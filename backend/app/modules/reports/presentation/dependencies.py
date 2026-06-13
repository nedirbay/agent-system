from __future__ import annotations

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_session
from app.modules.analysis.infrastructure.repositories import SqlAlchemyAnalysisJobRepository
from app.modules.reports.application.report_agent import ReportAgentService
from app.modules.reports.application.services import ReportService
from app.modules.reports.infrastructure.repositories import SqlAlchemyReportRepository


def get_report_service(session: AsyncSession = Depends(get_session)) -> ReportService:
    return ReportService(SqlAlchemyReportRepository(session))


def get_report_agent_service(
    session: AsyncSession = Depends(get_session),
) -> ReportAgentService:
    return ReportAgentService(
        jobs=SqlAlchemyAnalysisJobRepository(session),
        reports=SqlAlchemyReportRepository(session),
    )

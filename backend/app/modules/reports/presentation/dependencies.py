from __future__ import annotations

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_session
from app.modules.reports.application.services import ReportService
from app.modules.reports.infrastructure.repositories import SqlAlchemyReportRepository


def get_report_service(session: AsyncSession = Depends(get_session)) -> ReportService:
    return ReportService(SqlAlchemyReportRepository(session))

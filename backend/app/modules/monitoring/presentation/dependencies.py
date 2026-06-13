from __future__ import annotations

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_session
from app.modules.monitoring.application.services import MonitoringService


def get_monitoring_service(
    session: AsyncSession = Depends(get_session),
) -> MonitoringService:
    return MonitoringService(session)

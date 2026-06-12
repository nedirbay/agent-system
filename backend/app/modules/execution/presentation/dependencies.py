from __future__ import annotations

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_session
from app.modules.execution.application.services import ExecutionRunService
from app.modules.execution.infrastructure.repositories import SqlAlchemyExecutionRunRepository


def get_executionrun_service(session: AsyncSession = Depends(get_session)) -> ExecutionRunService:
    return ExecutionRunService(SqlAlchemyExecutionRunRepository(session))

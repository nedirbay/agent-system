from __future__ import annotations

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_session
from app.modules.workflows.application.services import WorkflowService
from app.modules.workflows.infrastructure.repositories import SqlAlchemyWorkflowRepository


def get_workflow_service(session: AsyncSession = Depends(get_session)) -> WorkflowService:
    return WorkflowService(SqlAlchemyWorkflowRepository(session))

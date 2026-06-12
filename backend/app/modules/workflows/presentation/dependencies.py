from __future__ import annotations

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_session
from app.modules.agents.presentation.dependencies import get_orchestrator_service
from app.modules.workflows.application.engine import WorkflowEngine
from app.modules.workflows.application.services import WorkflowService
from app.modules.workflows.infrastructure.instance_repository import (
    SqlAlchemyWorkflowInstanceRepository,
)
from app.modules.workflows.infrastructure.llm_executor import LlmStepExecutor
from app.modules.workflows.infrastructure.repositories import SqlAlchemyWorkflowRepository
from app.shared.llm import get_llm_provider


def get_workflow_service(session: AsyncSession = Depends(get_session)) -> WorkflowService:
    return WorkflowService(SqlAlchemyWorkflowRepository(session))


def get_workflow_engine(session: AsyncSession = Depends(get_session)) -> WorkflowEngine:
    return WorkflowEngine(
        orchestrator=get_orchestrator_service(),
        repository=SqlAlchemyWorkflowInstanceRepository(session),
        executor=LlmStepExecutor(get_llm_provider()),
    )

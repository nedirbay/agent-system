from __future__ import annotations

import uuid

from app.core.exceptions import NotFoundError
from app.modules.workflows.domain.entities import Workflow
from app.modules.workflows.domain.repositories import WorkflowRepository
from app.modules.workflows.application.commands import CreateWorkflowCommand


class WorkflowService:
    """Application service orchestrating Workflow use cases."""

    def __init__(self, repository: WorkflowRepository) -> None:
        self._repo = repository

    async def create(self, command: CreateWorkflowCommand) -> Workflow:
        entity = Workflow(name=command.name, description=command.description, is_active=command.is_active)
        return await self._repo.add(entity)

    async def get(self, entity_id: uuid.UUID) -> Workflow:
        entity = await self._repo.get(entity_id)
        if entity is None:
            raise NotFoundError("Workflow not found")
        return entity

    async def list(self, *, limit: int = 100, offset: int = 0) -> list[Workflow]:
        return await self._repo.list(limit=limit, offset=offset)

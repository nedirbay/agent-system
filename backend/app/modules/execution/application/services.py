from __future__ import annotations

import uuid

from app.core.exceptions import NotFoundError
from app.modules.execution.domain.entities import ExecutionRun
from app.modules.execution.domain.repositories import ExecutionRunRepository
from app.modules.execution.application.commands import CreateExecutionRunCommand


class ExecutionRunService:
    """Application service orchestrating ExecutionRun use cases."""

    def __init__(self, repository: ExecutionRunRepository) -> None:
        self._repo = repository

    async def create(self, command: CreateExecutionRunCommand) -> ExecutionRun:
        entity = ExecutionRun(task_id=command.task_id, command=command.command, status=command.status, output=command.output)
        return await self._repo.add(entity)

    async def get(self, entity_id: uuid.UUID) -> ExecutionRun:
        entity = await self._repo.get(entity_id)
        if entity is None:
            raise NotFoundError("ExecutionRun not found")
        return entity

    async def list(self, *, limit: int = 100, offset: int = 0) -> list[ExecutionRun]:
        return await self._repo.list(limit=limit, offset=offset)

from __future__ import annotations

import uuid

from app.core.exceptions import NotFoundError
from app.modules.analysis.domain.entities import AnalysisJob
from app.modules.analysis.domain.repositories import AnalysisJobRepository
from app.modules.analysis.application.commands import CreateAnalysisJobCommand


class AnalysisJobService:
    """Application service orchestrating AnalysisJob use cases."""

    def __init__(self, repository: AnalysisJobRepository) -> None:
        self._repo = repository

    async def create(self, command: CreateAnalysisJobCommand) -> AnalysisJob:
        entity = AnalysisJob(task_id=command.task_id, kind=command.kind, status=command.status, result=command.result)
        return await self._repo.add(entity)

    async def get(self, entity_id: uuid.UUID) -> AnalysisJob:
        entity = await self._repo.get(entity_id)
        if entity is None:
            raise NotFoundError("AnalysisJob not found")
        return entity

    async def list(self, *, limit: int = 100, offset: int = 0) -> list[AnalysisJob]:
        return await self._repo.list(limit=limit, offset=offset)

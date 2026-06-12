from __future__ import annotations

import uuid

from app.core.exceptions import NotFoundError
from app.modules.reports.domain.entities import Report
from app.modules.reports.domain.repositories import ReportRepository
from app.modules.reports.application.commands import CreateReportCommand


class ReportService:
    """Application service orchestrating Report use cases."""

    def __init__(self, repository: ReportRepository) -> None:
        self._repo = repository

    async def create(self, command: CreateReportCommand) -> Report:
        entity = Report(user_id=command.user_id, task_id=command.task_id, name=command.name, format=command.format, storage_path=command.storage_path)
        return await self._repo.add(entity)

    async def get(self, entity_id: uuid.UUID) -> Report:
        entity = await self._repo.get(entity_id)
        if entity is None:
            raise NotFoundError("Report not found")
        return entity

    async def list(self, *, limit: int = 100, offset: int = 0) -> list[Report]:
        return await self._repo.list(limit=limit, offset=offset)

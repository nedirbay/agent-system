from __future__ import annotations

import uuid

from app.core.exceptions import NotFoundError
from app.modules.audit.domain.entities import AuditLog
from app.modules.audit.domain.repositories import AuditLogRepository
from app.modules.audit.application.commands import CreateAuditLogCommand


class AuditLogService:
    """Application service orchestrating AuditLog use cases."""

    def __init__(self, repository: AuditLogRepository) -> None:
        self._repo = repository

    async def create(self, command: CreateAuditLogCommand) -> AuditLog:
        entity = AuditLog(user_id=command.user_id, entity_type=command.entity_type, entity_id=command.entity_id, action=command.action, details=command.details)
        return await self._repo.add(entity)

    async def get(self, entity_id: uuid.UUID) -> AuditLog:
        entity = await self._repo.get(entity_id)
        if entity is None:
            raise NotFoundError("AuditLog not found")
        return entity

    async def list(self, *, limit: int = 100, offset: int = 0) -> list[AuditLog]:
        return await self._repo.list(limit=limit, offset=offset)

from __future__ import annotations

import uuid
from abc import ABC, abstractmethod

from app.shared.domain.repository import AbstractRepository
from app.modules.audit.domain.entities import AuditLog


class AuditLogRepository(AbstractRepository[AuditLog], ABC):
    """Persistence port for AuditLog aggregates (append-only, AUD-001/004)."""

    @abstractmethod
    async def latest(self) -> AuditLog | None:
        """The most recently created entry — the tail of the hash chain."""

    @abstractmethod
    async def list_filtered(
        self,
        *,
        user_id: uuid.UUID | None = None,
        entity_type: str | None = None,
        action: str | None = None,
        limit: int = 100,
        offset: int = 0,
    ) -> list[AuditLog]:
        """Query the trail by actor / entity / action (full audit capability)."""

    @abstractmethod
    async def list_chain(self) -> list[AuditLog]:
        """All entries in insertion (chain) order — for integrity verification."""

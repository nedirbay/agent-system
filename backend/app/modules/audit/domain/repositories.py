from __future__ import annotations

from abc import ABC

from app.shared.domain.repository import AbstractRepository
from app.modules.audit.domain.entities import AuditLog


class AuditLogRepository(AbstractRepository[AuditLog], ABC):
    """Persistence port for AuditLog aggregates."""

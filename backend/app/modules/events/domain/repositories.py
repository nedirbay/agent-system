from __future__ import annotations

from abc import ABC

from app.shared.domain.repository import AbstractRepository
from app.modules.events.domain.entities import SystemEvent


class SystemEventRepository(AbstractRepository[SystemEvent], ABC):
    """Persistence port for SystemEvent aggregates."""

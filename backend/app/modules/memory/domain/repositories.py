from __future__ import annotations

from abc import ABC

from app.shared.domain.repository import AbstractRepository
from app.modules.memory.domain.entities import MemoryItem


class MemoryItemRepository(AbstractRepository[MemoryItem], ABC):
    """Persistence port for MemoryItem aggregates."""

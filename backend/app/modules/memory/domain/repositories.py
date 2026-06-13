from __future__ import annotations

import uuid
from abc import ABC, abstractmethod

from app.shared.domain.repository import AbstractRepository
from app.modules.memory.domain.entities import MemoryItem, MemoryReference


class MemoryItemRepository(AbstractRepository[MemoryItem], ABC):
    """Persistence port for MemoryItem aggregates."""

    @abstractmethod
    async def list_recent(
        self, *, memory_type: str | None = None, limit: int = 20
    ) -> list[MemoryItem]:
        """Most recently created memories, optionally filtered by type."""


class MemoryReferenceRepository(AbstractRepository[MemoryReference], ABC):
    """Persistence port for MemoryReference links (MEMORY_REFERENCES)."""

    @abstractmethod
    async def list_for_memory(self, memory_id: uuid.UUID) -> list[MemoryReference]:
        """Return all references attached to a memory."""

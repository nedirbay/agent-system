"""Memory vector index port (Roadmap Task 19 / AG-009 "Long-Term Memory").

Long-term memories are embedded and stored so they can be recalled by semantic
similarity, not just chronology. This mirrors the knowledge layer's VectorStore
but keys on `memory_id` and lives in its own collection (one collection = one
model/dim, EM-002). Abstracted so the application layer never touches Qdrant.
"""
from __future__ import annotations

import uuid
from abc import ABC, abstractmethod
from dataclasses import dataclass, field


@dataclass
class MemoryVectorHit:
    memory_id: uuid.UUID
    score: float
    payload: dict = field(default_factory=dict)


class MemoryVectorIndex(ABC):
    @abstractmethod
    async def ensure(self, *, dimension: int) -> None:
        """Create the collection if absent, sized to the embedding dimension."""

    @abstractmethod
    async def upsert(
        self, memory_id: uuid.UUID, vector: list[float], payload: dict
    ) -> None:
        """Insert or replace a memory's vector."""

    @abstractmethod
    async def search(
        self,
        vector: list[float],
        *,
        top_k: int = 5,
        memory_type: str | None = None,
    ) -> list[MemoryVectorHit]:
        """Return the nearest memories, optionally filtered by type."""

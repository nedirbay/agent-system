"""Vector store port (Roadmap Task 10 / RT-001..RT-002).

Abstracts the vector database (Qdrant) behind upsert/search so the knowledge
layer never depends on a concrete client.
"""
from __future__ import annotations

import uuid
from abc import ABC, abstractmethod
from dataclasses import dataclass, field


@dataclass
class VectorPoint:
    """A vector plus the payload kept for citation/filtering (CH-003 / RT-002)."""

    id: uuid.UUID
    vector: list[float]
    payload: dict


@dataclass
class SearchHit:
    id: uuid.UUID
    score: float
    payload: dict = field(default_factory=dict)


class VectorStore(ABC):
    @abstractmethod
    async def ensure_collection(self, *, dimension: int) -> None:
        """Create the collection if absent, sized to the embedding dimension."""

    @abstractmethod
    async def upsert(self, points: list[VectorPoint]) -> None:
        """Insert or replace vectors."""

    @abstractmethod
    async def search(
        self,
        vector: list[float],
        *,
        limit: int = 20,
        document_id: uuid.UUID | None = None,
    ) -> list[SearchHit]:
        """Return the nearest points, optionally filtered to one document."""

    @abstractmethod
    async def delete_for_document(self, document_id: uuid.UUID) -> None:
        """Remove every point belonging to a document (re-index support)."""

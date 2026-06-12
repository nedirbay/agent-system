"""Embedding provider port (Roadmap Task 9 / EM-001..EM-004).

No agent or service talks to a vendor embedding SDK directly; everything goes
through this interface so the model is a configuration choice (AIR-006). A
collection may hold vectors from exactly one model/dimension (EM-002).
"""
from __future__ import annotations

from abc import ABC, abstractmethod


class EmbeddingProvider(ABC):
    @property
    @abstractmethod
    def model_name(self) -> str:
        """Identifier of the embedding model (pinned per deployment)."""

    @property
    @abstractmethod
    def dimension(self) -> int:
        """Vector dimension produced by this model."""

    @abstractmethod
    async def embed(self, texts: list[str]) -> list[list[float]]:
        """Return one vector per input text, in the same order."""

    async def embed_one(self, text: str) -> list[float]:
        vectors = await self.embed([text])
        return vectors[0]

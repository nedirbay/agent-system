"""Long-term memory service (Roadmap Task 19 / AG-009 "Long-Term Memory").

Persists durable memories of past tasks and recalls them by semantic similarity.
On `remember` a memory is stored in Postgres, its references recorded, and its
embedding upserted into the memory vector index. On `recall` the query is
embedded and matched against that index, with results re-ranked by similarity
weighted by importance.

Graceful degradation (FH-001): if the embedder or vector index is unavailable,
`remember` still persists the memory and `recall` falls back to the most recent
memories so the platform keeps working without the vector store.
"""
from __future__ import annotations

import uuid
from dataclasses import dataclass, field

from app.core.config import get_settings
from app.core.exceptions import AppError
from app.core.logging import get_logger
from app.modules.knowledge.domain.embedding import EmbeddingProvider
from app.modules.memory.domain.entities import MemoryItem, MemoryReference
from app.modules.memory.domain.memory_vector import MemoryVectorIndex
from app.modules.memory.domain.repositories import (
    MemoryItemRepository,
    MemoryReferenceRepository,
)

_logger = get_logger("memory.long_term")
_SNIPPET = 280


@dataclass(frozen=True)
class MemoryRef:
    related_entity_type: str
    related_entity_id: uuid.UUID | None = None


@dataclass(frozen=True)
class RecalledMemory:
    memory_id: uuid.UUID
    memory_type: str | None
    content: str
    importance_score: int | None
    score: float
    references: list[MemoryRef] = field(default_factory=list)


class LongTermMemoryService:
    def __init__(
        self,
        *,
        items: MemoryItemRepository,
        references: MemoryReferenceRepository,
        embedder: EmbeddingProvider,
        vectors: MemoryVectorIndex,
    ) -> None:
        self._items = items
        self._references = references
        self._embedder = embedder
        self._vectors = vectors

    async def remember(
        self,
        content: str,
        *,
        memory_type: str | None = None,
        importance_score: int | None = None,
        references: list[MemoryRef] | None = None,
    ) -> MemoryItem:
        if not (content or "").strip():
            raise AppError("content must not be empty")
        if importance_score is not None and not 0 <= importance_score <= 10:
            raise AppError("importance_score must be between 0 and 10")

        item = await self._items.add(
            MemoryItem(
                memory_type=memory_type,
                content=content.strip(),
                importance_score=importance_score,
            )
        )

        for ref in references or []:
            await self._references.add(
                MemoryReference(
                    memory_id=item.id,
                    related_entity_type=ref.related_entity_type,
                    related_entity_id=ref.related_entity_id,
                )
            )

        # Index for semantic recall; never fail the write if embedding is down.
        try:
            vector = await self._embedder.embed_one(item.content or "")
            await self._vectors.ensure(dimension=self._embedder.dimension)
            await self._vectors.upsert(
                item.id,
                vector,
                {
                    "memory_id": str(item.id),
                    "memory_type": item.memory_type,
                    "importance_score": item.importance_score,
                    "content": item.content,
                },
            )
        except Exception:  # pragma: no cover - infra failure path
            _logger.warning("memory.embed_failed", memory_id=str(item.id))

        return item

    async def recall(
        self,
        query: str,
        *,
        top_k: int | None = None,
        memory_type: str | None = None,
    ) -> list[RecalledMemory]:
        if not (query or "").strip():
            raise AppError("query must not be empty")
        top_k = top_k or get_settings().memory_recall_top_k

        try:
            vector = await self._embedder.embed_one(query)
            hits = await self._vectors.search(
                vector, top_k=top_k, memory_type=memory_type
            )
        except Exception:  # pragma: no cover - infra failure path
            _logger.warning("memory.recall_degraded")
            return await self._recent(memory_type=memory_type, limit=top_k)

        if not hits:
            return []

        recalled: list[RecalledMemory] = []
        for hit in hits:
            payload = hit.payload or {}
            importance = payload.get("importance_score")
            refs = await self._load_refs(hit.memory_id)
            recalled.append(
                RecalledMemory(
                    memory_id=hit.memory_id,
                    memory_type=payload.get("memory_type"),
                    content=_snippet(payload.get("content", "")),
                    importance_score=importance,
                    score=_weighted(hit.score, importance),
                    references=refs,
                )
            )
        recalled.sort(key=lambda r: r.score, reverse=True)
        return recalled

    async def _recent(
        self, *, memory_type: str | None, limit: int
    ) -> list[RecalledMemory]:
        items = await self._items.list_recent(memory_type=memory_type, limit=limit)
        return [
            RecalledMemory(
                memory_id=i.id,
                memory_type=i.memory_type,
                content=_snippet(i.content or ""),
                importance_score=i.importance_score,
                score=0.0,
                references=await self._load_refs(i.id),
            )
            for i in items
        ]

    async def _load_refs(self, memory_id: uuid.UUID) -> list[MemoryRef]:
        refs = await self._references.list_for_memory(memory_id)
        return [
            MemoryRef(
                related_entity_type=r.related_entity_type or "",
                related_entity_id=r.related_entity_id,
            )
            for r in refs
        ]


def _weighted(score: float, importance: int | None) -> float:
    """Boost similarity by importance (0-10) so vital memories surface first."""
    factor = 1.0 + (importance or 0) / 20.0  # up to +50%
    return round(score * factor, 6)


def _snippet(text: str) -> str:
    text = text.strip()
    if len(text) <= _SNIPPET:
        return text
    return text[: _SNIPPET - 1].rstrip() + "…"

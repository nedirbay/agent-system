"""Memory vector index adapters (Roadmap Task 19).

`QdrantMemoryVectorIndex` stores long-term memory vectors in their own Qdrant
collection, keyed by `memory_id` with a `memory_type` payload for filtered
recall. `InMemoryMemoryVectorIndex` is a cosine-similarity fallback used in
tests and when Qdrant is unavailable (graceful degradation, FH-001).
"""
from __future__ import annotations

import math
import uuid

from app.core.config import get_settings
from app.modules.memory.domain.memory_vector import MemoryVectorHit, MemoryVectorIndex


class QdrantMemoryVectorIndex(MemoryVectorIndex):
    def __init__(self, *, collection: str | None = None, url: str | None = None) -> None:
        from qdrant_client import AsyncQdrantClient

        settings = get_settings()
        self._collection = collection or settings.qdrant_memory_collection
        self._client = AsyncQdrantClient(url=url or settings.qdrant_url)

    async def ensure(self, *, dimension: int) -> None:
        from qdrant_client import models

        if await self._client.collection_exists(self._collection):
            return
        await self._client.create_collection(
            collection_name=self._collection,
            vectors_config=models.VectorParams(
                size=dimension, distance=models.Distance.COSINE
            ),
        )
        await self._client.create_payload_index(
            collection_name=self._collection,
            field_name="memory_type",
            field_schema=models.PayloadSchemaType.KEYWORD,
        )

    async def upsert(
        self, memory_id: uuid.UUID, vector: list[float], payload: dict
    ) -> None:
        from qdrant_client import models

        await self._client.upsert(
            collection_name=self._collection,
            points=[
                models.PointStruct(id=str(memory_id), vector=vector, payload=payload)
            ],
        )

    async def search(
        self,
        vector: list[float],
        *,
        top_k: int = 5,
        memory_type: str | None = None,
    ) -> list[MemoryVectorHit]:
        from qdrant_client import models

        query_filter = None
        if memory_type is not None:
            query_filter = models.Filter(
                must=[
                    models.FieldCondition(
                        key="memory_type",
                        match=models.MatchValue(value=memory_type),
                    )
                ]
            )
        response = await self._client.query_points(
            collection_name=self._collection,
            query=vector,
            limit=top_k,
            query_filter=query_filter,
            with_payload=True,
        )
        return [
            MemoryVectorHit(
                memory_id=uuid.UUID(str(p.id)),
                score=float(p.score),
                payload=p.payload or {},
            )
            for p in response.points
        ]


class InMemoryMemoryVectorIndex(MemoryVectorIndex):
    """Cosine-similarity index for tests / Qdrant-down fallback."""

    def __init__(self) -> None:
        self._points: dict[uuid.UUID, tuple[list[float], dict]] = {}

    async def ensure(self, *, dimension: int) -> None:
        return None

    async def upsert(
        self, memory_id: uuid.UUID, vector: list[float], payload: dict
    ) -> None:
        self._points[memory_id] = (vector, payload)

    async def search(
        self,
        vector: list[float],
        *,
        top_k: int = 5,
        memory_type: str | None = None,
    ) -> list[MemoryVectorHit]:
        hits: list[MemoryVectorHit] = []
        for mid, (vec, payload) in self._points.items():
            if memory_type is not None and payload.get("memory_type") != memory_type:
                continue
            hits.append(
                MemoryVectorHit(
                    memory_id=mid, score=_cosine(vector, vec), payload=payload
                )
            )
        hits.sort(key=lambda h: h.score, reverse=True)
        return hits[:top_k]


def _cosine(a: list[float], b: list[float]) -> float:
    if not a or not b or len(a) != len(b):
        return 0.0
    dot = sum(x * y for x, y in zip(a, b))
    na = math.sqrt(sum(x * x for x in a))
    nb = math.sqrt(sum(y * y for y in b))
    if na == 0 or nb == 0:
        return 0.0
    return dot / (na * nb)

"""Qdrant adapter for the VectorStore port (Roadmap Task 10).

Uses the async Qdrant client against the deployment's collection. Payload
filtering by `document_id` supports per-document retrieval (RT-002).
"""
from __future__ import annotations

import uuid

from qdrant_client import AsyncQdrantClient, models

from app.core.config import get_settings
from app.modules.knowledge.domain.vector_store import (
    SearchHit,
    VectorPoint,
    VectorStore,
)


class QdrantVectorStore(VectorStore):
    def __init__(self, *, collection: str | None = None, url: str | None = None) -> None:
        settings = get_settings()
        self._collection = collection or settings.qdrant_documents_collection
        self._client = AsyncQdrantClient(url=url or settings.qdrant_url)

    async def ensure_collection(self, *, dimension: int) -> None:
        if await self._client.collection_exists(self._collection):
            return
        await self._client.create_collection(
            collection_name=self._collection,
            vectors_config=models.VectorParams(
                size=dimension, distance=models.Distance.COSINE
            ),
        )
        # Index the document_id payload so filtered search stays fast (RT-002).
        await self._client.create_payload_index(
            collection_name=self._collection,
            field_name="document_id",
            field_schema=models.PayloadSchemaType.KEYWORD,
        )

    async def upsert(self, points: list[VectorPoint]) -> None:
        if not points:
            return
        await self._client.upsert(
            collection_name=self._collection,
            points=[
                models.PointStruct(id=str(p.id), vector=p.vector, payload=p.payload)
                for p in points
            ],
        )

    async def search(
        self,
        vector: list[float],
        *,
        limit: int = 20,
        document_id: uuid.UUID | None = None,
    ) -> list[SearchHit]:
        query_filter = None
        if document_id is not None:
            query_filter = models.Filter(
                must=[
                    models.FieldCondition(
                        key="document_id",
                        match=models.MatchValue(value=str(document_id)),
                    )
                ]
            )
        response = await self._client.query_points(
            collection_name=self._collection,
            query=vector,
            limit=limit,
            query_filter=query_filter,
            with_payload=True,
        )
        return [
            SearchHit(id=uuid.UUID(str(p.id)), score=float(p.score), payload=p.payload or {})
            for p in response.points
        ]

    async def delete_for_document(self, document_id: uuid.UUID) -> None:
        if not await self._client.collection_exists(self._collection):
            return
        await self._client.delete(
            collection_name=self._collection,
            points_selector=models.FilterSelector(
                filter=models.Filter(
                    must=[
                        models.FieldCondition(
                            key="document_id",
                            match=models.MatchValue(value=str(document_id)),
                        )
                    ]
                )
            ),
        )

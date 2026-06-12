"""Knowledge indexing & retrieval service (Roadmap Tasks 8–10).

Orchestrates the RAG ingestion pipeline:

    document text → chunk (Task 8) → embed (Task 9) → store in Qdrant (Task 10)

and the query side: embed the question, search the vector store, return cited
chunks. Re-indexing is idempotent — existing chunks/points for the document are
cleared first (EM-002 re-index support).
"""
from __future__ import annotations

import uuid

from app.core.config import get_settings
from app.core.exceptions import NotFoundError
from app.modules.knowledge.application.commands import (
    IndexResult,
    SearchQuery,
    SearchResultItem,
)
from app.modules.knowledge.domain.chunk import Chunker, ChunkRepository, DocumentChunk
from app.modules.knowledge.domain.embedding import EmbeddingProvider
from app.modules.knowledge.domain.source import DocumentSource
from app.modules.knowledge.domain.vector_store import VectorPoint, VectorStore


class KnowledgeIndexService:
    def __init__(
        self,
        *,
        source: DocumentSource,
        chunker: Chunker,
        chunks: ChunkRepository,
        embedder: EmbeddingProvider,
        vector_store: VectorStore,
    ) -> None:
        self._source = source
        self._chunker = chunker
        self._chunks = chunks
        self._embedder = embedder
        self._vectors = vector_store

    async def index_document(self, document_id: uuid.UUID) -> IndexResult:
        source = await self._source.get(document_id)
        if source is None:
            raise NotFoundError(
                "Document not found or has no extracted text — parse it first"
            )

        # Idempotent re-index: drop prior chunks/points for this document.
        await self._chunks.delete_for_document(document_id)
        await self._vectors.delete_for_document(document_id)

        drafts = self._chunker.split(source.text)
        if not drafts:
            return IndexResult(
                document_id=document_id,
                chunk_count=0,
                embedded_count=0,
                embedding_model=self._embedder.model_name,
                collection="",
            )

        vectors = await self._embedder.embed([d.content for d in drafts])

        chunks = [
            DocumentChunk(
                document_id=document_id,
                chunk_index=d.chunk_index,
                content=d.content,
                token_count=d.token_count,
                page=d.page,
                embedding_model=self._embedder.model_name,
                embedded=True,
            )
            for d in drafts
        ]
        saved = await self._chunks.add_many(chunks)

        await self._vectors.ensure_collection(dimension=self._embedder.dimension)
        points = [
            VectorPoint(
                id=chunk.id,
                vector=vector,
                payload={
                    "document_id": str(document_id),
                    "chunk_index": chunk.chunk_index,
                    "page": chunk.page,
                    "token_count": chunk.token_count,
                    "file_name": source.file_name,
                    "content": chunk.content,
                },
            )
            for chunk, vector in zip(saved, vectors)
        ]
        await self._vectors.upsert(points)

        return IndexResult(
            document_id=document_id,
            chunk_count=len(saved),
            embedded_count=len(points),
            embedding_model=self._embedder.model_name,
            collection=get_settings().qdrant_documents_collection,
        )

    async def search(self, query: SearchQuery) -> list[SearchResultItem]:
        vector = await self._embedder.embed_one(query.query)
        hits = await self._vectors.search(
            vector, limit=query.top_k, document_id=query.document_id
        )
        results: list[SearchResultItem] = []
        for hit in hits:
            payload = hit.payload or {}
            doc_raw = payload.get("document_id")
            results.append(
                SearchResultItem(
                    chunk_id=hit.id,
                    document_id=uuid.UUID(doc_raw) if doc_raw else None,
                    chunk_index=payload.get("chunk_index"),
                    score=hit.score,
                    page=payload.get("page"),
                    content=payload.get("content", ""),
                )
            )
        return results

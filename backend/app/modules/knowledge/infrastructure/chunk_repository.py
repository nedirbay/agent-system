from __future__ import annotations

import uuid

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.knowledge.domain.chunk import ChunkRepository, DocumentChunk
from app.modules.knowledge.infrastructure.chunk_model import DocumentChunkModel


def _to_entity(model: DocumentChunkModel) -> DocumentChunk:
    return DocumentChunk(
        id=model.id,
        created_at=model.created_at,
        document_id=model.document_id,
        chunk_index=model.chunk_index,
        content=model.content,
        token_count=model.token_count,
        page=model.page,
        embedding_model=model.embedding_model,
        embedded=model.embedded,
    )


class SqlAlchemyChunkRepository(ChunkRepository):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def add_many(self, chunks: list[DocumentChunk]) -> list[DocumentChunk]:
        models = [
            DocumentChunkModel(
                id=c.id,
                created_at=c.created_at,
                document_id=c.document_id,
                chunk_index=c.chunk_index,
                content=c.content,
                token_count=c.token_count,
                page=c.page,
                embedding_model=c.embedding_model,
                embedded=c.embedded,
            )
            for c in chunks
        ]
        self._session.add_all(models)
        await self._session.flush()
        return [_to_entity(m) for m in models]

    async def delete_for_document(self, document_id: uuid.UUID) -> int:
        result = await self._session.execute(
            delete(DocumentChunkModel).where(
                DocumentChunkModel.document_id == document_id
            )
        )
        await self._session.flush()
        return result.rowcount or 0

    async def list_for_document(self, document_id: uuid.UUID) -> list[DocumentChunk]:
        result = await self._session.execute(
            select(DocumentChunkModel)
            .where(DocumentChunkModel.document_id == document_id)
            .order_by(DocumentChunkModel.chunk_index)
        )
        return [_to_entity(m) for m in result.scalars().all()]

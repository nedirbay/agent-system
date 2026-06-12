from __future__ import annotations

import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.documents.domain.entities import Document
from app.modules.documents.domain.repositories import DocumentRepository
from app.modules.documents.infrastructure.models import DocumentModel


def _to_entity(model: DocumentModel) -> Document:
    return Document(
        id=model.id,
        created_at=model.created_at,
        user_id=model.user_id,
        file_name=model.file_name,
        mime_type=model.mime_type,
        size=model.size,
        storage_path=model.storage_path,
        status=model.status,
        extracted_text=model.extracted_text,
        page_count=model.page_count,
        doc_metadata=model.doc_metadata,
    )


class SqlAlchemyDocumentRepository(DocumentRepository):
    """SQLAlchemy adapter implementing the Document port."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def add(self, entity: Document) -> Document:
        model = DocumentModel(
            id=entity.id,
            created_at=entity.created_at,
            user_id=entity.user_id,
            file_name=entity.file_name,
            mime_type=entity.mime_type,
            size=entity.size,
            storage_path=entity.storage_path,
            status=entity.status,
            extracted_text=entity.extracted_text,
            page_count=entity.page_count,
            doc_metadata=entity.doc_metadata,
        )
        self._session.add(model)
        await self._session.flush()
        return _to_entity(model)

    async def update(self, entity: Document) -> Document:
        model = await self._session.get(DocumentModel, entity.id)
        if model is None:
            raise KeyError(entity.id)
        model.file_name = entity.file_name
        model.mime_type = entity.mime_type
        model.size = entity.size
        model.storage_path = entity.storage_path
        model.status = entity.status
        model.extracted_text = entity.extracted_text
        model.page_count = entity.page_count
        model.doc_metadata = entity.doc_metadata
        await self._session.flush()
        return _to_entity(model)

    async def get(self, entity_id: uuid.UUID) -> Document | None:
        model = await self._session.get(DocumentModel, entity_id)
        return _to_entity(model) if model else None

    async def list(self, *, limit: int = 100, offset: int = 0) -> list[Document]:
        result = await self._session.execute(
            select(DocumentModel).limit(limit).offset(offset)
        )
        return [_to_entity(m) for m in result.scalars().all()]

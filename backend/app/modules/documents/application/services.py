from __future__ import annotations

import uuid

from app.core.exceptions import NotFoundError
from app.modules.documents.domain.entities import Document
from app.modules.documents.domain.repositories import DocumentRepository
from app.modules.documents.application.commands import CreateDocumentCommand


class DocumentService:
    """Application service orchestrating Document use cases."""

    def __init__(self, repository: DocumentRepository) -> None:
        self._repo = repository

    async def create(self, command: CreateDocumentCommand) -> Document:
        entity = Document(user_id=command.user_id, file_name=command.file_name, mime_type=command.mime_type, size=command.size, storage_path=command.storage_path, status=command.status)
        return await self._repo.add(entity)

    async def get(self, entity_id: uuid.UUID) -> Document:
        entity = await self._repo.get(entity_id)
        if entity is None:
            raise NotFoundError("Document not found")
        return entity

    async def list(self, *, limit: int = 100, offset: int = 0) -> list[Document]:
        return await self._repo.list(limit=limit, offset=offset)

from __future__ import annotations

import uuid

from app.core.exceptions import AppError, NotFoundError
from app.modules.documents.domain.entities import Document
from app.modules.documents.domain.metadata import MetadataExtractor
from app.modules.documents.domain.parser import DocumentParser
from app.modules.documents.domain.repositories import DocumentRepository
from app.modules.documents.domain.storage import FileStorage
from app.modules.documents.application.commands import (
    CreateDocumentCommand,
    ParseOutcome,
    UploadDocumentCommand,
)


class DocumentService:
    """Application service orchestrating Document use cases."""

    def __init__(
        self,
        repository: DocumentRepository,
        storage: FileStorage | None = None,
        parser: DocumentParser | None = None,
        metadata: MetadataExtractor | None = None,
    ) -> None:
        self._repo = repository
        self._storage = storage
        self._parser = parser
        self._metadata = metadata

    async def create(self, command: CreateDocumentCommand) -> Document:
        entity = Document(user_id=command.user_id, file_name=command.file_name, mime_type=command.mime_type, size=command.size, storage_path=command.storage_path, status=command.status)
        return await self._repo.add(entity)

    async def upload(self, command: UploadDocumentCommand) -> Document:
        """Store the uploaded bytes in object storage, then persist a record."""
        storage = self._require_storage()
        await storage.ensure_ready()
        # Object key namespaced by a fresh UUID so identical filenames never collide.
        key = f"{uuid.uuid4()}/{command.file_name}"
        stored = await storage.upload(key, command.content, command.mime_type)
        entity = Document(
            user_id=command.user_id,
            file_name=command.file_name,
            mime_type=command.mime_type,
            size=stored.size,
            storage_path=key,
            status="uploaded",
        )
        return await self._repo.add(entity)

    async def get_download_url(self, entity_id: uuid.UUID, *, expires_seconds: int = 3600) -> str:
        """Return a presigned URL so the client downloads straight from object storage."""
        entity = await self.get(entity_id)
        if not entity.storage_path:
            raise NotFoundError("Document has no stored file")
        return await self._require_storage().presigned_get_url(
            entity.storage_path, expires_seconds=expires_seconds
        )

    async def parse(self, entity_id: uuid.UUID) -> ParseOutcome:
        """Download the stored file, extract its text, and persist the result."""
        storage = self._require_storage()
        parser = self._require_parser()
        entity = await self.get(entity_id)
        if not entity.storage_path:
            raise NotFoundError("Document has no stored file")

        data = await storage.download(entity.storage_path)
        parsed = await parser.parse(
            data=data, file_name=entity.file_name, mime_type=entity.mime_type
        )

        entity.extracted_text = parsed.text
        entity.page_count = parsed.page_count
        entity.status = "parsed"
        if self._metadata is not None:
            meta = await self._metadata.extract(
                data=data,
                text=parsed.text,
                file_name=entity.file_name,
                mime_type=entity.mime_type,
            )
            # Keep the parser's own findings (format, ocr) alongside the metadata.
            meta["parser"] = parsed.metadata
            entity.doc_metadata = meta
        saved = await self._repo.update(entity)
        return ParseOutcome(
            document=saved,
            char_count=len(parsed.text),
            ocr_used=bool(parsed.metadata.get("ocr")),
        )

    def _require_storage(self) -> FileStorage:
        if self._storage is None:
            raise AppError("File storage is not configured")
        return self._storage

    def _require_parser(self) -> DocumentParser:
        if self._parser is None:
            raise AppError("Document parser is not configured")
        return self._parser

    async def get(self, entity_id: uuid.UUID) -> Document:
        entity = await self._repo.get(entity_id)
        if entity is None:
            raise NotFoundError("Document not found")
        return entity

    async def list(self, *, limit: int = 100, offset: int = 0) -> list[Document]:
        return await self._repo.list(limit=limit, offset=offset)

"""DocumentSource adapter backed by the documents module repository."""
from __future__ import annotations

import uuid

from app.modules.documents.domain.repositories import DocumentRepository
from app.modules.knowledge.domain.source import DocumentSource, SourceText


class RepositoryDocumentSource(DocumentSource):
    def __init__(self, documents: DocumentRepository) -> None:
        self._documents = documents

    async def get(self, document_id: uuid.UUID) -> SourceText | None:
        doc = await self._documents.get(document_id)
        if doc is None or not doc.extracted_text:
            return None
        return SourceText(
            document_id=document_id,
            text=doc.extracted_text,
            file_name=doc.file_name,
            mime_type=doc.mime_type,
        )

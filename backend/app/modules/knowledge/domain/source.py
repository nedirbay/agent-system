"""Port for reading the source text a chunk pipeline indexes.

Decouples the knowledge layer from the documents module: the indexing service
asks for `(text, file_name, mime_type)` by id, and an infrastructure adapter
fulfils it from the documents repository.
"""
from __future__ import annotations

import uuid
from abc import ABC, abstractmethod
from dataclasses import dataclass


@dataclass
class SourceText:
    document_id: uuid.UUID
    text: str
    file_name: str | None = None
    mime_type: str | None = None


class DocumentSource(ABC):
    @abstractmethod
    async def get(self, document_id: uuid.UUID) -> SourceText | None:
        """Return the document's extracted text, or None if unknown/unparsed."""

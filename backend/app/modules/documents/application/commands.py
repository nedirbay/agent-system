from __future__ import annotations

import uuid
from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:  # pragma: no cover
    from app.modules.documents.domain.entities import Document


@dataclass
class CreateDocumentCommand:
    file_name: str
    user_id: uuid.UUID | None = None
    mime_type: str | None = None
    size: int | None = None
    storage_path: str | None = None
    status: str = "uploaded"


@dataclass
class UploadDocumentCommand:
    """Upload a binary file: persist the bytes in object storage + a DB record."""

    file_name: str
    content: bytes
    mime_type: str | None = None
    user_id: uuid.UUID | None = None


@dataclass
class ParseOutcome:
    """Result of a parse run, carrying the saved document plus run details."""

    document: "Document"  # noqa: F821 (forward ref, resolved at runtime via TYPE_CHECKING)
    char_count: int
    ocr_used: bool

from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict


class DocumentCreate(BaseModel):
    file_name: str
    user_id: uuid.UUID | None = None
    mime_type: str | None = None
    size: int | None = None
    storage_path: str | None = None
    status: str = "uploaded"


class DocumentRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    created_at: datetime
    user_id: uuid.UUID | None = None
    file_name: str | None = None
    mime_type: str | None = None
    size: int | None = None
    storage_path: str | None = None
    status: str | None = None
    page_count: int | None = None
    doc_metadata: dict | None = None


class DownloadUrlResponse(BaseModel):
    url: str
    expires_in: int


class ParseResult(BaseModel):
    """Outcome of a parse run — includes a preview of the extracted text."""

    id: uuid.UUID
    status: str | None = None
    page_count: int | None = None
    char_count: int
    ocr_used: bool
    doc_metadata: dict | None = None
    text_preview: str

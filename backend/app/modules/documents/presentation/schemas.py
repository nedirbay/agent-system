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

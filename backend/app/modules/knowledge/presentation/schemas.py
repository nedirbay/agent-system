from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict


class KnowledgeItemCreate(BaseModel):
    source_type: str | None = None
    source_id: uuid.UUID | None = None
    title: str | None = None
    content: str | None = None


class KnowledgeItemRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    created_at: datetime
    source_type: str | None = None
    source_id: uuid.UUID | None = None
    title: str | None = None
    content: str | None = None

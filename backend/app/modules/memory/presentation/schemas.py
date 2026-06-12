from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict


class MemoryItemCreate(BaseModel):
    memory_type: str | None = None
    content: str | None = None
    importance_score: int | None = None


class MemoryItemRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    created_at: datetime
    memory_type: str | None = None
    content: str | None = None
    importance_score: int | None = None

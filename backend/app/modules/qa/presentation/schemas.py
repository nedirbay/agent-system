from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict


class QaConversationCreate(BaseModel):
    user_id: uuid.UUID | None = None
    title: str | None = None


class QaConversationRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    created_at: datetime
    user_id: uuid.UUID | None = None
    title: str | None = None

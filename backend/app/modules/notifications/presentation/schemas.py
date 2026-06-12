from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict


class NotificationCreate(BaseModel):
    title: str
    user_id: uuid.UUID | None = None
    message: str | None = None
    is_read: bool = False


class NotificationRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    created_at: datetime
    user_id: uuid.UUID | None = None
    title: str | None = None
    message: str | None = None
    is_read: bool | None = None

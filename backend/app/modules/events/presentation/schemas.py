from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict


class SystemEventCreate(BaseModel):
    event_type: str
    task_id: uuid.UUID | None = None
    payload: dict | None = None
    status: str = "published"


class SystemEventRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    created_at: datetime
    event_type: str | None = None
    task_id: uuid.UUID | None = None
    payload: dict | None = None
    status: str | None = None

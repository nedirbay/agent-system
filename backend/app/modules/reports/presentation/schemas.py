from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict


class ReportCreate(BaseModel):
    name: str
    user_id: uuid.UUID | None = None
    task_id: uuid.UUID | None = None
    format: str | None = None
    storage_path: str | None = None


class ReportRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    created_at: datetime
    user_id: uuid.UUID | None = None
    task_id: uuid.UUID | None = None
    name: str | None = None
    format: str | None = None
    storage_path: str | None = None

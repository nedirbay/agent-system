from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict


class ExecutionRunCreate(BaseModel):
    task_id: uuid.UUID | None = None
    command: str | None = None
    status: str = "pending"
    output: str | None = None


class ExecutionRunRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    created_at: datetime
    task_id: uuid.UUID | None = None
    command: str | None = None
    status: str | None = None
    output: str | None = None

from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict


class AgentCreate(BaseModel):
    name: str
    type: str | None = None
    description: str | None = None
    is_active: bool = True


class AgentRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    created_at: datetime
    name: str | None = None
    type: str | None = None
    description: str | None = None
    is_active: bool | None = None

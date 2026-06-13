from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict


class AuditLogCreate(BaseModel):
    user_id: uuid.UUID | None = None
    actor_type: str | None = "user"
    entity_type: str | None = None
    entity_id: uuid.UUID | None = None
    action: str | None = None
    details: dict | None = None
    correlation_id: str | None = None


class SecurityEventRequest(BaseModel):
    event: str
    user_id: uuid.UUID | None = None
    details: dict | None = None
    correlation_id: str | None = None


class AuditLogRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    created_at: datetime
    user_id: uuid.UUID | None = None
    actor_type: str | None = None
    entity_type: str | None = None
    entity_id: uuid.UUID | None = None
    action: str | None = None
    details: dict | None = None
    correlation_id: str | None = None
    prev_hash: str | None = None
    entry_hash: str | None = None


class IntegrityReportRead(BaseModel):
    ok: bool
    count: int
    broken_at: int | None = None
    broken_id: uuid.UUID | None = None

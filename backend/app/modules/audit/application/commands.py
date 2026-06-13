from __future__ import annotations

import uuid
from dataclasses import dataclass


@dataclass
class CreateAuditLogCommand:
    user_id: uuid.UUID | None = None
    actor_type: str | None = "user"
    entity_type: str | None = None
    entity_id: uuid.UUID | None = None
    action: str | None = None
    details: dict | None = None
    correlation_id: str | None = None

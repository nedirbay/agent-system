from __future__ import annotations

import uuid
from dataclasses import dataclass


@dataclass
class CreateAuditLogCommand:
    user_id: uuid.UUID | None = None
    entity_type: str | None = None
    entity_id: uuid.UUID | None = None
    action: str | None = None
    details: dict | None = None

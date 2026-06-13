from __future__ import annotations

import uuid
from dataclasses import dataclass

from app.shared.domain.entity import BaseEntity


@dataclass
class AuditLog(BaseEntity):
    user_id: uuid.UUID | None = None
    actor_type: str | None = "user"  # user | agent | system (AUD-001)
    entity_type: str | None = None
    entity_id: uuid.UUID | None = None
    action: str | None = None
    details: dict | None = None
    correlation_id: str | None = None  # CC-002 cross-layer trace id
    # Tamper-evident hash chain (AUD-004): each entry hashes its content plus
    # the previous entry's hash, so any edit/removal breaks the chain.
    prev_hash: str | None = None
    entry_hash: str | None = None

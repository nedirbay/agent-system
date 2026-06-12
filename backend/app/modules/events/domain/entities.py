from __future__ import annotations

import uuid
from dataclasses import dataclass

from app.shared.domain.entity import BaseEntity


@dataclass
class SystemEvent(BaseEntity):
    event_type: str | None = None
    task_id: uuid.UUID | None = None
    payload: dict | None = None
    status: str | None = "published"

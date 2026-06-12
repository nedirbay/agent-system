from __future__ import annotations

import uuid
from dataclasses import dataclass


@dataclass
class CreateSystemEventCommand:
    event_type: str
    task_id: uuid.UUID | None = None
    payload: dict | None = None
    status: str = "published"

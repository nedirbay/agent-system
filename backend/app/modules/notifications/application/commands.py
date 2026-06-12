from __future__ import annotations

import uuid
from dataclasses import dataclass


@dataclass
class CreateNotificationCommand:
    title: str
    user_id: uuid.UUID | None = None
    message: str | None = None
    is_read: bool = False

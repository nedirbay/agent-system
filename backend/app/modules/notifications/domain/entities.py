from __future__ import annotations

import uuid
from dataclasses import dataclass

from app.shared.domain.entity import BaseEntity


@dataclass
class Notification(BaseEntity):
    user_id: uuid.UUID | None = None
    title: str | None = None
    message: str | None = None
    is_read: bool | None = False

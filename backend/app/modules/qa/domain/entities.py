from __future__ import annotations

import uuid
from dataclasses import dataclass

from app.shared.domain.entity import BaseEntity


@dataclass
class QaConversation(BaseEntity):
    user_id: uuid.UUID | None = None
    title: str | None = None

from __future__ import annotations

import uuid
from dataclasses import dataclass

from app.shared.domain.entity import BaseEntity


@dataclass
class Agent(BaseEntity):
    name: str | None = None
    type: str | None = None
    description: str | None = None
    is_active: bool | None = True

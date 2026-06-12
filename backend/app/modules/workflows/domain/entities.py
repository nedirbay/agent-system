from __future__ import annotations

import uuid
from dataclasses import dataclass

from app.shared.domain.entity import BaseEntity


@dataclass
class Workflow(BaseEntity):
    name: str | None = None
    description: str | None = None
    is_active: bool | None = True

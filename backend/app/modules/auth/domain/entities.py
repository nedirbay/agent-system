from __future__ import annotations

import uuid
from dataclasses import dataclass

from app.shared.domain.entity import BaseEntity


@dataclass
class User(BaseEntity):
    username: str | None = None
    email: str | None = None
    full_name: str | None = None
    password_hash: str | None = None
    status: str | None = "active"

from __future__ import annotations

import uuid
from dataclasses import dataclass


@dataclass
class CreateAgentCommand:
    name: str
    type: str | None = None
    description: str | None = None
    is_active: bool = True

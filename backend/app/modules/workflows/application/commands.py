from __future__ import annotations

import uuid
from dataclasses import dataclass


@dataclass
class CreateWorkflowCommand:
    name: str
    description: str | None = None
    is_active: bool = True

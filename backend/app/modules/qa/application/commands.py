from __future__ import annotations

import uuid
from dataclasses import dataclass


@dataclass
class CreateQaConversationCommand:
    user_id: uuid.UUID | None = None
    title: str | None = None

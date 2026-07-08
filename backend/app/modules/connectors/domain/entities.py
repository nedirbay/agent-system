from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from typing import Any

from app.shared.domain.entity import BaseEntity

# Connection lifecycle states.
STATUS_CONNECTED = "connected"
STATUS_ERROR = "error"
STATUS_DISABLED = "disabled"


@dataclass
class ConnectorConnection(BaseEntity):
    """A user's configured link to an external system.

    Secret credentials are held only as ``secret_ciphertext`` (Fernet-sealed);
    the plaintext never lives on the entity. ``secret_hint`` is a display-safe
    masked tail for the UI, and ``config`` holds non-secret values.
    """

    user_id: uuid.UUID | None = None
    connector_type: str = ""
    label: str = ""
    status: str = STATUS_CONNECTED
    config: dict[str, Any] = field(default_factory=dict)
    secret_ciphertext: str | None = None
    secret_hint: str | None = None

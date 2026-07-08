from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from typing import Any


@dataclass
class AddConnectorCommand:
    connector_type: str
    user_id: uuid.UUID | None = None
    label: str | None = None
    # Raw submitted values for the connector's fields (config + secrets mixed).
    values: dict[str, Any] = field(default_factory=dict)

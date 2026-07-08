from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any

from sqlalchemy import JSON, DateTime, String, Text, Uuid
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class ConnectorConnectionModel(Base):
    __tablename__ = "connector_connections"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )
    user_id: Mapped[uuid.UUID | None] = mapped_column(Uuid, nullable=True, index=True)
    connector_type: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    label: Mapped[str] = mapped_column(String(255), nullable=False)
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="connected")
    # Non-secret values only (e.g. email address, default channel).
    config: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False, default=dict)
    # Fernet-sealed JSON of the secret fields. NEVER stored in plaintext.
    secret_ciphertext: Mapped[str | None] = mapped_column(Text, nullable=True)
    # Display-safe masked tail of the primary secret (e.g. "••••b123").
    secret_hint: Mapped[str | None] = mapped_column(String(64), nullable=True)

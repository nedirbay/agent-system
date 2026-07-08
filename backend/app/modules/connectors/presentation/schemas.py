from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from app.modules.connectors.domain.catalog import ConnectorSpec
from app.modules.connectors.domain.entities import ConnectorConnection


# --- Catalogue ----------------------------------------------------------

class CredentialFieldRead(BaseModel):
    key: str
    label: str
    kind: str
    required: bool
    placeholder: str = ""
    help: str = ""


class ConnectorSpecRead(BaseModel):
    type: str
    name: str
    description: str
    category: str
    icon: str
    docs_url: str = ""
    fields: list[CredentialFieldRead] = Field(default_factory=list)

    @classmethod
    def from_spec(cls, spec: ConnectorSpec) -> "ConnectorSpecRead":
        return cls(
            type=spec.type,
            name=spec.name,
            description=spec.description,
            category=spec.category,
            icon=spec.icon,
            docs_url=spec.docs_url,
            fields=[
                CredentialFieldRead(
                    key=f.key,
                    label=f.label,
                    kind=f.kind,
                    required=f.required,
                    placeholder=f.placeholder,
                    help=f.help,
                )
                for f in spec.fields
            ],
        )


# --- Connections --------------------------------------------------------

class AddConnectorRequest(BaseModel):
    connector_type: str
    label: str | None = None
    # Raw field values keyed by CredentialField.key (config + secrets).
    values: dict[str, Any] = Field(default_factory=dict)


class ConnectorConnectionRead(BaseModel):
    """A stored connection. Carries only a masked hint — never the secret."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    created_at: datetime
    connector_type: str
    label: str
    status: str
    config: dict[str, Any] = Field(default_factory=dict)
    secret_hint: str | None = None
    has_secret: bool = False

    @classmethod
    def from_entity(cls, entity: ConnectorConnection) -> "ConnectorConnectionRead":
        return cls(
            id=entity.id,
            created_at=entity.created_at,
            connector_type=entity.connector_type,
            label=entity.label,
            status=entity.status,
            config=entity.config,
            secret_hint=entity.secret_hint,
            has_secret=bool(entity.secret_ciphertext),
        )

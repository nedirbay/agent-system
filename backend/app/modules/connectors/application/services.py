from __future__ import annotations

import json
import uuid

from app.core.crypto import encrypt_secret, mask_secret
from app.core.exceptions import AppError, ForbiddenError, NotFoundError
from app.modules.connectors.application.commands import AddConnectorCommand
from app.modules.connectors.domain.catalog import (
    CONNECTOR_CATALOG,
    ConnectorSpec,
    get_connector_spec,
)
from app.modules.connectors.domain.entities import (
    STATUS_CONNECTED,
    ConnectorConnection,
)
from app.modules.connectors.domain.repositories import ConnectorConnectionRepository


class ConnectorService:
    """Application service for the connector catalogue and user connections.

    Enforces the security boundary around credentials: secrets submitted to
    :meth:`add` are validated against the catalogue, sealed with Fernet, and the
    plaintext is dropped immediately. Nothing this service returns ever carries a
    decrypted secret — only a masked hint for display.
    """

    def __init__(self, repository: ConnectorConnectionRepository) -> None:
        self._repo = repository

    # --- Catalogue -------------------------------------------------------
    def list_catalog(self) -> list[ConnectorSpec]:
        return list(CONNECTOR_CATALOG.values())

    # --- Connections -----------------------------------------------------
    async def list_connections(
        self, user_id: uuid.UUID | None, *, limit: int = 100, offset: int = 0
    ) -> list[ConnectorConnection]:
        return await self._repo.list_by_user(user_id, limit=limit, offset=offset)

    async def add(self, command: AddConnectorCommand) -> ConnectorConnection:
        spec = get_connector_spec(command.connector_type)
        if spec is None:
            raise AppError(f"Unknown connector type '{command.connector_type}'")

        values = command.values or {}
        config: dict[str, object] = {}
        secrets: dict[str, str] = {}

        for fld in spec.fields:
            raw = values.get(fld.key)
            provided = raw is not None and str(raw).strip() != ""
            if not provided:
                if fld.required:
                    raise AppError(f"Missing required field '{fld.label}'")
                continue
            if fld.is_secret:
                secrets[fld.key] = str(raw)
            else:
                config[fld.key] = raw

        # Seal all secret fields together; keep only a masked hint for display.
        secret_ciphertext: str | None = None
        secret_hint: str | None = None
        if secrets:
            secret_ciphertext = encrypt_secret(json.dumps(secrets))
            primary = next(iter(spec.secret_fields), None)
            if primary is not None and primary.key in secrets:
                secret_hint = mask_secret(secrets[primary.key])

        entity = ConnectorConnection(
            user_id=command.user_id,
            connector_type=spec.type,
            label=(command.label or spec.name).strip() or spec.name,
            status=STATUS_CONNECTED,
            config=config,
            secret_ciphertext=secret_ciphertext,
            secret_hint=secret_hint,
        )
        return await self._repo.add(entity)

    async def delete(
        self, user_id: uuid.UUID | None, connection_id: uuid.UUID
    ) -> None:
        existing = await self._repo.get(connection_id)
        if existing is None:
            raise NotFoundError("Connection not found")
        if existing.user_id != user_id:
            raise ForbiddenError("This connection belongs to another user")
        await self._repo.delete(connection_id)

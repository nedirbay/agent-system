from __future__ import annotations

import json
import uuid

import pytest
from fastapi.testclient import TestClient

from app.core.crypto import decrypt_secret, encrypt_secret, mask_secret
from app.core.exceptions import AppError, ForbiddenError
from app.main import app
from app.modules.connectors.application.commands import AddConnectorCommand
from app.modules.connectors.application.services import ConnectorService
from app.modules.connectors.domain.entities import ConnectorConnection
from app.modules.connectors.domain.repositories import ConnectorConnectionRepository
from app.modules.connectors.presentation.schemas import ConnectorConnectionRead


class MemoryConnectorRepository(ConnectorConnectionRepository):
    def __init__(self) -> None:
        self.items: dict[uuid.UUID, ConnectorConnection] = {}

    async def add(self, entity: ConnectorConnection) -> ConnectorConnection:
        self.items[entity.id] = entity
        return entity

    async def get(self, entity_id: uuid.UUID) -> ConnectorConnection | None:
        return self.items.get(entity_id)

    async def list(self, *, limit: int = 100, offset: int = 0) -> list[ConnectorConnection]:
        return list(self.items.values())[offset : offset + limit]

    async def list_by_user(
        self, user_id: uuid.UUID | None, *, limit: int = 100, offset: int = 0
    ) -> list[ConnectorConnection]:
        rows = [c for c in self.items.values() if c.user_id == user_id]
        return rows[offset : offset + limit]

    async def delete(self, entity_id: uuid.UUID) -> bool:
        return self.items.pop(entity_id, None) is not None


# --- Encryption ---------------------------------------------------------

def test_secret_encryption_round_trip() -> None:
    secret = "xoxb-super-secret-token-9999"
    sealed = encrypt_secret(secret)
    assert sealed != secret  # not plaintext
    assert secret not in sealed  # ciphertext leaks nothing
    assert decrypt_secret(sealed) == secret


def test_mask_secret_reveals_only_tail() -> None:
    assert mask_secret("xoxb-abcd1234") == "••••1234"
    assert "abcd" not in mask_secret("xoxb-abcd1234")


# --- Catalogue endpoint -------------------------------------------------

def test_catalog_endpoint_lists_connectors() -> None:
    client = TestClient(app)
    res = client.get("/api/v1/connectors/catalog")
    assert res.status_code == 200
    types = {c["type"] for c in res.json()}
    assert {"slack", "gmail", "whatsapp"} <= types

    slack = next(c for c in res.json() if c["type"] == "slack")
    secret_fields = [f for f in slack["fields"] if f["kind"] == "secret"]
    assert any(f["key"] == "bot_token" for f in secret_fields)


# --- Service: add / validation / security -------------------------------

@pytest.mark.asyncio
async def test_add_seals_secret_and_never_exposes_plaintext() -> None:
    service = ConnectorService(MemoryConnectorRepository())
    token = "xoxb-1234567890-abcdef"

    conn = await service.add(
        AddConnectorCommand(
            connector_type="slack",
            user_id=uuid.uuid4(),
            label="Team Slack",
            values={"bot_token": token, "default_channel": "#ops"},
        )
    )

    # Secret is sealed, recoverable only via decryption.
    assert conn.secret_ciphertext is not None
    assert token not in conn.secret_ciphertext
    assert json.loads(decrypt_secret(conn.secret_ciphertext))["bot_token"] == token
    # Non-secret value kept in the clear; hint masked.
    assert conn.config == {"default_channel": "#ops"}
    assert conn.secret_hint == mask_secret(token)

    # The API projection exposes no plaintext, only a hint + flag.
    read = ConnectorConnectionRead.from_entity(conn)
    dumped = read.model_dump()
    assert dumped["has_secret"] is True
    assert "secret_ciphertext" not in dumped
    assert token not in read.model_dump_json()


@pytest.mark.asyncio
async def test_add_rejects_unknown_connector() -> None:
    service = ConnectorService(MemoryConnectorRepository())
    with pytest.raises(AppError):
        await service.add(AddConnectorCommand(connector_type="myspace", values={}))


@pytest.mark.asyncio
async def test_add_rejects_missing_required_field() -> None:
    service = ConnectorService(MemoryConnectorRepository())
    with pytest.raises(AppError):
        # Slack requires bot_token.
        await service.add(
            AddConnectorCommand(connector_type="slack", values={"default_channel": "#x"})
        )


@pytest.mark.asyncio
async def test_optional_secret_may_be_omitted() -> None:
    service = ConnectorService(MemoryConnectorRepository())
    # MCP api_key is optional.
    conn = await service.add(
        AddConnectorCommand(
            connector_type="mcp",
            values={"endpoint": "https://mcp.example.com/sse"},
        )
    )
    assert conn.secret_ciphertext is None
    assert conn.config == {"endpoint": "https://mcp.example.com/sse"}


@pytest.mark.asyncio
async def test_delete_forbids_other_users_connection() -> None:
    repo = MemoryConnectorRepository()
    service = ConnectorService(repo)
    owner = uuid.uuid4()
    conn = await service.add(
        AddConnectorCommand(
            connector_type="telegram",
            user_id=owner,
            values={"bot_token": "123:ABC"},
        )
    )
    with pytest.raises(ForbiddenError):
        await service.delete(uuid.uuid4(), conn.id)
    # Still present after a forbidden delete.
    assert await repo.get(conn.id) is not None

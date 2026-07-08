from __future__ import annotations

import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.connectors.domain.entities import ConnectorConnection
from app.modules.connectors.domain.repositories import ConnectorConnectionRepository
from app.modules.connectors.infrastructure.models import ConnectorConnectionModel


def _to_entity(model: ConnectorConnectionModel) -> ConnectorConnection:
    return ConnectorConnection(
        id=model.id,
        created_at=model.created_at,
        user_id=model.user_id,
        connector_type=model.connector_type,
        label=model.label,
        status=model.status,
        config=dict(model.config or {}),
        secret_ciphertext=model.secret_ciphertext,
        secret_hint=model.secret_hint,
    )


class SqlAlchemyConnectorConnectionRepository(ConnectorConnectionRepository):
    """SQLAlchemy adapter implementing the connector connection port."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def add(self, entity: ConnectorConnection) -> ConnectorConnection:
        model = ConnectorConnectionModel(
            id=entity.id,
            created_at=entity.created_at,
            user_id=entity.user_id,
            connector_type=entity.connector_type,
            label=entity.label,
            status=entity.status,
            config=entity.config,
            secret_ciphertext=entity.secret_ciphertext,
            secret_hint=entity.secret_hint,
        )
        self._session.add(model)
        await self._session.flush()
        return _to_entity(model)

    async def get(self, entity_id: uuid.UUID) -> ConnectorConnection | None:
        model = await self._session.get(ConnectorConnectionModel, entity_id)
        return _to_entity(model) if model else None

    async def list(self, *, limit: int = 100, offset: int = 0) -> list[ConnectorConnection]:
        result = await self._session.execute(
            select(ConnectorConnectionModel).limit(limit).offset(offset)
        )
        return [_to_entity(m) for m in result.scalars().all()]

    async def list_by_user(
        self, user_id: uuid.UUID | None, *, limit: int = 100, offset: int = 0
    ) -> list[ConnectorConnection]:
        stmt = select(ConnectorConnectionModel).where(
            ConnectorConnectionModel.user_id == user_id
        )
        result = await self._session.execute(stmt.limit(limit).offset(offset))
        return [_to_entity(m) for m in result.scalars().all()]

    async def delete(self, entity_id: uuid.UUID) -> bool:
        model = await self._session.get(ConnectorConnectionModel, entity_id)
        if model is None:
            return False
        await self._session.delete(model)
        await self._session.flush()
        return True

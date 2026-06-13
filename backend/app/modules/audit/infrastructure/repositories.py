from __future__ import annotations

import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.audit.domain.entities import AuditLog
from app.modules.audit.domain.repositories import AuditLogRepository
from app.modules.audit.infrastructure.models import AuditLogModel


def _to_entity(model: AuditLogModel) -> AuditLog:
    return AuditLog(
        id=model.id,
        created_at=model.created_at,
        user_id=model.user_id,
        actor_type=model.actor_type,
        entity_type=model.entity_type,
        entity_id=model.entity_id,
        action=model.action,
        details=model.details,
        correlation_id=model.correlation_id,
        prev_hash=model.prev_hash,
        entry_hash=model.entry_hash,
    )


class SqlAlchemyAuditLogRepository(AuditLogRepository):
    """SQLAlchemy adapter implementing the AuditLog port."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def add(self, entity: AuditLog) -> AuditLog:
        model = AuditLogModel(
            id=entity.id,
            created_at=entity.created_at,
            user_id=entity.user_id,
            actor_type=entity.actor_type,
            entity_type=entity.entity_type,
            entity_id=entity.entity_id,
            action=entity.action,
            details=entity.details,
            correlation_id=entity.correlation_id,
            prev_hash=entity.prev_hash,
            entry_hash=entity.entry_hash,
        )
        self._session.add(model)
        await self._session.flush()
        return _to_entity(model)

    async def get(self, entity_id: uuid.UUID) -> AuditLog | None:
        model = await self._session.get(AuditLogModel, entity_id)
        return _to_entity(model) if model else None

    async def list(self, *, limit: int = 100, offset: int = 0) -> list[AuditLog]:
        result = await self._session.execute(
            select(AuditLogModel)
            .order_by(AuditLogModel.created_at.desc())
            .limit(limit)
            .offset(offset)
        )
        return [_to_entity(m) for m in result.scalars().all()]

    async def latest(self) -> AuditLog | None:
        result = await self._session.execute(
            select(AuditLogModel).order_by(AuditLogModel.created_at.desc()).limit(1)
        )
        model = result.scalars().first()
        return _to_entity(model) if model else None

    async def list_filtered(
        self,
        *,
        user_id: uuid.UUID | None = None,
        entity_type: str | None = None,
        action: str | None = None,
        limit: int = 100,
        offset: int = 0,
    ) -> list[AuditLog]:
        statement = select(AuditLogModel)
        if user_id is not None:
            statement = statement.where(AuditLogModel.user_id == user_id)
        if entity_type is not None:
            statement = statement.where(AuditLogModel.entity_type == entity_type)
        if action is not None:
            statement = statement.where(AuditLogModel.action == action)
        statement = (
            statement.order_by(AuditLogModel.created_at.desc()).limit(limit).offset(offset)
        )
        result = await self._session.execute(statement)
        return [_to_entity(m) for m in result.scalars().all()]

    async def list_chain(self) -> list[AuditLog]:
        result = await self._session.execute(
            select(AuditLogModel).order_by(AuditLogModel.created_at.asc())
        )
        return [_to_entity(m) for m in result.scalars().all()]

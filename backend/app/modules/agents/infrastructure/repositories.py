from __future__ import annotations

import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.agents.domain.entities import Agent
from app.modules.agents.domain.repositories import AgentRepository
from app.modules.agents.infrastructure.models import AgentModel


def _to_entity(model: AgentModel) -> Agent:
    return Agent(
        id=model.id,
        created_at=model.created_at,
        name=model.name,
        type=model.type,
        description=model.description,
        is_active=model.is_active,
    )


class SqlAlchemyAgentRepository(AgentRepository):
    """SQLAlchemy adapter implementing the Agent port."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def add(self, entity: Agent) -> Agent:
        model = AgentModel(
            id=entity.id,
            created_at=entity.created_at,
            name=entity.name,
            type=entity.type,
            description=entity.description,
            is_active=entity.is_active,
        )
        self._session.add(model)
        await self._session.flush()
        return _to_entity(model)

    async def get(self, entity_id: uuid.UUID) -> Agent | None:
        model = await self._session.get(AgentModel, entity_id)
        return _to_entity(model) if model else None

    async def list(self, *, limit: int = 100, offset: int = 0) -> list[Agent]:
        result = await self._session.execute(
            select(AgentModel).limit(limit).offset(offset)
        )
        return [_to_entity(m) for m in result.scalars().all()]

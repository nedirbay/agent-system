from __future__ import annotations

import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.workflows.domain.entities import Workflow
from app.modules.workflows.domain.repositories import WorkflowRepository
from app.modules.workflows.infrastructure.models import WorkflowModel


def _to_entity(model: WorkflowModel) -> Workflow:
    return Workflow(
        id=model.id,
        created_at=model.created_at,
        name=model.name,
        description=model.description,
        is_active=model.is_active,
    )


class SqlAlchemyWorkflowRepository(WorkflowRepository):
    """SQLAlchemy adapter implementing the Workflow port."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def add(self, entity: Workflow) -> Workflow:
        model = WorkflowModel(
            id=entity.id,
            created_at=entity.created_at,
            name=entity.name,
            description=entity.description,
            is_active=entity.is_active,
        )
        self._session.add(model)
        await self._session.flush()
        return _to_entity(model)

    async def get(self, entity_id: uuid.UUID) -> Workflow | None:
        model = await self._session.get(WorkflowModel, entity_id)
        return _to_entity(model) if model else None

    async def list(self, *, limit: int = 100, offset: int = 0) -> list[Workflow]:
        result = await self._session.execute(
            select(WorkflowModel).limit(limit).offset(offset)
        )
        return [_to_entity(m) for m in result.scalars().all()]

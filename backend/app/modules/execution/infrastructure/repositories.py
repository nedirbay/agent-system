from __future__ import annotations

import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.execution.domain.entities import ExecutionRun
from app.modules.execution.domain.repositories import ExecutionRunRepository
from app.modules.execution.infrastructure.models import ExecutionRunModel


def _to_entity(model: ExecutionRunModel) -> ExecutionRun:
    return ExecutionRun(
        id=model.id,
        created_at=model.created_at,
        task_id=model.task_id,
        command=model.command,
        status=model.status,
        output=model.output,
    )


class SqlAlchemyExecutionRunRepository(ExecutionRunRepository):
    """SQLAlchemy adapter implementing the ExecutionRun port."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def add(self, entity: ExecutionRun) -> ExecutionRun:
        model = ExecutionRunModel(
            id=entity.id,
            created_at=entity.created_at,
            task_id=entity.task_id,
            command=entity.command,
            status=entity.status,
            output=entity.output,
        )
        self._session.add(model)
        await self._session.flush()
        return _to_entity(model)

    async def get(self, entity_id: uuid.UUID) -> ExecutionRun | None:
        model = await self._session.get(ExecutionRunModel, entity_id)
        return _to_entity(model) if model else None

    async def list(self, *, limit: int = 100, offset: int = 0) -> list[ExecutionRun]:
        result = await self._session.execute(
            select(ExecutionRunModel).limit(limit).offset(offset)
        )
        return [_to_entity(m) for m in result.scalars().all()]

from __future__ import annotations

import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.analysis.domain.entities import AnalysisJob
from app.modules.analysis.domain.repositories import AnalysisJobRepository
from app.modules.analysis.infrastructure.models import AnalysisJobModel


def _to_entity(model: AnalysisJobModel) -> AnalysisJob:
    return AnalysisJob(
        id=model.id,
        created_at=model.created_at,
        task_id=model.task_id,
        kind=model.kind,
        status=model.status,
        result=model.result,
    )


class SqlAlchemyAnalysisJobRepository(AnalysisJobRepository):
    """SQLAlchemy adapter implementing the AnalysisJob port."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def add(self, entity: AnalysisJob) -> AnalysisJob:
        model = AnalysisJobModel(
            id=entity.id,
            created_at=entity.created_at,
            task_id=entity.task_id,
            kind=entity.kind,
            status=entity.status,
            result=entity.result,
        )
        self._session.add(model)
        await self._session.flush()
        return _to_entity(model)

    async def get(self, entity_id: uuid.UUID) -> AnalysisJob | None:
        model = await self._session.get(AnalysisJobModel, entity_id)
        return _to_entity(model) if model else None

    async def list(self, *, limit: int = 100, offset: int = 0) -> list[AnalysisJob]:
        result = await self._session.execute(
            select(AnalysisJobModel).limit(limit).offset(offset)
        )
        return [_to_entity(m) for m in result.scalars().all()]

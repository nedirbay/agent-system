from __future__ import annotations

import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.reports.domain.entities import Report
from app.modules.reports.domain.repositories import ReportRepository
from app.modules.reports.infrastructure.models import ReportModel


def _to_entity(model: ReportModel) -> Report:
    return Report(
        id=model.id,
        created_at=model.created_at,
        user_id=model.user_id,
        task_id=model.task_id,
        name=model.name,
        format=model.format,
        storage_path=model.storage_path,
        content=model.content,
    )


class SqlAlchemyReportRepository(ReportRepository):
    """SQLAlchemy adapter implementing the Report port."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def add(self, entity: Report) -> Report:
        model = ReportModel(
            id=entity.id,
            created_at=entity.created_at,
            user_id=entity.user_id,
            task_id=entity.task_id,
            name=entity.name,
            format=entity.format,
            storage_path=entity.storage_path,
            content=entity.content,
        )
        self._session.add(model)
        await self._session.flush()
        return _to_entity(model)

    async def get(self, entity_id: uuid.UUID) -> Report | None:
        model = await self._session.get(ReportModel, entity_id)
        return _to_entity(model) if model else None

    async def list(self, *, limit: int = 100, offset: int = 0) -> list[Report]:
        result = await self._session.execute(
            select(ReportModel).limit(limit).offset(offset)
        )
        return [_to_entity(m) for m in result.scalars().all()]

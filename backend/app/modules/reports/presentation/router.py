from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends

from app.modules.reports.application.commands import CreateReportCommand
from app.modules.reports.application.services import ReportService
from app.modules.reports.presentation.dependencies import get_report_service
from app.modules.reports.presentation.schemas import ReportCreate, ReportRead

router = APIRouter(prefix="/reports", tags=["Reports"])


@router.post("", response_model=ReportRead, status_code=201)
async def create_report(
    payload: ReportCreate,
    service: ReportService = Depends(get_report_service),
) -> ReportRead:
    command = CreateReportCommand(**payload.model_dump())
    entity = await service.create(command)
    return ReportRead.model_validate(entity)


@router.get("", response_model=list[ReportRead])
async def list_report(
    limit: int = 100,
    offset: int = 0,
    service: ReportService = Depends(get_report_service),
) -> list[ReportRead]:
    items = await service.list(limit=limit, offset=offset)
    return [ReportRead.model_validate(i) for i in items]


@router.get("/{item_id}", response_model=ReportRead)
async def get_report(
    item_id: uuid.UUID,
    service: ReportService = Depends(get_report_service),
) -> ReportRead:
    entity = await service.get(item_id)
    return ReportRead.model_validate(entity)

from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends

from app.modules.analysis.application.commands import CreateAnalysisJobCommand
from app.modules.analysis.application.services import AnalysisJobService
from app.modules.analysis.presentation.dependencies import get_analysisjob_service
from app.modules.analysis.presentation.schemas import AnalysisJobCreate, AnalysisJobRead

router = APIRouter(prefix="/analysis", tags=["Analysis"])


@router.post("", response_model=AnalysisJobRead, status_code=201)
async def create_analysisjob(
    payload: AnalysisJobCreate,
    service: AnalysisJobService = Depends(get_analysisjob_service),
) -> AnalysisJobRead:
    command = CreateAnalysisJobCommand(**payload.model_dump())
    entity = await service.create(command)
    return AnalysisJobRead.model_validate(entity)


@router.get("", response_model=list[AnalysisJobRead])
async def list_analysisjob(
    limit: int = 100,
    offset: int = 0,
    service: AnalysisJobService = Depends(get_analysisjob_service),
) -> list[AnalysisJobRead]:
    items = await service.list(limit=limit, offset=offset)
    return [AnalysisJobRead.model_validate(i) for i in items]


@router.get("/{item_id}", response_model=AnalysisJobRead)
async def get_analysisjob(
    item_id: uuid.UUID,
    service: AnalysisJobService = Depends(get_analysisjob_service),
) -> AnalysisJobRead:
    entity = await service.get(item_id)
    return AnalysisJobRead.model_validate(entity)

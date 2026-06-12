from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends

from app.modules.audit.application.commands import CreateAuditLogCommand
from app.modules.audit.application.services import AuditLogService
from app.modules.audit.presentation.dependencies import get_auditlog_service
from app.modules.audit.presentation.schemas import AuditLogCreate, AuditLogRead

router = APIRouter(prefix="/audit", tags=["Audit"])


@router.post("", response_model=AuditLogRead, status_code=201)
async def create_auditlog(
    payload: AuditLogCreate,
    service: AuditLogService = Depends(get_auditlog_service),
) -> AuditLogRead:
    command = CreateAuditLogCommand(**payload.model_dump())
    entity = await service.create(command)
    return AuditLogRead.model_validate(entity)


@router.get("", response_model=list[AuditLogRead])
async def list_auditlog(
    limit: int = 100,
    offset: int = 0,
    service: AuditLogService = Depends(get_auditlog_service),
) -> list[AuditLogRead]:
    items = await service.list(limit=limit, offset=offset)
    return [AuditLogRead.model_validate(i) for i in items]


@router.get("/{item_id}", response_model=AuditLogRead)
async def get_auditlog(
    item_id: uuid.UUID,
    service: AuditLogService = Depends(get_auditlog_service),
) -> AuditLogRead:
    entity = await service.get(item_id)
    return AuditLogRead.model_validate(entity)

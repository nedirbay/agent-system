from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends

from app.modules.audit.application.commands import CreateAuditLogCommand
from app.modules.audit.application.services import AuditLogService
from app.modules.audit.presentation.dependencies import get_auditlog_service
from app.modules.audit.presentation.schemas import (
    AuditLogCreate,
    AuditLogRead,
    IntegrityReportRead,
    SecurityEventRequest,
)

router = APIRouter(prefix="/audit", tags=["Audit"])


@router.post("", response_model=AuditLogRead, status_code=201)
async def create_auditlog(
    payload: AuditLogCreate,
    service: AuditLogService = Depends(get_auditlog_service),
) -> AuditLogRead:
    command = CreateAuditLogCommand(**payload.model_dump())
    entity = await service.create(command)
    return AuditLogRead.model_validate(entity)


@router.post("/security-events", response_model=AuditLogRead, status_code=201)
async def record_security_event(
    payload: SecurityEventRequest,
    service: AuditLogService = Depends(get_auditlog_service),
) -> AuditLogRead:
    """Record a security-relevant event in the trail (AUD-002)."""
    entity = await service.record_security_event(
        payload.event,
        user_id=payload.user_id,
        details=payload.details,
        correlation_id=payload.correlation_id,
    )
    return AuditLogRead.model_validate(entity)


@router.get("/verify", response_model=IntegrityReportRead)
async def verify_integrity(
    service: AuditLogService = Depends(get_auditlog_service),
) -> IntegrityReportRead:
    """Verify the audit hash chain — detects tampering or deletions (AUD-004)."""
    report = await service.verify_integrity()
    return IntegrityReportRead(
        ok=report.ok,
        count=report.count,
        broken_at=report.broken_at,
        broken_id=report.broken_id,
    )


@router.get("", response_model=list[AuditLogRead])
async def list_auditlog(
    user_id: uuid.UUID | None = None,
    entity_type: str | None = None,
    action: str | None = None,
    limit: int = 100,
    offset: int = 0,
    service: AuditLogService = Depends(get_auditlog_service),
) -> list[AuditLogRead]:
    items = await service.query(
        user_id=user_id,
        entity_type=entity_type,
        action=action,
        limit=limit,
        offset=offset,
    )
    return [AuditLogRead.model_validate(i) for i in items]


@router.get("/{item_id}", response_model=AuditLogRead)
async def get_auditlog(
    item_id: uuid.UUID,
    service: AuditLogService = Depends(get_auditlog_service),
) -> AuditLogRead:
    entity = await service.get(item_id)
    return AuditLogRead.model_validate(entity)

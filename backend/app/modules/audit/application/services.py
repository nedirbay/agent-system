from __future__ import annotations

import hashlib
import json
import uuid
from dataclasses import dataclass

from app.core.exceptions import AppError, NotFoundError
from app.core.logging import LogCategory, get_category_logger
from app.modules.audit.application.commands import CreateAuditLogCommand
from app.modules.audit.domain.entities import AuditLog
from app.modules.audit.domain.repositories import AuditLogRepository

_audit_log = get_category_logger(LogCategory.AUDIT)
_security_log = get_category_logger(LogCategory.SECURITY)

# Canonical security events flowing through the trail (AUD-002).
SECURITY_EVENTS = frozenset(
    {
        "LoginSuccess",
        "LoginFailed",
        "PermissionDenied",
        "ApprovalGranted",
        "ApprovalDenied",
        "SandboxViolation",
    }
)


def _compute_hash(entity: AuditLog, prev_hash: str | None) -> str:
    """Deterministic SHA-256 over the entry's content + the previous hash."""
    payload = {
        "prev": prev_hash or "",
        "created_at": entity.created_at.isoformat(),
        "user_id": str(entity.user_id) if entity.user_id else None,
        "actor_type": entity.actor_type,
        "entity_type": entity.entity_type,
        "entity_id": str(entity.entity_id) if entity.entity_id else None,
        "action": entity.action,
        "details": entity.details,
        "correlation_id": entity.correlation_id,
    }
    blob = json.dumps(payload, sort_keys=True, default=str, separators=(",", ":"))
    return hashlib.sha256(blob.encode("utf-8")).hexdigest()


@dataclass(frozen=True)
class IntegrityReport:
    ok: bool
    count: int
    broken_at: int | None = None
    broken_id: uuid.UUID | None = None


class AuditLogService:
    """Append-only, tamper-evident audit trail (FR-014 / AUD-001..004)."""

    def __init__(self, repository: AuditLogRepository) -> None:
        self._repo = repository

    async def record(
        self,
        *,
        action: str,
        user_id: uuid.UUID | None = None,
        actor_type: str = "user",
        entity_type: str | None = None,
        entity_id: uuid.UUID | None = None,
        details: dict | None = None,
        correlation_id: str | None = None,
    ) -> AuditLog:
        if not action or not action.strip():
            raise AppError("An audit entry requires an action")

        prev = await self._repo.latest()
        prev_hash = prev.entry_hash if prev else None
        entry = AuditLog(
            action=action,
            user_id=user_id,
            actor_type=actor_type,
            entity_type=entity_type,
            entity_id=entity_id,
            details=details,
            correlation_id=correlation_id,
            prev_hash=prev_hash,
        )
        entry.entry_hash = _compute_hash(entry, prev_hash)
        stored = await self._repo.add(entry)
        _audit_log.info(
            "audit.recorded",
            action=action,
            entity_type=entity_type,
            actor_type=actor_type,
            audit_id=str(stored.id),
        )
        return stored

    async def record_security_event(
        self,
        event: str,
        *,
        user_id: uuid.UUID | None = None,
        details: dict | None = None,
        correlation_id: str | None = None,
    ) -> AuditLog:
        """Record a security-relevant event (AUD-002); also logs to the security category."""
        _security_log.info(
            "security.event",
            security_event=event,
            user_id=str(user_id) if user_id else None,
        )
        return await self.record(
            action=event,
            user_id=user_id,
            actor_type="system",
            entity_type="security",
            details=details,
            correlation_id=correlation_id,
        )

    async def create(self, command: CreateAuditLogCommand) -> AuditLog:
        """CRUD entrypoint — routed through `record` so the hash chain stays intact."""
        return await self.record(
            action=command.action or "unspecified",
            user_id=command.user_id,
            actor_type=command.actor_type or "user",
            entity_type=command.entity_type,
            entity_id=command.entity_id,
            details=command.details,
            correlation_id=command.correlation_id,
        )

    async def get(self, entity_id: uuid.UUID) -> AuditLog:
        entity = await self._repo.get(entity_id)
        if entity is None:
            raise NotFoundError("AuditLog not found")
        return entity

    async def list(self, *, limit: int = 100, offset: int = 0) -> list[AuditLog]:
        return await self._repo.list(limit=limit, offset=offset)

    async def query(
        self,
        *,
        user_id: uuid.UUID | None = None,
        entity_type: str | None = None,
        action: str | None = None,
        limit: int = 100,
        offset: int = 0,
    ) -> list[AuditLog]:
        return await self._repo.list_filtered(
            user_id=user_id,
            entity_type=entity_type,
            action=action,
            limit=limit,
            offset=offset,
        )

    async def verify_integrity(self) -> IntegrityReport:
        """Walk the chain, recomputing hashes; report the first tampered entry (AUD-004)."""
        chain = await self._repo.list_chain()
        prev_hash: str | None = None
        for index, entry in enumerate(chain):
            expected = _compute_hash(entry, prev_hash)
            if entry.prev_hash != prev_hash or entry.entry_hash != expected:
                return IntegrityReport(
                    ok=False, count=len(chain), broken_at=index, broken_id=entry.id
                )
            prev_hash = entry.entry_hash
        return IntegrityReport(ok=True, count=len(chain))

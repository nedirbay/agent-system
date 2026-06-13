from __future__ import annotations

import uuid

import pytest
from fastapi.testclient import TestClient

from app.core.exceptions import AppError
from app.core.metrics import MetricsRegistry, get_metrics
from app.main import app
from app.modules.audit.application.services import AuditLogService
from app.modules.audit.domain.entities import AuditLog
from app.modules.audit.domain.repositories import AuditLogRepository


# --------------------------------------------------------------------------- #
# Task 28 — Performance tracking (metrics registry)
# --------------------------------------------------------------------------- #


def test_metrics_registry_records_requests_and_rates() -> None:
    reg = MetricsRegistry()
    reg.record_request(0.010, 200)
    reg.record_request(0.020, 200)
    reg.record_request(0.030, 500)
    reg.record_request(0.040, 404)

    snap = reg.snapshot()
    assert snap["requests_total"] == 4
    assert snap["errors_total"] == 1  # one 5xx
    assert snap["client_errors_total"] == 1  # one 4xx
    assert snap["error_rate"] == 0.25
    assert snap["processing_time_ms"]["avg"] == 25.0
    assert snap["processing_time_ms"]["max"] == 40.0


def test_metrics_registry_counts_tasks_and_prometheus_text() -> None:
    reg = MetricsRegistry()
    reg.record_task("qa")
    reg.record_task("qa")
    reg.record_task("execution")

    snap = reg.snapshot()
    assert snap["tasks_total"] == 3
    assert snap["tasks_by_kind"] == {"qa": 2, "execution": 1}

    text = reg.prometheus_text(gauges={"active_users": 5})
    assert "http_requests_total" in text
    assert 'agent_tasks_total{kind="qa"} 2' in text
    assert "active_users 5.0" in text


def test_metrics_endpoint_through_middleware() -> None:
    # The ObservabilityMiddleware feeds the global registry on every request.
    get_metrics().reset()
    client = TestClient(app)

    r = client.get("/health")
    assert r.status_code == 200
    # Middleware echoes the correlation id back (CC-002).
    assert r.headers.get("X-Correlation-ID")

    snap = get_metrics().snapshot()
    assert snap["requests_total"] >= 1


# --------------------------------------------------------------------------- #
# Task 29 — Audit system (hash-chain integrity)
# --------------------------------------------------------------------------- #


class FakeAuditRepo(AuditLogRepository):
    def __init__(self) -> None:
        self.items: list[AuditLog] = []

    async def add(self, entity: AuditLog) -> AuditLog:
        self.items.append(entity)
        return entity

    async def get(self, entity_id: uuid.UUID) -> AuditLog | None:
        return next((i for i in self.items if i.id == entity_id), None)

    async def list(self, *, limit: int = 100, offset: int = 0) -> list[AuditLog]:
        return list(reversed(self.items))[offset : offset + limit]

    async def latest(self) -> AuditLog | None:
        return self.items[-1] if self.items else None

    async def list_filtered(
        self,
        *,
        user_id: uuid.UUID | None = None,
        entity_type: str | None = None,
        action: str | None = None,
        limit: int = 100,
        offset: int = 0,
    ) -> list[AuditLog]:
        out = self.items
        if user_id is not None:
            out = [i for i in out if i.user_id == user_id]
        if entity_type is not None:
            out = [i for i in out if i.entity_type == entity_type]
        if action is not None:
            out = [i for i in out if i.action == action]
        return list(reversed(out))[offset : offset + limit]

    async def list_chain(self) -> list[AuditLog]:
        return list(self.items)


@pytest.mark.asyncio
async def test_audit_record_builds_hash_chain() -> None:
    service = AuditLogService(FakeAuditRepo())

    first = await service.record(action="DocumentUploaded", entity_type="document")
    second = await service.record(action="DocumentParsed", entity_type="document")

    assert first.prev_hash is None
    assert first.entry_hash
    # Each link points at the previous entry's hash.
    assert second.prev_hash == first.entry_hash
    assert second.entry_hash != first.entry_hash


@pytest.mark.asyncio
async def test_audit_verify_detects_tampering() -> None:
    repo = FakeAuditRepo()
    service = AuditLogService(repo)
    await service.record(action="LoginSuccess", entity_type="security")
    await service.record(action="DocumentDeleted", entity_type="document")

    assert (await service.verify_integrity()).ok is True

    # Tamper with a stored entry's content without recomputing its hash.
    repo.items[0].action = "SomethingElse"
    report = await service.verify_integrity()
    assert report.ok is False
    assert report.broken_at == 0


@pytest.mark.asyncio
async def test_audit_security_event_and_query() -> None:
    service = AuditLogService(FakeAuditRepo())
    user = uuid.uuid4()

    await service.record_security_event("LoginFailed", user_id=user, details={"ip": "x"})
    await service.record(action="DocumentUploaded", entity_type="document")

    security = await service.query(entity_type="security")
    assert len(security) == 1
    assert security[0].action == "LoginFailed"
    assert security[0].actor_type == "system"


@pytest.mark.asyncio
async def test_audit_record_requires_action() -> None:
    service = AuditLogService(FakeAuditRepo())
    with pytest.raises(AppError):
        await service.record(action="   ")

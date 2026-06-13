from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from app.core import readiness
from app.core.security import create_access_token
from app.main import app

client = TestClient(app)


# --------------------------------------------------------------------------- #
# Task 30 — Security review (auth enforcement + hardening headers)
# --------------------------------------------------------------------------- #


def test_security_headers_present_on_every_response() -> None:
    r = client.get("/health")
    assert r.status_code == 200
    assert r.headers["x-content-type-options"] == "nosniff"
    assert r.headers["x-frame-options"] == "DENY"
    assert "referrer-policy" in r.headers
    assert "permissions-policy" in r.headers


def test_protected_endpoint_rejects_missing_or_invalid_token() -> None:
    assert client.get("/api/v1/auth/me").status_code == 401
    bad = client.get("/api/v1/auth/me", headers={"Authorization": "Bearer not-a-jwt"})
    assert bad.status_code == 401


def test_protected_endpoint_accepts_valid_token() -> None:
    token = create_access_token(subject="user-123", extra={"username": "alice"})
    r = client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["id"] == "user-123"
    assert body["username"] == "alice"


# --------------------------------------------------------------------------- #
# Task 31 — Scalability review (readiness probe)
# --------------------------------------------------------------------------- #


@pytest.mark.asyncio
async def test_readiness_ready_when_all_components_up(monkeypatch) -> None:
    async def ok() -> None:
        return None

    monkeypatch.setattr(
        readiness, "_CHECKS", {"database": ok, "redis": ok, "qdrant": ok}
    )
    result = await readiness.check_readiness(timeout=0.2)
    assert result["status"] == "ready"
    assert result["components"] == {"database": "up", "redis": "up", "qdrant": "up"}


@pytest.mark.asyncio
async def test_readiness_not_ready_when_database_down(monkeypatch) -> None:
    async def ok() -> None:
        return None

    async def fail() -> None:
        raise RuntimeError("connection refused")

    # DB is critical; Redis down alone stays ready, DB down flips to not_ready.
    monkeypatch.setattr(
        readiness, "_CHECKS", {"database": fail, "redis": ok, "qdrant": ok}
    )
    result = await readiness.check_readiness(timeout=0.2)
    assert result["status"] == "not_ready"
    assert result["components"]["database"] == "down"


@pytest.mark.asyncio
async def test_readiness_degrades_gracefully_when_noncritical_down(monkeypatch) -> None:
    async def ok() -> None:
        return None

    async def fail() -> None:
        raise RuntimeError("redis unavailable")

    monkeypatch.setattr(
        readiness, "_CHECKS", {"database": ok, "redis": fail, "qdrant": fail}
    )
    result = await readiness.check_readiness(timeout=0.2)
    # Redis/Qdrant are non-critical — node is still ready to serve (FH-001).
    assert result["status"] == "ready"
    assert result["components"]["redis"] == "down"


# --------------------------------------------------------------------------- #
# Task 32 — Final validation (full app composition smoke test)
# --------------------------------------------------------------------------- #


def test_all_module_routers_are_mounted() -> None:
    paths = {getattr(r, "path", "") for r in app.routes}
    expected = {
        "/health",
        "/health/ready",
        "/api/v1/auth/me",
        "/api/v1/documents",
        "/api/v1/knowledge",
        "/api/v1/qa/ask",
        "/api/v1/analysis/documents/analyze",
        "/api/v1/agents",
        "/api/v1/workflows",
        "/api/v1/memory/context",
        "/api/v1/execution/plan",
        "/api/v1/audit/verify",
        "/api/v1/monitoring/metrics",
    }
    missing = expected - paths
    assert not missing, f"unmounted routes: {missing}"


def test_openapi_schema_generates() -> None:
    schema = app.openapi()
    assert schema["info"]["title"]
    assert len(schema["paths"]) > 20


def test_error_envelope_shape() -> None:
    # AppError handler returns the documented { error: { code, message } } shape.
    r = client.get("/api/v1/auth/me")
    assert r.status_code == 401
    assert r.json()["error"]["code"] == "unauthorized"

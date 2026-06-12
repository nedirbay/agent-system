"""End-to-end smoke test exercising the clean-architecture chain
(domain -> application service -> repository -> ORM) against a throwaway
SQLite database. No external services required.
"""
import asyncio
import os
import tempfile

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

import app.core.registry  # noqa: F401  (register all ORM models on Base.metadata)
from app.core.database import Base, get_session
from app.main import app


@pytest.fixture(scope="module")
def client():
    # A temp file (not :memory:) so the schema is visible across connections/loops.
    fd, path = tempfile.mkstemp(suffix=".db")
    os.close(fd)
    url = f"sqlite+aiosqlite:///{path}"
    engine = create_async_engine(url)
    sessionmaker = async_sessionmaker(engine, expire_on_commit=False)

    async def _setup():
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        await engine.dispose()

    asyncio.run(_setup())

    async def _override():
        async with sessionmaker() as session:
            try:
                yield session
                await session.commit()
            except Exception:
                await session.rollback()
                raise

    app.dependency_overrides[get_session] = _override
    yield TestClient(app)
    app.dependency_overrides.clear()
    os.unlink(path)


def test_register_login_flow(client):
    r = client.post(
        "/api/v1/auth/register",
        json={"username": "alice", "email": "alice@acme.io",
              "password": "supersecret", "full_name": "Alice"},
    )
    assert r.status_code == 201, r.text
    assert "password_hash" not in r.json()  # hash is never exposed

    dup = client.post(
        "/api/v1/auth/register",
        json={"username": "alice", "email": "alice@acme.io", "password": "supersecret"},
    )
    assert dup.status_code == 409

    ok = client.post(
        "/api/v1/auth/login",
        json={"username": "alice", "password": "supersecret"},
    )
    assert ok.status_code == 200 and ok.json()["access_token"]

    bad = client.post(
        "/api/v1/auth/login",
        json={"username": "alice", "password": "wrong"},
    )
    assert bad.status_code == 401


def test_other_modules_crud(client):
    d = client.post("/api/v1/documents", json={"file_name": "report.pdf", "status": "uploaded"})
    assert d.status_code == 201 and d.json()["file_name"] == "report.pdf"
    assert len(client.get("/api/v1/documents").json()) >= 1

    a = client.post("/api/v1/agents", json={"name": "Orchestrator", "type": "orchestrator", "is_active": True})
    assert a.status_code == 201 and a.json()["is_active"] is True

"""Readiness probe (Faza 10 Task 31 / scalability & orchestration).

Liveness ("is the process up?") is the cheap `/health` endpoint. Readiness
("can it serve traffic?") probes the backing services a load balancer / k8s
needs healthy before routing requests here. Each check is time-boxed and
failures degrade gracefully: the database is treated as critical (its loss
makes the node not-ready), while Redis and Qdrant losses are reported but
non-fatal because the app degrades around them (FH-001).
"""
from __future__ import annotations

import asyncio

from sqlalchemy import text

from app.core.logging import get_logger

_logger = get_logger("readiness")


async def _check_database() -> None:
    from app.core.database import get_engine

    async with get_engine().connect() as conn:
        await conn.execute(text("SELECT 1"))


async def _check_redis() -> None:
    from app.core.clients import get_redis

    await get_redis().ping()


async def _check_qdrant() -> None:
    from app.core.clients import get_qdrant

    # qdrant-client is synchronous; run off the event loop.
    await asyncio.to_thread(get_qdrant().get_collections)


_CHECKS = {
    "database": _check_database,
    "redis": _check_redis,
    "qdrant": _check_qdrant,
}
_CRITICAL = {"database"}


async def check_readiness(*, timeout: float = 2.0) -> dict:
    components: dict[str, str] = {}
    for name, check in _CHECKS.items():
        try:
            await asyncio.wait_for(check(), timeout=timeout)
            components[name] = "up"
        except Exception:
            components[name] = "down"
            _logger.warning("readiness.component_down", component=name)

    ready = all(components[name] == "up" for name in _CRITICAL)
    return {"status": "ready" if ready else "not_ready", "components": components}

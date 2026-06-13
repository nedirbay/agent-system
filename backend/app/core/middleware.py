"""Observability middleware (Faza 9 Tasks 27/28 / CC-002).

Binds a per-request `correlation_id` (propagated via the `X-Correlation-ID`
header) into structlog's contextvars so every log line emitted while handling
the request carries it — satisfying the CC-002 cross-layer correlation goal.
It also times each request and feeds the metrics registry (Task 28) and emits
an application-category log line on completion (Task 27).

Implemented as a *pure ASGI* middleware rather than Starlette's
`BaseHTTPMiddleware`: the latter runs the downstream app in a separate task,
which both breaks contextvar propagation and trips asyncpg's "attached to a
different loop" guard. A pure ASGI middleware shares the request's task.
"""
from __future__ import annotations

import time
import uuid

import structlog

from app.core.config import get_settings
from app.core.logging import LogCategory, get_category_logger
from app.core.metrics import get_metrics

CORRELATION_HEADER = b"x-correlation-id"

# Baseline hardening headers (Faza 10 Task 30 / SEC-001 defense-in-depth).
_SECURITY_HEADERS: list[tuple[bytes, bytes]] = [
    (b"x-content-type-options", b"nosniff"),
    (b"x-frame-options", b"DENY"),
    (b"referrer-policy", b"strict-origin-when-cross-origin"),
    (b"permissions-policy", b"geolocation=(), microphone=(), camera=()"),
]


class SecurityHeadersMiddleware:
    """Attaches baseline security headers to every HTTP response (pure ASGI)."""

    def __init__(self, app) -> None:
        self.app = app
        # HSTS only outside local/dev, where TLS terminates upstream.
        self._hsts = get_settings().environment not in {"local", "test"}

    async def __call__(self, scope, receive, send) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        async def send_wrapper(message) -> None:
            if message["type"] == "http.response.start":
                message.setdefault("headers", [])
                message["headers"].extend(_SECURITY_HEADERS)
                if self._hsts:
                    message["headers"].append(
                        (b"strict-transport-security", b"max-age=31536000; includeSubDomains")
                    )
            await send(message)

        await self.app(scope, receive, send_wrapper)


class ObservabilityMiddleware:
    def __init__(self, app) -> None:
        self.app = app

    async def __call__(self, scope, receive, send) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        headers = dict(scope.get("headers") or [])
        raw_cid = headers.get(CORRELATION_HEADER)
        correlation_id = raw_cid.decode() if raw_cid else str(uuid.uuid4())

        structlog.contextvars.bind_contextvars(correlation_id=correlation_id)
        logger = get_category_logger(LogCategory.APPLICATION)
        start = time.perf_counter()
        status_holder = {"code": 500}

        async def send_wrapper(message) -> None:
            if message["type"] == "http.response.start":
                status_holder["code"] = message["status"]
                message.setdefault("headers", [])
                message["headers"].append(
                    (CORRELATION_HEADER, correlation_id.encode())
                )
            await send(message)

        try:
            await self.app(scope, receive, send_wrapper)
        except Exception:
            duration = time.perf_counter() - start
            get_metrics().record_request(duration, 500)
            logger.error(
                "request.failed",
                method=scope.get("method"),
                path=scope.get("path"),
                duration_ms=round(duration * 1000, 2),
            )
            structlog.contextvars.clear_contextvars()
            raise

        duration = time.perf_counter() - start
        get_metrics().record_request(duration, status_holder["code"])
        logger.info(
            "request.completed",
            method=scope.get("method"),
            path=scope.get("path"),
            status=status_holder["code"],
            duration_ms=round(duration * 1000, 2),
        )
        structlog.contextvars.clear_contextvars()

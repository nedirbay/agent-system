"""FastAPI application factory — wires configuration, middleware, exception
handlers, the model registry, and every module router into one app.
"""
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

import app.core.registry  # noqa: F401  (registers all ORM models on Base.metadata)
from app.api.router import api_router
from app.core.config import get_settings
from app.core.exceptions import register_exception_handlers
from app.core.logging import configure_logging, get_logger
from app.core.middleware import ObservabilityMiddleware, SecurityHeadersMiddleware
from app.core.readiness import check_readiness


@asynccontextmanager
async def lifespan(_: FastAPI):
    configure_logging()
    logger = get_logger("startup")
    settings = get_settings()
    logger.info("api.startup", environment=settings.environment)
    yield
    logger.info("api.shutdown")


def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(
        title=settings.app_name,
        version="0.1.0",
        debug=settings.debug,
        lifespan=lifespan,
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    # Correlation IDs + request metrics (Faza 9, Tasks 27/28). Added after CORS
    # so it runs inside the CORS layer for every request.
    app.add_middleware(ObservabilityMiddleware)
    # Baseline security headers on every response (Faza 10, Task 30).
    app.add_middleware(SecurityHeadersMiddleware)

    register_exception_handlers(app)
    app.include_router(api_router, prefix=settings.api_v1_prefix)

    @app.get("/health", tags=["System"])
    async def health() -> dict[str, str]:
        """Liveness probe — the process is up."""
        return {"status": "ok"}

    @app.get("/health/ready", tags=["System"])
    async def health_ready():
        """Readiness probe — backing services reachable (Task 31)."""
        result = await check_readiness()
        status_code = 200 if result["status"] == "ready" else 503
        return JSONResponse(status_code=status_code, content=result)

    @app.get("/", tags=["System"])
    async def root() -> dict[str, str]:
        return {"name": settings.app_name, "docs": "/docs"}

    return app


app = create_app()

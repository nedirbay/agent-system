"""Structured logging configuration (structlog)."""
import logging

import structlog

from app.core.config import get_settings


def configure_logging() -> None:
    settings = get_settings()
    logging.basicConfig(
        format="%(message)s",
        level=logging.DEBUG if settings.debug else logging.INFO,
    )
    structlog.configure(
        processors=[
            structlog.contextvars.merge_contextvars,
            structlog.processors.add_log_level,
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.StackInfoRenderer(),
            structlog.dev.ConsoleRenderer()
            if settings.debug
            else structlog.processors.JSONRenderer(),
        ],
        wrapper_class=structlog.make_filtering_bound_logger(logging.INFO),
        logger_factory=structlog.PrintLoggerFactory(),
        cache_logger_on_first_use=True,
    )


def get_logger(name: str | None = None) -> structlog.stdlib.BoundLogger:
    return structlog.get_logger(name)


class LogCategory:
    """The four log categories required by SYSTEM_REQUIREMENTS §11 (Task 27)."""

    APPLICATION = "application"
    SECURITY = "security"
    AGENT = "agent"
    AUDIT = "audit"


def get_category_logger(category: str) -> structlog.stdlib.BoundLogger:
    """Logger tagged with a `log_category` field for downstream routing/filtering."""
    return structlog.get_logger(category).bind(log_category=category)

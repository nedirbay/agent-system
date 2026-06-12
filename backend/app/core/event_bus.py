"""Event Bus publisher abstraction (EVENT_BUS_SPECIFICATION.md).

Defines the standard event envelope and a publisher port. A Kafka-backed
implementation is provided; it connects lazily so the app boots without Kafka.
"""
from __future__ import annotations

import json
import uuid
from abc import ABC, abstractmethod
from datetime import datetime, timezone
from typing import Any

from app.core.config import get_settings
from app.core.logging import get_logger

logger = get_logger(__name__)


def build_event(
    event_type: str,
    payload: dict[str, Any],
    *,
    task_id: str | None = None,
    correlation_id: str | None = None,
    producer: str = "api",
    version: str = "v1",
) -> dict[str, Any]:
    """Construct the standard event envelope from the Event Bus spec."""
    return {
        "eventId": str(uuid.uuid4()),
        "eventType": event_type,
        "taskId": task_id,
        "correlationId": correlation_id or str(uuid.uuid4()),
        "producer": producer,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "version": version,
        "payload": payload,
    }


class EventPublisher(ABC):
    @abstractmethod
    async def publish(self, topic: str, event: dict[str, Any]) -> None: ...

    async def start(self) -> None:  # pragma: no cover - optional lifecycle
        ...

    async def stop(self) -> None:  # pragma: no cover - optional lifecycle
        ...


class LoggingEventPublisher(EventPublisher):
    """Fallback publisher used when Kafka is unavailable (logs events)."""

    async def publish(self, topic: str, event: dict[str, Any]) -> None:
        logger.info("event.published", topic=topic, event_type=event.get("eventType"))


class KafkaEventPublisher(EventPublisher):
    """At-least-once Kafka publisher (partitioned by taskId for ordering)."""

    def __init__(self, bootstrap_servers: str) -> None:
        self._bootstrap = bootstrap_servers
        self._producer: Any | None = None

    async def start(self) -> None:
        from aiokafka import AIOKafkaProducer

        self._producer = AIOKafkaProducer(
            bootstrap_servers=self._bootstrap,
            value_serializer=lambda v: json.dumps(v).encode(),
            key_serializer=lambda k: k.encode() if k else None,
            enable_idempotence=True,
        )
        await self._producer.start()

    async def stop(self) -> None:
        if self._producer is not None:
            await self._producer.stop()
            self._producer = None

    async def publish(self, topic: str, event: dict[str, Any]) -> None:
        if self._producer is None:
            raise RuntimeError("KafkaEventPublisher not started")
        await self._producer.send_and_wait(topic, event, key=event.get("taskId"))


_publisher: EventPublisher | None = None


def get_event_publisher() -> EventPublisher:
    """Return the process-wide publisher (FastAPI dependency / DI seam)."""
    global _publisher
    if _publisher is None:
        _publisher = LoggingEventPublisher()
    return _publisher


def set_event_publisher(publisher: EventPublisher) -> None:
    global _publisher
    _publisher = publisher

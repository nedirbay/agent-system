from __future__ import annotations

from pydantic import BaseModel


class ProcessingTime(BaseModel):
    avg: float
    p50: float
    p95: float
    p99: float
    max: float


class MetricsSummary(BaseModel):
    uptime_seconds: float
    requests_total: int
    errors_total: int
    client_errors_total: int
    error_rate: float
    tasks_total: int
    tasks_by_kind: dict[str, int]
    processing_time_ms: ProcessingTime
    # DB-derived gauges (Section-11)
    active_users: int
    total_users: int
    active_agents: int
    task_count: int

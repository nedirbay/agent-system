"""In-process performance metrics registry (Faza 9 Task 28 / SYSTEM_REQUIREMENTS §11).

A dependency-free, thread-safe metrics collector covering the Section-11
metrics: task count, processing time, and error rate (active users/agents are
derived from the database at scrape time — see the monitoring module).

The production target is OpenTelemetry → Prometheus (ADR-014/CC-002); this
registry is the offline MVP and already speaks the Prometheus text exposition
format, so a scraper can read it directly via `/monitoring/metrics/prometheus`.
"""
from __future__ import annotations

import threading
import time
from collections import deque

# Histogram-ish buckets for request processing time, in seconds.
_MAX_SAMPLES = 4096


class MetricsRegistry:
    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._started = time.monotonic()
        self._requests = 0
        self._errors = 0  # HTTP 5xx
        self._client_errors = 0  # HTTP 4xx
        self._duration_sum = 0.0
        self._durations: deque[float] = deque(maxlen=_MAX_SAMPLES)
        self._tasks: dict[str, int] = {}
        self._status: dict[int, int] = {}

    # --- recording ------------------------------------------------------ #

    def record_request(self, duration_seconds: float, status_code: int) -> None:
        with self._lock:
            self._requests += 1
            self._duration_sum += duration_seconds
            self._durations.append(duration_seconds)
            self._status[status_code] = self._status.get(status_code, 0) + 1
            if status_code >= 500:
                self._errors += 1
            elif status_code >= 400:
                self._client_errors += 1

    def record_task(self, kind: str) -> None:
        """Count a unit of agent/workflow work (Section-11 "task count")."""
        with self._lock:
            self._tasks[kind] = self._tasks.get(kind, 0) + 1

    def reset(self) -> None:
        """Clear all metrics — used by tests for isolation."""
        with self._lock:
            self._started = time.monotonic()
            self._requests = 0
            self._errors = 0
            self._client_errors = 0
            self._duration_sum = 0.0
            self._durations.clear()
            self._tasks.clear()
            self._status.clear()

    # --- reading -------------------------------------------------------- #

    @staticmethod
    def _percentile(samples: list[float], pct: float) -> float:
        if not samples:
            return 0.0
        ordered = sorted(samples)
        idx = min(len(ordered) - 1, int(round((pct / 100.0) * (len(ordered) - 1))))
        return ordered[idx]

    def snapshot(self) -> dict:
        with self._lock:
            samples = list(self._durations)
            requests = self._requests
            errors = self._errors
            duration_sum = self._duration_sum
            tasks = dict(self._tasks)
            client_errors = self._client_errors
            uptime = time.monotonic() - self._started

        avg = (duration_sum / requests) if requests else 0.0
        return {
            "uptime_seconds": round(uptime, 1),
            "requests_total": requests,
            "errors_total": errors,
            "client_errors_total": client_errors,
            "error_rate": round(errors / requests, 4) if requests else 0.0,
            "tasks_total": sum(tasks.values()),
            "tasks_by_kind": tasks,
            "processing_time_ms": {
                "avg": round(avg * 1000, 2),
                "p50": round(self._percentile(samples, 50) * 1000, 2),
                "p95": round(self._percentile(samples, 95) * 1000, 2),
                "p99": round(self._percentile(samples, 99) * 1000, 2),
                "max": round(max(samples) * 1000, 2) if samples else 0.0,
            },
        }

    def prometheus_text(self, *, gauges: dict[str, float] | None = None) -> str:
        snap = self.snapshot()
        lines: list[str] = []

        def metric(name: str, value: float, mtype: str, help_text: str) -> None:
            lines.append(f"# HELP {name} {help_text}")
            lines.append(f"# TYPE {name} {mtype}")
            lines.append(f"{name} {value}")

        metric("http_requests_total", snap["requests_total"], "counter", "Total HTTP requests")
        metric("http_request_errors_total", snap["errors_total"], "counter", "HTTP 5xx responses")
        metric(
            "http_request_duration_ms_avg",
            snap["processing_time_ms"]["avg"],
            "gauge",
            "Average request processing time (ms)",
        )
        metric(
            "http_request_duration_ms_p95",
            snap["processing_time_ms"]["p95"],
            "gauge",
            "p95 request processing time (ms)",
        )
        metric("agent_tasks_total", snap["tasks_total"], "counter", "Total agent/workflow tasks")
        for kind, count in snap["tasks_by_kind"].items():
            lines.append(f'agent_tasks_total{{kind="{kind}"}} {count}')

        for name, value in (gauges or {}).items():
            metric(name, float(value), "gauge", name.replace("_", " "))

        return "\n".join(lines) + "\n"


_registry = MetricsRegistry()


def get_metrics() -> MetricsRegistry:
    """Process-wide metrics registry singleton."""
    return _registry

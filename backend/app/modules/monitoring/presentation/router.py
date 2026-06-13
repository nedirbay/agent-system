from __future__ import annotations

from fastapi import APIRouter, Depends
from fastapi.responses import PlainTextResponse

from app.modules.monitoring.application.services import MonitoringService
from app.modules.monitoring.presentation.dependencies import get_monitoring_service
from app.modules.monitoring.presentation.schemas import MetricsSummary

router = APIRouter(prefix="/monitoring", tags=["Monitoring"])


@router.get("/metrics", response_model=MetricsSummary)
async def metrics_summary(
    service: MonitoringService = Depends(get_monitoring_service),
) -> MetricsSummary:
    """Section-11 metrics: active users/agents, task count, processing time, error rate."""
    return MetricsSummary(**await service.summary())


@router.get("/metrics/prometheus", response_class=PlainTextResponse)
async def metrics_prometheus(
    service: MonitoringService = Depends(get_monitoring_service),
) -> str:
    """Prometheus text exposition format for scraping (ADR-014)."""
    return await service.prometheus()

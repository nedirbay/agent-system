# Scalability Review — Task 31 (Faza 10)

> Reviews the implementation against the performance (PER-001..004), scalability
> (§9), and reliability (§10) requirements in `SYSTEM_REQUIREMENTS.md` and the
> architecture in `HIGH_LEVEL_ARCHITECTURE.md`. Honest MVP posture.

_Last reviewed: 2026-06-13._

## Performance requirements

| Req | Target | Status | Notes |
|---|---|---|---|
| PER-001 Search response | ≤ 5 s | **Supported by design** | Qdrant vector search + `retrieval_top_k`; `/monitoring/metrics` reports live p50/p95/p99 processing time so the target is measurable. |
| PER-002 QA response | ≤ 15 s | **Supported by design** | RAG retrieve→answer; bounded by the LLM provider. Extractive fallback when no LLM. |
| PER-003 Upload processing | 1,000 docs at once | **Partial** | Upload + parse implemented; bulk throughput depends on running parsing as background workers (event-driven), currently in-process. |
| PER-004 Concurrent users | ≥ 100 | **Supported by design** | Stateless async FastAPI workers scale horizontally behind a load balancer; see below. |

## Horizontal scaling (§9)

| Property | Status | Evidence |
|---|---|---|
| Stateless application tier | **Implemented** | No in-process user state; session memory lives in **Redis**, not the worker. Any instance can serve any request. |
| Shared session/state store | **Implemented** | Redis-backed session memory (Faza 6) with TTL; live workflow state externalized. |
| Vector/data tiers scale independently | **Implemented (design)** | Postgres, Qdrant, Redis, object storage are separate services (TECH_STACK_DECISION). |
| Distributed processing / agent scaling | **Partial** | Event Bus (Kafka) scaffolded for decoupled, independently-scaled agents; the MVP workflow engine runs in-process (documented in config). |
| Readiness for orchestration | **Implemented** | `GET /health` (liveness) + `GET /health/ready` (readiness: DB/Redis/Qdrant probes, DB critical) enable load-balancer / k8s rollout and autoscaling. |
| Connection pooling | **Implemented** | SQLAlchemy async engine pool per worker. |

## Reliability (§10)

| Req | Status | Notes |
|---|---|---|
| Availability 99.5% | **Supported by design** | Stateless replicas + readiness gating + graceful degradation (FH-001): Redis/Qdrant outages downgrade features rather than failing the node. |
| Graceful degradation | **Implemented** | Memory recall falls back to recent items; monitoring gauges and readiness degrade to "down" without crashing. |
| Backups / DR | **Deferred** | Daily encrypted backups + DR runbook are ops-layer (Section 10); not app code. |

## Observability for scaling decisions

- `MetricsRegistry` (Faza 9) exposes request count, **error rate**, and
  **processing-time percentiles** — the inputs an HPA / operator uses to scale.
- `/monitoring/metrics/prometheus` is scrape-ready (ADR-014).
- Per-request `correlation_id` (CC-002) supports tracing a request across
  horizontally-scaled instances.

## Known MVP limits / next steps

1. Move document parsing & agent steps onto Kafka-driven background workers so
   PER-003 bulk ingestion scales out (the engine is in-process today).
2. Add load/soak testing to validate PER-001/002/004 against real targets.
3. Tune Postgres/Qdrant connection-pool sizing per replica under load.
4. Introduce caching for hot retrieval queries to protect PER-001 at scale.

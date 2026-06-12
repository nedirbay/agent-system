# HIGH_LEVEL_ARCHITECTURE.md

# Overview

This document provides the high-level architecture of the AI Multi-Agent Knowledge & Automation Platform — the deliverable promised in `PROJECT_ROADMAP.md` Task 2. It ties together every other specification into one picture: how requests flow, how the layers relate, and how the system is deployed and scaled.

It references rather than repeats the detailed specs: agents (`AGENT_SPECIFICATIONS.md`), coordination (`WORKFLOW_ENGINE_SPECIFICATION.md`, `EVENT_BUS_SPECIFICATION.md`), storage (`DATABASE_DESIGN.md`), API (`API_SPECIFICATION.md`), intelligence (`LLM_AND_RAG_STRATEGY.md`), technology (`TECH_STACK_DECISION.md`), and security (`SECURITY_ARCHITECTURE.md`).

---

# Architectural Goals

## AG-001

Separate concerns into independent, horizontally scalable layers (`SYSTEM_REQUIREMENTS.md` Section 9).

## AG-002

Keep agents stateless and decoupled, communicating only through the Event Bus (`AGENT_SPECIFICATIONS.md`, `EVENT_BUS_SPECIFICATION.md`).

## AG-003

Run fully on-premise with no mandatory cloud dependency (`TECH_STACK_DECISION.md` GP-001).

## AG-004

Meet the platform targets: 10M+ documents, 100+ concurrent users, 1M+ events/day, 99.5% availability.

---

# System Context

```text
                 ┌─────────────────────────────────────────┐
   Users         │              The Platform                │     External
 (4 roles)  ───▶ │  (ingest · search · QA · analyze ·       │ ──▶ Sources
                 │   report · automate)                     │     (files, DBs,
                 │                                          │      APIs, cloud)
                 └─────────────────────────────────────────┘
```

Users (Administrator, Analyst, Operator, Read-Only) interact through the web UI. The platform ingests from local files, shared folders, databases, APIs, and cloud storage (`SYSTEM_REQUIREMENTS.md` Section 6).

---

# Layered Architecture

```text
┌──────────────────────────────────────────────────────────────┐
│ 1. PRESENTATION LAYER                                         │
│    Web UI: Chat · Workspace · Dashboard   (React/TS)          │
└───────────────▲──────────────────────────────────────────────┘
                │ HTTPS / REST + SSE  (API_SPECIFICATION.md)
┌───────────────┴──────────────────────────────────────────────┐
│ 2. API / GATEWAY LAYER                                        │
│    AuthN/AuthZ · rate limit · routing · request validation    │
└───────────────▲──────────────────────────────────────────────┘
                │
┌───────────────┴──────────────────────────────────────────────┐
│ 3. ORCHESTRATION LAYER                                        │
│    Orchestrator Agent · Workflow Engine                       │
│    (plan → sequence → route → recover)                        │
└───────────────▲──────────────────────────────────────────────┘
                │ publish / consume events
┌───────────────┴──────────────────────────────────────────────┐
│ 4. EVENT BUS  (Kafka)                                         │
│    durable · ordered-per-task · retry · DLQ                   │
└───────────────▲──────────────────────────────────────────────┘
                │
┌───────────────┴──────────────────────────────────────────────┐
│ 5. AGENT LAYER  (stateless workers, scaled independently)     │
│  Document · Knowledge · Analysis · QA · Report · Research ·   │
│  Execution · Memory · Critic                                  │
└───────────────▲──────────────────────────────────────────────┘
                │
┌───────────────┴──────────────────────────────────────────────┐
│ 6. INTELLIGENCE LAYER                                         │
│    LLM Provider abstraction · Embeddings · RAG pipeline       │
│    (LLM_AND_RAG_STRATEGY.md)                                  │
└───────────────▲──────────────────────────────────────────────┘
                │
┌───────────────┴──────────────────────────────────────────────┐
│ 7. DATA LAYER                                                 │
│  PostgreSQL · Vector DB · Redis · Object Storage              │
│  (DATABASE_DESIGN.md)                                         │
└──────────────────────────────────────────────────────────────┘

   Cross-cutting:  Security (SECURITY_ARCHITECTURE.md) ·
                   Observability (OTel/Prometheus/Grafana/Loki)
```

---

# Layer Responsibilities

## L1 Presentation

The React/TypeScript web app (Roadmap Phase 8): Chat Interface (`FR-007`), Workspace for documents/tasks, and analytics Dashboard (`FR-010`). Talks only to the API layer; streams chat and progress via SSE.

## L2 API / Gateway

Single entry point. Authenticates JWTs, enforces RBAC (`FR-002`), rate-limits, validates requests, and routes to services. Implements the contract in `API_SPECIFICATION.md`. Long-running work is accepted as a task and tracked asynchronously.

## L3 Orchestration

The Orchestrator Agent decomposes a request into a plan (Roadmap Task 11) and selects agents (Task 12). The Workflow Engine executes that plan as an ordered, recoverable workflow (`WORKFLOW_ENGINE_SPECIFICATION.md`), persisting state and enforcing human-approval gates.

## L4 Event Bus

The asynchronous backbone (`EVENT_BUS_SPECIFICATION.md`). All inter-component messaging flows here: durable, per-task ordered, with retries and a Dead Letter Queue. Decouples producers from consumers and enables independent scaling.

## L5 Agents

Nine specialized, stateless agent types (`AGENT_SPECIFICATIONS.md`). Each consumes its assigned events, does one job, writes outputs/logs, and publishes a completion event. They never call each other directly and never talk to the user directly.

## L6 Intelligence

The shared AI capability behind the agents: the LLM provider abstraction (`AIR-006`), embedding generation, and the RAG retrieval/grounding pipeline (`LLM_AND_RAG_STRATEGY.md`). Agents request reasoning/generation/retrieval through this layer.

## L7 Data

The four storage technologies from `DATABASE_DESIGN.md` / `TECH_STACK_DECISION.md`: PostgreSQL (system of record), Vector DB (embeddings/semantic search), Redis (sessions, live workflow state), and Object Storage (files, reports, screenshots).

---

# Primary Data Flows

## Flow A — Document Ingestion (FR-003 → FR-006)

```text
UI ──upload──▶ API ──store file──▶ Object Storage
                │
                └─ publish DocumentUploaded ─▶ Event Bus
                                                  │
                                 Workflow Engine starts ingestion workflow:
                                 Document Agent (parse + OCR + metadata)
                                        ▼
                                 Document Agent (chunk)
                                        ▼
                                 Knowledge Agent (embed → Vector DB; index)
                                        ▼
                                 Critic Agent (validate)
                                        ▼
                                 publish document.indexed
```

Document status moves `Uploaded → Processing → Indexed` (`DOCUMENTS`).

## Flow B — Question Answering (FR-007)

```text
UI ──question──▶ API ──create task──▶ Orchestrator
                                          │ plan
                                          ▼
   Memory Agent (context) ─▶ Knowledge Agent (hybrid retrieval)
                                          ▼
                              QA Agent (grounded answer + citations)
                                          ▼
                              Critic Agent (hallucination check)
                                          ▼
   API ◀── answer + references (streamed via SSE) ◀── Workflow Engine
```

Must complete within PER-002 (≤ 15 s); search step within PER-001 (≤ 5 s).

## Flow C — Analysis & Report (FR-008 → FR-009)

```text
UI ▶ API ▶ Orchestrator ▶ Analysis Agent (stats/trends)
                                 ▼
                         Report Agent (PDF/DOCX/XLSX) ▶ Object Storage
                                 ▼
                         notify user ▶ download via API
```

## Flow D — Computer Use (FR-015)

```text
UI ▶ API ▶ Orchestrator ▶ Workflow Engine
                                 ▼
                         Human Approval Step (if sensitive) ── waits ──▶ /approvals
                                 ▼ (approved)
                         Execution Agent ── runs in isolated sandbox
                                 ▼
                         logs + screenshots + outputs ▶ Data Layer
```

Sensitive actions are gated by approval; execution is sandboxed (`SECURITY_ARCHITECTURE.md` SB-*).

---

# Cross-Cutting Concerns

## CC-001 Security

Applied at every layer: TLS everywhere, JWT/RBAC at the gateway, service mTLS, encrypted storage, the Execution Agent sandbox, and a full audit trail. See `SECURITY_ARCHITECTURE.md`.

## CC-002 Observability

OpenTelemetry traces follow a request across all layers via `correlationId`. Metrics (active users/agents, task count, processing time, error rate) and the four log categories satisfy `SYSTEM_REQUIREMENTS.md` Section 11.

## CC-003 Memory & Context

The Memory Agent provides session, working, long-term, and knowledge memory to other agents, keeping them stateless while preserving context across steps (`FR-012`).

## CC-004 Auditing

Every user, agent, and system action is recorded (`FR-014`); audit and security events have their own retention tiers.

---

# Deployment Architecture

```text
                 ┌──────────── Kubernetes Cluster ────────────┐
   Clients ─TLS─▶ │  Ingress / API Gateway                     │
                 │     │                                       │
                 │     ├─ API services            (HPA)        │
                 │     ├─ Orchestrator + Workflow (HPA)        │
                 │     ├─ Agent workers · one Deployment each  │
                 │     │     (Document, QA, Analysis, …)       │
                 │     ├─ Execution Agent sandbox pool         │
                 │     │     (gVisor/Firecracker, isolated zone)│
                 │     └─ Intelligence services (embeddings,   │
                 │           LLM gateway)                      │
                 │                                             │
                 │  Stateful set / managed:                    │
                 │     Kafka · PostgreSQL · Vector DB ·        │
                 │     Redis · MinIO                           │
                 │                                             │
                 │  Platform: Prometheus·Grafana·Loki·Keycloak │
                 └─────────────────────────────────────────────┘
```

## DEP-001 Scaling Units

Each agent type is its own Deployment with a HorizontalPodAutoscaler, scaling on Event Bus consumer lag (`AGENT_SPECIFICATIONS.md` horizontal-scaling requirement, Workflow SC-*).

## DEP-002 Statelessness

API services, orchestration, and agents hold no local state; all state lives in the data layer, enabling free horizontal scaling and self-healing.

## DEP-003 Sandbox Pool

Execution Agent sandboxes run in a dedicated, network-isolated node pool (`SECURITY_ARCHITECTURE.md` NET-002).

## DEP-004 Environments

Local (Docker Compose), Staging, and Production (Kubernetes), per `TECH_STACK_DECISION.md`.

---

# Scalability & Reliability Summary

| Requirement | How the architecture meets it |
| --- | --- |
| 10M+ documents | Vector DB sharding + object storage + Postgres partitioning. |
| 100+ concurrent users | Stateless API/agents behind HPA. |
| 1M+ events/day | Kafka partitioned by `taskId`. |
| 99.5% availability | K8s self-healing, replicas, daily backups, DR plan. |
| ≤ 5 s search / ≤ 15 s QA | Hybrid retrieval, caching, model tiering, streaming. |
| Horizontal scaling | Independent Deployments per agent + consumer-group scaling. |

---

# Document Map

| Concern | Specification |
| --- | --- |
| What & why | `SYSTEM_REQUIREMENTS.md` |
| Architecture (this) | `HIGH_LEVEL_ARCHITECTURE.md` |
| Agents | `AGENT_SPECIFICATIONS.md` |
| Coordination | `WORKFLOW_ENGINE_SPECIFICATION.md`, `EVENT_BUS_SPECIFICATION.md` |
| Storage | `DATABASE_DESIGN.md` |
| External API | `API_SPECIFICATION.md` |
| AI / RAG | `LLM_AND_RAG_STRATEGY.md` |
| Technology choices | `TECH_STACK_DECISION.md` |
| Security | `SECURITY_ARCHITECTURE.md` |
| Plan | `PROJECT_ROADMAP.md` |

---

# Success Criteria

The architecture is validated if:

* Every functional requirement maps onto a clear path through the layers.
* Each layer can be scaled and deployed independently.
* Agents remain stateless and communicate only via the Event Bus.
* The whole system runs on a single on-prem cluster with no mandatory cloud dependency.
* The platform targets (scale, concurrency, event volume, availability, latency) are achievable as described.

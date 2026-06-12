# TECH_STACK_DECISION.md

# Overview

This document records the concrete technology choices for the AI Multi-Agent Knowledge & Automation Platform. The other specifications are deliberately technology-agnostic; this document binds those logical components ("Vector Database", "Event Bus", "Cache Layer") to specific products and explains why.

Each decision is recorded as an ADR-style entry: context, decision, and rationale. Decisions marked **Locked** should not be changed without a new version of this document. Decisions marked **Default** are sensible starting points that may be revisited during Phase 1.

---

# Guiding Principles

## GP-001 On-Premise First

The platform must run fully on-premise for enterprise/regulated customers. No component may *require* a public cloud service. Cloud is an optional deployment target, not a dependency.

## GP-002 Open Standards

Prefer open, portable interfaces (S3 API, OpenAPI, SQL, OpenTelemetry) so individual components can be swapped.

## GP-003 Operational Simplicity

Prefer fewer moving parts that the target team can actually run. Avoid introducing a new datastore when an existing one suffices.

## GP-004 AI-Native

The stack must make LLM orchestration, embeddings, and RAG first-class, not bolted on.

---

# Decision Summary

| Layer | Choice | Status |
| --- | --- | --- |
| Backend language / framework | Python 3.12 + FastAPI | Locked |
| Async task workers | Python + asyncio, containerized per agent | Locked |
| Frontend | TypeScript + React + Vite | Locked |
| UI component layer | Tailwind CSS + shadcn/ui | Default |
| Relational database | PostgreSQL 16 | Locked |
| Vector database | Qdrant (pgvector for small deployments) | Default |
| Cache / session store | Redis 7 | Locked |
| Event Bus | Apache Kafka (Redpanda-compatible) | Default |
| Object / file storage | MinIO (S3-compatible API) | Locked |
| LLM provider | Anthropic Claude family | Default |
| Embeddings | Voyage AI (cloud) / BGE-M3 (on-prem) | Default |
| OCR | Tesseract + PaddleOCR fallback | Default |
| Document parsing | Apache Tika + unstructured | Default |
| Execution Agent sandbox | gVisor-isolated containers / Firecracker microVM | Locked |
| Containerization | Docker + Kubernetes | Locked |
| Observability | OpenTelemetry + Prometheus + Grafana + Loki | Default |
| Auth | OAuth2 / OIDC + JWT (Keycloak) | Default |
| CI/CD | GitHub Actions + Helm | Default |

---

# ADR-001 Backend: Python + FastAPI

## Context

The system is AI-heavy: LLM orchestration, embeddings, document parsing, OCR. These ecosystems are strongest in Python.

## Decision

Python 3.12 with FastAPI for all backend services and agent workers. Pydantic for schema validation (it also defines the API and event payload models).

## Rationale

* Richest AI/ML and document-processing ecosystem.
* FastAPI gives async I/O (needed for concurrent agent calls) and auto-generated OpenAPI (feeds `API_SPECIFICATION.md`).
* Pydantic models become the single source of truth shared by the API layer and the Event Bus payloads.

---

# ADR-002 Frontend: React + TypeScript

## Context

FR-010 / Roadmap Phase 8 require a chat interface, workspace, and analytics dashboard.

## Decision

TypeScript + React (Vite build), Tailwind CSS + shadcn/ui for components, TanStack Query for server state, Recharts for dashboard visualizations.

## Rationale

* Largest talent pool and component ecosystem.
* Strong streaming support for token-by-token chat responses.
* TypeScript types can be generated from the backend OpenAPI schema, keeping client and server in sync.

---

# ADR-003 Relational Database: PostgreSQL

## Context

`DATABASE_DESIGN.md` defines ~30 relational entities (users, tasks, agent runs, audit logs). Strong consistency and rich querying are required.

## Decision

PostgreSQL 16 as the system of record for all relational entities.

## Rationale

* ACID guarantees for tasks, audit logs, and workflow state persistence.
* JSONB columns store flexible payloads (agent configuration, event payloads) without a separate document store.
* The `pgvector` extension lets small deployments avoid a separate vector DB entirely (see ADR-004).

---

# ADR-004 Vector Database: Qdrant (pgvector fallback)

## Context

`AIR-007` RAG and FR-006 require semantic search over 100K → 10M+ documents across the collections `documents`, `knowledge`, `conversations`, `reports`.

## Decision

* **Default / scale:** Qdrant as a dedicated vector store.
* **Small deployments (< ~1M chunks):** `pgvector` inside the existing PostgreSQL, to reduce moving parts.

## Rationale

* Qdrant is open-source, on-prem friendly, supports payload filtering (tenant, document, category), and scales horizontally to the 10M+ target.
* Offering pgvector for small installs honors GP-003 (operational simplicity).
* Both are abstracted behind a `VectorStore` interface so the choice is a deployment-time config, not a code change.

---

# ADR-005 Cache Layer: Redis

## Context

`DATABASE_DESIGN.md` names cache keys for Active Sessions, Active Tasks, Agent State, and Workflow State. The Workflow Engine keeps live instance state in cache.

## Decision

Redis 7 for sessions, working context, live workflow state, and rate limiting.

## Rationale

* Microsecond reads for hot workflow-step transitions.
* Native TTLs match the retention policy (e.g. 30-day session memory).
* Pub/Sub available for lightweight intra-process signaling if needed.

---

# ADR-006 Event Bus: Apache Kafka

## Context

`EVENT_BUS_SPECIFICATION.md` requires: at-least-once delivery, per-task ordering, durable retention, a Dead Letter Queue, and 1,000,000+ events/day.

## Decision

Apache Kafka (or the API-compatible Redpanda for a lighter on-prem footprint) as the Event Bus.

## Rationale

* **Per-partition ordering** satisfies the required event ordering when partitioned by `taskId`.
* **Durable, replayable log** satisfies "events must persist" and the 30-day / 12-month / 24-month retention tiers.
* DLQ implemented as a dedicated topic.
* Consumer groups give horizontal scaling of agents (OBJ-002).
* Redpanda is a drop-in for teams that find full Kafka too heavy.

---

# ADR-007 Object Storage: MinIO

## Context

FR-003 and `DATABASE_DESIGN.md` File Storage require storing uploaded files, generated reports, screenshots, and attachments — potentially millions of objects.

## Decision

MinIO, exposing the S3 API.

## Rationale

* Fully on-prem, S3-compatible — code written against the S3 SDK runs unchanged on AWS S3 if a customer chooses cloud.
* Scales to billions of objects; supports versioning and encryption at rest (SEC-003).

---

# ADR-008 LLM Provider: Anthropic Claude

## Context

The platform is the "intelligence" behind every agent. `AIR-006` requires multi-model support; quality of QA, analysis, and reporting depends directly on model capability.

## Decision

Default to the Anthropic Claude family, accessed through a provider-abstraction layer so other models can be added (`AIR-006`):

* **Orchestrator / Analysis / Critic (complex reasoning):** `claude-opus-4-8`
* **Document / QA / Report (high-volume general work):** `claude-sonnet-4-6`
* **Classification / routing / cheap high-throughput steps:** `claude-haiku-4-5-20251001`

## Rationale

* Strong reasoning and long context for multi-step agent workflows and grounded RAG answers.
* Native tool-use and computer-use, directly serving FR-015 (Execution Agent).
* The tiered mapping controls cost: cheap models for routing, premium models only for hard reasoning.
* The abstraction layer keeps `AIR-006` (multi-model) satisfied and avoids hard provider lock-in.

> Detailed model routing, prompting, and grounding rules live in `LLM_AND_RAG_STRATEGY.md`.

---

# ADR-009 Embeddings: Voyage AI / BGE-M3

## Context

Claude does not provide an embeddings endpoint; RAG needs a dedicated embedding model with a fixed dimensionality for the vector collections.

## Decision

* **Cloud-allowed deployments:** Voyage AI (`voyage-3` class) — Anthropic's recommended embedding partner.
* **Strict on-prem deployments:** BGE-M3 (open-source) served locally via a small inference service.

## Rationale

* Two options preserve GP-001 (on-prem first) while giving the best quality where cloud is permitted.
* Embedding model and dimension are pinned per deployment; changing them requires a re-index, so the choice is recorded in deployment config and never mixed within one collection.

---

# ADR-010 Document Parsing & OCR

## Context

FR-004 / FR-005 require text + metadata extraction from PDF, DOCX, XLSX, CSV, TXT, JSON, and OCR for images and scanned PDFs.

## Decision

* Parsing: Apache Tika + the `unstructured` library for layout-aware extraction.
* OCR: Tesseract as default, PaddleOCR as fallback for difficult scans and non-Latin scripts.

## Rationale

* Tika covers the broadest range of formats; `unstructured` preserves structure (tables, headings) that improves chunk quality.
* Both OCR engines are open-source and run on-prem.

---

# ADR-011 Execution Agent Sandbox: gVisor / Firecracker

## Context

FR-015 and the Execution Agent allow browser actions, file operations, and script execution — the highest-risk capability. `SEC-005` mandates isolated execution.

## Decision

Run every Execution Agent task inside a strongly isolated, ephemeral sandbox:

* **Default:** gVisor-sandboxed containers (syscall interception).
* **High-security:** Firecracker microVMs (hardware-level isolation).

The sandbox has no access to the production network, secrets, or persistent storage beyond a scratch volume.

## Rationale

* Untrusted, model-driven actions must not be able to touch the host or other tenants.
* Ephemeral environments are destroyed after each task, limiting blast radius.

> Full sandbox design is specified in `SECURITY_ARCHITECTURE.md`.

---

# ADR-012 Containerization & Orchestration

## Context

`SYSTEM_REQUIREMENTS.md` Sections 9 (scalability) and 10 (reliability) require horizontal scaling, distributed processing, and 99.5% availability.

## Decision

Docker images for every service; Kubernetes for orchestration; Helm for packaging and deployment.

## Rationale

* Each agent type scales independently via its own Deployment + HorizontalPodAutoscaler (OBJ-002, SC-002 in the Workflow spec).
* Self-healing and rolling updates support the availability target.
* Helm charts give reproducible on-prem and cloud installs.

---

# ADR-013 Authentication & Authorization

## Context

FR-001 / FR-002 / SEC-001 / SEC-002 require login, session management, password reset, and role-based access (Administrator, Analyst, Operator, Read-Only).

## Decision

Keycloak as the identity provider (OAuth2 / OIDC), issuing JWT access tokens. The backend enforces RBAC from the roles/permissions tables in `DATABASE_DESIGN.md`.

## Rationale

* Off-the-shelf, on-prem identity with sessions, password reset, MFA, and LDAP/AD federation (common enterprise requirement).
* Standard JWT verification at the API gateway; fine-grained permission checks in the services.

---

# ADR-014 Observability

## Context

Section 11 requires metrics (active users/agents, task count, processing time, error rate) and four log categories (application, security, agent, audit).

## Decision

OpenTelemetry instrumentation across all services, exporting to Prometheus (metrics), Loki (logs), and Grafana (dashboards). Traces via Tempo/Jaeger.

## Rationale

* A single tracing standard lets one workflow be followed across the API, Event Bus, and every agent via `correlationId`.
* Open-source and on-prem; satisfies the monitoring requirements without vendor lock-in.

---

# Environment Strategy

| Environment | Purpose |
| --- | --- |
| Local (Docker Compose) | Single-machine developer stack with all components. |
| Staging (Kubernetes) | Pre-production validation, load testing against PER-* targets. |
| Production (Kubernetes) | HA deployment meeting the 99.5% availability target. |

---

# Open Decisions (to confirm in Phase 1)

* OD-001 — Vector DB at launch: Qdrant vs pgvector, based on expected corpus size.
* OD-002 — Event Bus: full Kafka vs Redpanda, based on ops capacity.
* OD-003 — Embedding model: cloud (Voyage) vs on-prem (BGE-M3), based on data-residency policy.
* OD-004 — Whether to self-host any open-weight LLM as an `AIR-006` secondary provider.

---

# Success Criteria

The stack is considered validated if:

* The full platform runs on a single on-prem cluster with no public-cloud dependency.
* Each logical component in the other specs maps to exactly one chosen product.
* Every chosen datastore meets its requirement tier (10M+ vectors, 1M+ events/day, 100+ concurrent users).
* Components remain swappable behind interfaces (vector store, LLM provider, embeddings, object storage).

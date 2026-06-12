# API_SPECIFICATION.md

# Overview

This document defines the external HTTP API of the AI Multi-Agent Knowledge & Automation Platform. It is the contract between the frontend (and any third-party client) and the backend, allowing both sides to be built in parallel.

The API is REST over HTTPS with JSON bodies, plus Server-Sent Events (SSE) for streaming chat. It is generated from and validated against the FastAPI / Pydantic models described in `TECH_STACK_DECISION.md`, and every endpoint maps to the functional requirements in `SYSTEM_REQUIREMENTS.md` and the entities in `DATABASE_DESIGN.md`.

---

# Conventions

## API-CV-001 Base URL & Versioning

All endpoints are namespaced under a version prefix:

```text
https://<host>/api/v1
```

Breaking changes increment the version (`/api/v2`). Additive changes do not.

## API-CV-002 Format

* Requests and responses use `application/json` (UTF-8), except file upload (`multipart/form-data`) and streaming (`text/event-stream`).
* Timestamps are ISO-8601 UTC (e.g. `2026-06-12T10:40:00Z`).
* Identifiers are UUID v4 strings.

## API-CV-003 Authentication

All endpoints except `/auth/login` and `/health` require a bearer token:

```text
Authorization: Bearer <jwt>
```

Tokens are issued by the identity provider (ADR-013). Each request is authorized against the caller's role and permissions (`FR-002`).

## API-CV-004 Pagination

List endpoints accept `?page=<n>&pageSize=<n>` (default `page=1`, `pageSize=20`, max `100`) and return a paginated envelope.

## API-CV-005 Idempotency

State-changing `POST` requests may include an `Idempotency-Key` header; replays with the same key return the original result. This aligns with the at-least-once / idempotency rules of the Event Bus.

## API-CV-006 Correlation

Clients may send `X-Correlation-Id`; if absent, the server generates one. It is propagated into the Event Bus `correlationId` so a request can be traced through every agent.

---

# Standard Response Envelopes

## Success

```json
{
  "success": true,
  "data": {},
  "meta": {
    "correlationId": "",
    "timestamp": ""
  }
}
```

## Paginated

```json
{
  "success": true,
  "data": [],
  "pagination": {
    "page": 1,
    "pageSize": 20,
    "totalItems": 0,
    "totalPages": 0
  },
  "meta": { "correlationId": "", "timestamp": "" }
}
```

## Error

```json
{
  "success": false,
  "error": {
    "code": "RESOURCE_NOT_FOUND",
    "message": "Human-readable description",
    "details": {}
  },
  "meta": { "correlationId": "", "timestamp": "" }
}
```

---

# Error Codes

| HTTP | code | Meaning |
| --- | --- | --- |
| 400 | `VALIDATION_ERROR` | Malformed or invalid request body / params. |
| 401 | `UNAUTHENTICATED` | Missing or invalid token. |
| 403 | `PERMISSION_DENIED` | Authenticated but not authorized for this action. |
| 404 | `RESOURCE_NOT_FOUND` | Entity does not exist. |
| 409 | `CONFLICT` | State conflict (e.g. duplicate, already processed). |
| 413 | `PAYLOAD_TOO_LARGE` | Upload exceeds the size limit. |
| 422 | `UNPROCESSABLE` | Semantically invalid (e.g. unsupported file type). |
| 429 | `RATE_LIMITED` | Too many requests. |
| 500 | `INTERNAL_ERROR` | Unhandled server error. |
| 503 | `SERVICE_UNAVAILABLE` | Dependency (LLM, vector DB, bus) unavailable. |

A `403 PERMISSION_DENIED` also emits a `PermissionDenied` security event on the Event Bus.

---

# Resource Map

| Area | Base path | Backing requirement |
| --- | --- | --- |
| Authentication | `/auth` | FR-001 |
| Users & roles | `/users`, `/roles` | FR-002 |
| Documents | `/documents` | FR-003, FR-004, FR-005 |
| Knowledge / search | `/search` | FR-006 |
| Question answering | `/qa` | FR-007 |
| Tasks & workflows | `/tasks`, `/workflows` | FR-011 |
| Analysis | `/analysis` | FR-008 |
| Reports | `/reports` | FR-009 |
| Dashboard | `/dashboard` | FR-010 |
| Notifications | `/notifications` | FR-013 |
| Audit | `/audit` | FR-014 |
| Approvals | `/approvals` | FR-015, Workflow human-approval |
| System | `/health`, `/system` | Section 11 |

---

# Authentication

## POST /auth/login

Authenticate and receive tokens (`FR-001`).

Request:

```json
{ "username": "", "password": "" }
```

Response `data`:

```json
{
  "accessToken": "",
  "refreshToken": "",
  "expiresIn": 3600,
  "user": { "id": "", "username": "", "role": "Analyst" }
}
```

## POST /auth/refresh

Exchange a refresh token for a new access token.

## POST /auth/logout

Invalidate the current session.

## POST /auth/password-reset/request

Begin password reset (sends email). Body: `{ "email": "" }`.

## POST /auth/password-reset/confirm

Complete reset. Body: `{ "token": "", "newPassword": "" }`.

---

# Users & Roles (Administrator only)

## GET /users

Paginated list of users.

## POST /users

Create a user. Body: `{ "username", "email", "fullName", "roleId", "password" }`.

## GET /users/{id}

Fetch a user.

## PATCH /users/{id}

Update profile, role, or status.

## DELETE /users/{id}

Deactivate a user (soft delete → `Status = Inactive`).

## GET /roles

List roles and their permissions (`ROLES`, `ROLE_PERMISSIONS`).

---

# Documents

## POST /documents

Upload one or more files (`FR-003`). `multipart/form-data`, field `files[]`. Supports PDF, DOCX, XLSX, CSV, TXT, JSON, PNG, JPG.

Response `data`:

```json
{
  "documents": [
    { "id": "", "originalName": "", "mimeType": "", "size": 0, "status": "Uploaded" }
  ]
}
```

Uploading triggers a `DocumentUploaded` event, which the Workflow Engine turns into the ingestion workflow (parse → OCR if needed → chunk → embed → index).

## GET /documents

List documents with filters: `?status=&category=&tag=&q=` plus pagination.

## GET /documents/{id}

Document detail, including processing `status` (`Uploaded → Processing → Indexed → Failed`) and extracted metadata.

## GET /documents/{id}/chunks

Paginated chunks for the document (`DOCUMENT_CHUNKS`).

## GET /documents/{id}/status

Lightweight processing-status poll for upload progress UIs.

## POST /documents/{id}/reprocess

Re-run the ingestion workflow (e.g. after a parser upgrade).

## DELETE /documents/{id}

Delete a document and its chunks/embeddings. **Requires human approval** (sensitive action) — returns `202 Accepted` with an `approvalId`; deletion completes only after approval.

---

# Search (Knowledge Base)

## POST /search

Semantic / similarity search over the knowledge base (`FR-006`). Must respond within the PER-001 budget (≤ 5 s).

Request:

```json
{
  "query": "",
  "collections": ["documents", "knowledge"],
  "filters": { "category": "", "tag": "", "language": "" },
  "topK": 10
}
```

Response `data`:

```json
{
  "results": [
    {
      "documentId": "",
      "chunkId": "",
      "score": 0.0,
      "snippet": "",
      "source": { "fileName": "", "page": 0 }
    }
  ]
}
```

Each search is recorded in `SEARCH_HISTORY`.

---

# Question Answering

## POST /qa/conversations

Start a QA conversation (`QA_CONVERSATIONS`). Returns `{ "conversationId": "" }`.

## POST /qa/conversations/{id}/messages

Ask a question (`FR-007`). Must respond within PER-002 (≤ 15 s).

Request:

```json
{ "question": "", "stream": true }
```

Non-streaming response `data`:

```json
{
  "answer": "",
  "references": [ { "documentId": "", "chunkId": "", "snippet": "", "page": 0 } ],
  "confidence": 0.0
}
```

When `stream: true`, the server returns `text/event-stream` with incremental tokens, then a final `references` event. Grounding and citation rules are defined in `LLM_AND_RAG_STRATEGY.md`.

## GET /qa/conversations/{id}/messages

Conversation history (`QA_MESSAGES`).

---

# Tasks & Workflows

## POST /tasks

Submit a high-level request to the Orchestrator (`FR-011`). The Orchestrator plans it into a workflow.

Request:

```json
{ "title": "", "description": "", "priority": "Normal", "input": {} }
```

Response `data`:

```json
{ "taskId": "", "status": "Pending", "workflowInstanceId": "" }
```

## GET /tasks

List the caller's tasks with status filters.

## GET /tasks/{id}

Task detail including current status (`Pending → Running → Completed/Failed/Cancelled`) and agent runs.

## GET /tasks/{id}/events

Stream (SSE) live progress events for the task, projected from the Event Bus (`task.*`, `agent.*`, `workflow.*`). Powers real-time progress UI.

## POST /tasks/{id}/cancel

Request cancellation; the Workflow Engine moves the instance to `Compensating`/`Cancelled`.

## GET /workflows

List workflow definitions (`WORKFLOWS`).

## GET /workflows/{id}

Definition detail including ordered steps (`WORKFLOW_STEPS`).

## GET /workflows/instances/{instanceId}

Live workflow instance state (status, current step, completed steps) as defined in `WORKFLOW_ENGINE_SPECIFICATION.md`.

---

# Analysis

## POST /analysis

Run a statistical / analytical job over selected documents or datasets (`FR-008`).

Request:

```json
{
  "type": "trend | aggregation | correlation | profiling",
  "sources": { "documentIds": [], "datasetId": "" },
  "options": {}
}
```

Returns a `taskId`; results are retrieved via `GET /tasks/{id}` or attached to a report.

---

# Reports

## POST /reports

Generate a report (`FR-009`).

Request:

```json
{
  "taskId": "",
  "name": "",
  "format": "pdf | docx | xlsx",
  "sections": []
}
```

Returns `{ "reportId": "", "status": "Generating" }`.

## GET /reports

List reports (`REPORTS`).

## GET /reports/{id}

Report metadata and section list.

## GET /reports/{id}/download

Download the generated file (streamed from object storage).

---

# Dashboard

## GET /dashboard/metrics

Aggregated metrics for the analytics panel (`FR-010`): document counts, task throughput, active agents, processing time, error rate.

## GET /dashboard/trends

Time-series data for charts, with `?from=&to=&granularity=` parameters.

---

# Notifications

## GET /notifications

List the caller's notifications (`NOTIFICATIONS`).

## POST /notifications/{id}/read

Mark a notification read.

## GET /notifications/stream

SSE stream of new in-app notifications.

---

# Approvals (Human-in-the-loop)

Backs the Human Approval Step in the Workflow Engine and FR-015 sensitive actions.

## GET /approvals

List pending approvals visible to the caller.

## GET /approvals/{id}

Approval detail: requesting task, action description, payload preview.

## POST /approvals/{id}/decision

Approve or reject. Body: `{ "decision": "approve | reject", "comment": "" }`. Emits the approval event the workflow is waiting on.

---

# Audit (Administrator)

## GET /audit

Query the audit trail (`FR-014`, `AUDIT_LOGS`) with filters `?userId=&entityType=&action=&from=&to=`. Covers user, agent, and system actions.

---

# System

## GET /health

Liveness/readiness probe (no auth). Returns component status (DB, cache, bus, vector store, LLM).

## GET /system/info

Version and build metadata (authenticated).

---

# Rate Limiting

## API-RL-001

Per-user and per-IP limits are enforced (Redis-backed). Exceeding a limit returns `429 RATE_LIMITED` with a `Retry-After` header. Heavy endpoints (`/qa`, `/analysis`, `/reports`) have stricter limits than read endpoints.

---

# Streaming (SSE) Conventions

## API-ST-001

Streaming endpoints (`/qa` messages, `/tasks/{id}/events`, notification/notification streams) use `text/event-stream`. Each event has a `type` and JSON `data`. Streams end with a terminal `done` event. Clients must tolerate reconnection using the `Last-Event-ID` header.

---

# Security Notes

* All traffic is TLS (SEC-003); tokens are short-lived JWTs with refresh.
* Authorization is enforced per endpoint against role permissions; the four roles map to permission sets from `SYSTEM_REQUIREMENTS.md` Section 3.
* Every state change writes an `AUDIT_LOGS` entry and, where relevant, a security event.
* Detailed threat model and controls are in `SECURITY_ARCHITECTURE.md`.

---

# Success Criteria

The API is considered complete if:

* Every functional requirement (FR-001 … FR-015) is reachable through at least one endpoint.
* Frontend and backend can be developed independently against this contract and the generated OpenAPI schema.
* All responses follow the standard envelopes and error codes.
* Long-running work is asynchronous (task + event stream), and only fast reads block.
* Sensitive actions route through `/approvals` before execution.

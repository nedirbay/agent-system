# SECURITY_ARCHITECTURE.md

# Overview

This document defines the security architecture of the AI Multi-Agent Knowledge & Automation Platform. It expands the high-level security requirements (`SYSTEM_REQUIREMENTS.md` Section 7, SEC-001 … SEC-005) into concrete controls, with particular focus on the highest-risk capability: the Execution Agent's ability to perform real computer actions (`FR-015`).

It covers identity and access, data protection, the agent execution sandbox, network segmentation, secret management, AI-specific threats, auditing, and incident response.

---

# Security Principles

## SP-001 Least Privilege

Every user, agent, and service receives the minimum permissions required. The Execution Agent in particular runs with no standing access to production data, secrets, or network.

## SP-002 Defense in Depth

Multiple independent controls protect each asset, so a single failure does not lead to compromise.

## SP-003 Zero Trust Between Components

Components authenticate to each other; no service is trusted purely because it is "inside" the network. This applies to Event Bus producers/consumers as well.

## SP-004 Secure by Default

Sensitive actions are denied unless explicitly approved. Sandboxes start with no capabilities and are granted only what a task needs.

## SP-005 Full Auditability

Every security-relevant action is logged immutably (`FR-014`, SEC-004).

---

# Threat Model (Summary)

| Threat | Primary control |
| --- | --- |
| Stolen / replayed credentials | Short-lived JWT, refresh rotation, MFA |
| Privilege escalation | RBAC enforced per request, server-side |
| Malicious / runaway agent action | Sandbox + human approval gate |
| Prompt injection via documents | Input isolation, action gating, output validation |
| Data exfiltration by Execution Agent | No-egress sandbox, scratch-only storage |
| Sensitive data leakage to LLM | Data classification, redaction, provider controls |
| Tampering with audit trail | Append-only, integrity-protected audit store |
| Event Bus message forgery | Authenticated producers, signed/validated events |
| Secret leakage | Central secret manager, no secrets in code/logs |

---

# Identity & Access Management

## IAM-001 Authentication

All access requires authentication via the identity provider (ADR-013, Keycloak / OIDC). Supports password login, password reset (`FR-001`), MFA, and enterprise federation (LDAP/AD).

## IAM-002 Tokens

Access is granted via short-lived JWTs (default 1 hour) with rotating refresh tokens. Tokens are validated at the API gateway and carry the user's role; fine-grained permission checks happen in the services.

## IAM-003 Role-Based Access Control

The four roles from `SYSTEM_REQUIREMENTS.md` Section 3 (Administrator, Analyst, Operator, Read-Only) map to permission sets stored in `ROLES` / `PERMISSIONS` / `ROLE_PERMISSIONS`. Authorization is enforced server-side on every endpoint (`FR-002`, SEC-002); the client never decides access.

## IAM-004 Service Identity

Each backend service and agent has its own service identity and credentials. Agents authenticate to the Event Bus and to internal APIs; there are no shared "god" credentials.

## IAM-005 Session Management

Sessions are tracked (`SESSIONS`), expire on inactivity, and can be revoked centrally (e.g. on role change or suspected compromise).

---

# Data Protection

## DP-001 Encryption in Transit

All traffic — client↔API, service↔service, Event Bus, database connections — uses TLS (SEC-003).

## DP-002 Encryption at Rest

PostgreSQL, the vector store, Redis persistence, and MinIO object storage are encrypted at rest. Backups are encrypted with separately managed keys.

## DP-003 Data Classification

Data is classified (public / internal / confidential / restricted). Classification drives what may be sent to an external LLM provider and what must stay on-prem.

## DP-004 PII & Sensitive Data Handling

Detected PII/secrets in documents can be redacted or masked before being placed in prompts, depending on policy. Restricted-class data uses the on-prem embedding/model path (`LLM_AND_RAG_STRATEGY.md`).

## DP-005 Tenancy Isolation

All knowledge-base queries and retrievals are scoped by ownership/tenant filters so one user cannot retrieve another tenant's documents (extends to the future multi-tenancy in `DATABASE_DESIGN.md`).

## DP-006 Data Retention & Deletion

Retention follows `DATABASE_DESIGN.md` (audit 12 mo, agent logs 6 mo, session memory 30 d, etc.). Deletion of documents removes their chunks and embeddings and is a human-approved action.

---

# Execution Agent Sandbox (Highest Risk)

The Execution Agent (`AG-008`, `FR-015`) performs browser actions, file operations, and script execution driven by an LLM. This is the platform's most dangerous capability and receives the strictest controls (SEC-005).

## SB-001 Isolation Technology

Every Execution Agent task runs in an ephemeral, strongly isolated sandbox (ADR-011): gVisor-sandboxed containers by default, Firecracker microVMs for high-security deployments. Each task gets a fresh environment that is destroyed on completion.

## SB-002 No Standing Privileges

The sandbox starts with:

* No access to the production network (default-deny egress).
* No access to platform secrets, databases, or other tenants' data.
* No persistent storage — only an ephemeral scratch volume.
* A non-root user with a minimal filesystem.

## SB-003 Capability Grants

A task is granted only the specific capabilities it needs (e.g. outbound access to one approved domain for a browser task), explicitly and time-boxed. Everything else remains denied.

## SB-004 Human Approval Gate

The sensitive actions listed in `AGENT_SPECIFICATIONS.md` and FR-015 — delete files, send emails, database updates, external integrations, configuration changes — require human approval **before** execution. The Workflow Engine's Human Approval Step enforces this; the Execution Agent cannot bypass it.

## SB-005 Forbidden Operations

Direct destructive operations (e.g. unscoped delete) are forbidden outright (per AG-008 restrictions), regardless of approval, unless performed through an audited, reversible, compensating workflow.

## SB-006 Resource Limits

CPU, memory, execution time, and disk are bounded per task. A task exceeding limits is terminated and reported as a failed step.

## SB-007 Full Recording

All sandbox activity — commands, file changes, network attempts, and screenshots — is logged and attached to the `AGENT_RUNS` / `AGENT_LOGS` / `AGENT_OUTPUTS` records for audit and replay.

## SB-008 Egress Control

Outbound network is denied by default and allowed only to an explicit, approved allowlist per task, through a monitored proxy. This is the primary defense against data exfiltration.

---

# AI-Specific Security

## AI-SEC-001 Prompt Injection

Uploaded documents and retrieved content are untrusted input. Mitigations:

* Treat retrieved content as data, never as instructions that can change agent policy.
* All consequential actions are gated behind the human-approval workflow, so an injected instruction cannot trigger a sensitive action on its own.
* The Critic Agent validates outputs before a workflow advances.

## AI-SEC-002 Output Validation

Model outputs that drive actions (tool calls, decision steps) are schema-validated and bounds-checked before execution.

## AI-SEC-003 Data Sent to Models

Data classification (DP-003) governs what may leave the perimeter. Restricted data uses on-prem models/embeddings only. Provider data-retention settings are configured to disable training on platform data.

## AI-SEC-004 Model Abuse / Cost Attacks

Rate limiting and per-task token budgets (`LLM_AND_RAG_STRATEGY.md` TC-001) prevent a malicious or looping request from causing runaway model cost.

---

# Network Security

## NET-001 Segmentation

The platform is divided into zones: public edge (gateway), application services, data stores, and the sandbox zone. Traffic between zones is restricted to required paths only.

## NET-002 Sandbox Isolation Zone

Execution Agent sandboxes run in a dedicated, network-isolated zone with no route to data stores or secret stores and default-deny egress (SB-002, SB-008).

## NET-003 Internal mTLS

Service-to-service traffic uses mutual TLS so each side authenticates the other (SP-003).

## NET-004 Edge Protection

The public edge enforces TLS termination, rate limiting, request size limits, and basic WAF rules.

---

# Secret Management

## SEC-MGT-001

All secrets (DB credentials, LLM API keys, signing keys, storage keys) live in a central secret manager (e.g. Vault / Kubernetes secrets with encryption). Secrets are never committed to code, baked into images, or written to logs.

## SEC-MGT-002

Secrets are injected at runtime, scoped to the service that needs them, and rotated on a schedule. The Execution Agent sandbox receives no platform secrets (SB-002).

---

# Auditing & Monitoring

## AUD-001 Audit Trail

Every user, agent, and system action is recorded in `AUDIT_LOGS` (`FR-014`) with actor, entity, action, details, and timestamp. The trail is append-only and integrity-protected.

## AUD-002 Security Events

Security-relevant events (`LoginSuccess`, `LoginFailed`, `PermissionDenied`, approval decisions, sandbox policy violations) flow through the Event Bus and are retained 24 months (per the Event Bus retention tiers).

## AUD-003 Monitoring & Alerting

Security signals are monitored: repeated login failures, permission-denied spikes, sandbox egress attempts, abnormal token cost, and DLQ growth. Alerts route to operators.

## AUD-004 Log Integrity

Security and audit logs are write-once from the application's perspective and protected from tampering; access to them is itself audited.

---

# Reliability & Recovery (Security-Relevant)

## REC-001 Backups

Daily encrypted backups (per Section 10) of relational data, vector store, and object storage, with tested restore procedures.

## REC-002 Disaster Recovery

A documented DR plan (mandatory per Section 10) with defined RPO/RTO, including restoration of audit integrity.

## REC-003 Key Management

Encryption keys are backed up and rotated independently of data; loss of a key must not be silently recoverable by an attacker.

---

# Compliance Posture

## CMP-001

The architecture supports common enterprise requirements: on-prem data residency (`TECH_STACK_DECISION.md` GP-001), full audit trail, RBAC, encryption in transit and at rest, and data deletion on request. Specific certifications (e.g. ISO 27001, SOC 2, GDPR alignment) are deployment/organization concerns built on these controls.

---

# Incident Response

## IR-001

A documented runbook covers: detection (alerts/audit), containment (revoke sessions/credentials, kill sandboxes, isolate a zone), eradication, recovery from backups, and post-incident review.

## IR-002

Compromise of an Execution Agent sandbox is contained by design: ephemeral environment, no secrets, no egress, no data-store access — so blast radius is limited to that task's scratch space.

---

# Success Criteria

The security architecture is successful if:

* All access is authenticated and authorized server-side against roles (SEC-001, SEC-002).
* Data is encrypted in transit and at rest, and restricted data never leaves the perimeter (SEC-003, DP-003).
* The Execution Agent runs only in isolated, ephemeral, no-egress sandboxes and cannot perform sensitive actions without human approval (SEC-005, SB-*).
* Prompt-injection cannot, by itself, cause a consequential action.
* Every security-relevant action is immutably audited (SEC-004).
* A compromised sandbox cannot reach secrets, data stores, or other tenants.

# Security Review — Task 30 (Faza 10)

> Reviews the implementation against `SECURITY_ARCHITECTURE.md`. Each control is
> marked **Implemented**, **Partial** (MVP-level / scaffolded), or **Deferred**
> (design locked, requires production infrastructure). This is an honest MVP
> posture statement, not a claim of full production hardening.

_Last reviewed: 2026-06-13 · Backend test suite: 60 passing._

## 1. Identity & Access (IAM / SEC-001)

| Control | Status | Evidence / Notes |
|---|---|---|
| Password hashing | **Implemented** | bcrypt with 72-byte guard — `app/core/security.py`. |
| JWT issuance | **Implemented** | `create_access_token` (HS256, expiry) on `/auth/login`. |
| JWT verification dependency | **Implemented** | `app/core/auth.py` `get_current_user` (signature + expiry, stateless). Demonstrated on `GET /auth/me`. |
| RBAC at the gateway | **Partial** | The `get_current_user` building block exists and is enforced on `/auth/me`; most module routers are still open and must opt in as they are locked down. Roles/claims not yet modeled. |
| OIDC / Keycloak federation | **Deferred** | Local HS256 secret today; ADR pins Keycloak for production. |

## 2. Data Protection (DP)

| Control | Status | Notes |
|---|---|---|
| TLS everywhere | **Deferred** | Terminates at the ingress/gateway in production; HSTS header emitted by the app outside dev (`SecurityHeadersMiddleware`). |
| Encryption at rest | **Deferred** | Provided by the managed Postgres/object-store layer, not the app. |
| Secrets handling | **Partial** | Config via env (`pydantic-settings`); no platform secret injected into the Execution sandbox (SB-002). Vault/rotation deferred. |
| Password hash never exposed | **Implemented** | `UserRead` projection omits the hash. |

## 3. Execution Agent Sandbox (SB-001..008)

| Control | Status | Evidence |
|---|---|---|
| Capability classification (allow / approve / deny) | **Implemented** | `SafeExecutionSandbox.classify` (Faza 7). |
| Human-approval gate (SB-004) | **Implemented** | Sensitive actions require `approved=True`; fail-closed plan execution. |
| Forbidden ops (SB-005) | **Implemented** | Unscoped `delete_file` denied outright. |
| Scratch confinement (SB-002) | **Implemented** | `LocalSandboxDesktopDriver` resolves all paths inside the scratch volume. |
| Egress allowlist (SB-008) | **Implemented** | Browser actions denied unless host is allowlisted. |
| Command allowlist + timeout (SB-003/006) | **Implemented** | `run_process` restricted to allowlisted executables with a wall-clock timeout. |
| Isolation technology (SB-001, gVisor/Firecracker) | **Deferred** | Drivers enforce policy in-process; real microVM/gVisor isolation is a deployment concern. Browser is a simulation, not a real sandboxed Chromium. |

## 4. AI-Specific Security (AI-SEC)

| Control | Status | Notes |
|---|---|---|
| Retrieved content treated as data, not instructions | **Implemented** | RAG context is concatenated as data; consequential actions gated behind approval. |
| Consequential actions behind approval | **Implemented** | Execution Agent SB-004 gate. |
| Output validation | **Partial** | Pydantic schema-validates request/response bodies; Critic-agent output screening is scaffolded. |

## 5. Auditing & Monitoring (AUD-001..004)

| Control | Status | Evidence |
|---|---|---|
| Append-only audit trail (AUD-001) | **Implemented** | `AuditLogService.record` (Faza 9). |
| Security events (AUD-002) | **Implemented** | `LoginSuccess`/`LoginFailed` recorded on the login path; `record_security_event` + security-category logs. |
| Monitoring & alerting (AUD-003) | **Partial** | Metrics exposed (`/monitoring/metrics`, Prometheus format); alerting rules are an ops-layer concern. |
| Log integrity (AUD-004) | **Implemented** | SHA-256 hash chain (`prev_hash`→`entry_hash`); `GET /audit/verify` detects tampering. |

## 6. Transport / Headers hardening

| Control | Status | Evidence |
|---|---|---|
| `X-Content-Type-Options`, `X-Frame-Options`, `Referrer-Policy`, `Permissions-Policy` | **Implemented** | `SecurityHeadersMiddleware` on every response. |
| HSTS | **Implemented (non-dev)** | Emitted when `environment` is not local/test. |
| CORS allowlist | **Implemented** | Restricted to configured origins. |

## Top remaining items before production

1. Enforce `get_current_user` (and role checks) across all non-public routers.
2. Replace local JWT secret with Keycloak/OIDC; model roles & permissions.
3. Provision real sandbox isolation (gVisor/Firecracker) + a real browser driver.
4. Wire alerting on the exposed metrics and audit security events.
5. Secret manager + rotation; verify at-rest encryption on managed stores.

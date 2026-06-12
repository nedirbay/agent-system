# WORKFLOW_ENGINE_SPECIFICATION.md

# Overview

This document defines the Workflow Engine of the AI Multi-Agent Knowledge & Automation Platform.

The Workflow Engine is the component that turns a user request into an ordered, observable sequence of agent executions. It sits between the Orchestrator Agent and the Event Bus: the Orchestrator decides *what* must happen, the Workflow Engine guarantees *that it happens in the right order, exactly once, and can recover from failure*.

It coordinates the agents defined in `AGENT_SPECIFICATIONS.md`, communicates exclusively through the channel defined in `EVENT_BUS_SPECIFICATION.md`, and persists its state in the tables defined in `DATABASE_DESIGN.md` (`WORKFLOWS`, `WORKFLOW_STEPS`, plus the `Workflow State` cache key).

---

# Objectives

## OBJ-001

Execute multi-step, multi-agent processes in a deterministic and repeatable way.

## OBJ-002

Decouple workflow logic from individual agents so that agents remain stateless and reusable.

## OBJ-003

Guarantee that a workflow can recover from a failure at any step without losing completed work.

## OBJ-004

Support both predefined workflow templates and dynamically planned workflows produced by the Orchestrator.

## OBJ-005

Provide full observability: every step, transition, and decision must be logged and auditable.

## OBJ-006

Support horizontal scaling so that thousands of workflows can run concurrently.

---

# Relationship to Other Components

| Component | Role in Workflow Execution |
| --- | --- |
| Orchestrator Agent | Plans the workflow and submits it to the engine. |
| Workflow Engine | Owns workflow state, sequencing, retries, and compensation. |
| Specialized Agents | Execute individual steps; they never sequence themselves. |
| Event Bus | Transport for all step dispatch and result events. |
| Memory Agent | Supplies and stores context between steps. |
| Critic Agent | Validates step output before the workflow advances. |
| Relational DB | Persists workflow definitions, instances, and step history. |
| Cache Layer | Holds the live `Workflow State` for fast transitions. |

---

# Core Concepts

## Workflow Definition

A reusable template describing an ordered set of steps. Stored in the `WORKFLOWS` and `WORKFLOW_STEPS` tables. A definition is versioned and immutable once activated.

## Workflow Instance

A single running execution of a definition, bound to one `TaskId`. It has its own state, variables, and step history.

## Step

The smallest unit of execution. Each step targets one agent type, carries a configuration, and produces an output that is passed forward.

## Variables / Workflow Context

A key-value store carried through the instance. Steps read inputs from it and write outputs back into it. This is how data flows from one agent to the next without direct agent-to-agent communication.

## Transition

A rule that decides which step runs next, based on the previous step's status and the workflow context.

---

# Workflow Types

## WT-001 Static Workflow

Defined ahead of time as a template in the database. Used for predictable, repeatable processes such as "ingest and index a document".

## WT-002 Dynamic Workflow

Generated at runtime by the Orchestrator Agent through task decomposition (see Roadmap Task 11). The plan is materialized into a transient instance with the same execution guarantees as a static workflow.

## WT-003 Sub-Workflow

A workflow invoked as a single step inside a parent workflow. The parent waits for the child to complete and merges its output into the parent context.

---

# Step Types

## ST-001 Agent Step

Dispatches a task to a single agent type and waits for its completion event.

## ST-002 Decision Step

Evaluates a condition against the workflow context and selects the next branch. No agent is invoked.

## ST-003 Parallel Step

Fans out to multiple agent steps at once and waits for all (or a configured quorum) to complete before continuing.

## ST-004 Validation Step

Routes the previous output to the Critic Agent. If validation fails, the engine triggers a retry or an alternative branch.

## ST-005 Human Approval Step

Pauses the workflow and waits for an external approval event. Required for the sensitive actions listed in `AGENT_SPECIFICATIONS.md` (delete files, send emails, database updates, external integrations, configuration changes).

## ST-006 Wait / Timer Step

Suspends the workflow until a time delay elapses or an external event arrives.

---

# Standard Workflow Definition Structure

A workflow definition is expressed as follows:

```json
{
  "workflowId": "",
  "name": "",
  "version": "",
  "isActive": true,
  "input": {},
  "steps": [
    {
      "stepId": "",
      "stepOrder": 1,
      "stepType": "AgentStep",
      "agentType": "DocumentAgent",
      "configuration": {},
      "inputMapping": {},
      "outputMapping": {},
      "onSuccess": "next",
      "onFailure": "retry",
      "timeoutSeconds": 120
    }
  ]
}
```

## Field Definitions

### workflowId

Unique identifier of the definition.

### version

Schema/definition version. A changed definition must use a new version; running instances keep the version they started with.

### steps

Ordered list of steps to execute.

### stepType

One of the step types defined above.

### agentType

The target agent for an Agent Step (must exist in the Agent Registry).

### inputMapping

Maps fields from the workflow context into the step's input payload.

### outputMapping

Maps the step's output back into the workflow context.

### onSuccess / onFailure

The transition target when the step succeeds or fails (`next`, a specific `stepId`, `retry`, `compensate`, or `end`).

### timeoutSeconds

Maximum time the engine waits for the step's completion event before treating it as failed.

---

# Workflow Instance State

The live state of a running instance, kept in the `Workflow State` cache and periodically persisted to the database.

```json
{
  "instanceId": "",
  "workflowId": "",
  "taskId": "",
  "correlationId": "",
  "status": "Running",
  "currentStep": "",
  "completedSteps": [],
  "context": {},
  "startedAt": "",
  "updatedAt": ""
}
```

---

# Workflow Lifecycle

```text
Created

↓

Scheduled

↓

Running

↓

Completed
```

Alternative paths:

```text
Running

↓

Waiting        (human approval / timer / external event)

↓

Running


Running

↓

Failed

↓

Compensating   (rollback of completed steps)

↓

Cancelled
```

## Status Values

* Created — instance built but not yet started.
* Scheduled — accepted by the engine, waiting for a worker.
* Running — actively executing steps.
* Waiting — suspended on an external signal.
* Completed — all steps finished successfully.
* Failed — a step exhausted retries and no recovery path exists.
* Compensating — running compensation steps to undo partial work.
* Cancelled — stopped by a user, admin, or compensation completion.

---

# Step Lifecycle

```text
Pending

↓

Dispatched

↓

Running

↓

Succeeded
```

Failure path:

```text
Running

↓

Failed

↓

Retrying

↓

Succeeded   (or)   Exhausted
```

This mirrors the Agent Lifecycle (`Created → Assigned → Running → Completed`) in `AGENT_SPECIFICATIONS.md`; one step maps to one `AGENT_RUNS` record.

---

# Execution Model

## EX-001 Event-Driven Dispatch

The engine never calls agents directly. To run a step it publishes the corresponding dispatch event (e.g. `task.assigned`) and registers a listener for the matching completion event (`agent.completed` / `agent.failed`).

## EX-002 One Step, One Event Correlation

Every dispatched step carries the instance `correlationId` and `taskId`, so the resulting completion event can be matched back to the exact waiting step.

## EX-003 Context Passing

Before dispatch, `inputMapping` reads from the instance context. After a successful completion, `outputMapping` writes the agent output back into the context for the next step.

## EX-004 Advancement

On a completion event, the engine evaluates the step's `onSuccess` / `onFailure` transition, updates the instance state, persists it, and dispatches the next step.

## EX-005 Determinism

Given the same definition, input, and agent outputs, a workflow must always follow the same path. Decision steps must be pure functions of the workflow context.

---

# Workflow Events

The engine produces and consumes the workflow events already declared in `EVENT_BUS_SPECIFICATION.md`.

## Published by the Engine

| Topic | Meaning |
| --- | --- |
| `workflow.started` | A new instance began execution. |
| `workflow.completed` | All steps finished successfully. |
| `workflow.failed` | The instance failed unrecoverably. |
| `task.assigned` | A step was dispatched to an agent. |

## Consumed by the Engine

| Topic | Reaction |
| --- | --- |
| `task.created` | Build and schedule a workflow instance for the task. |
| `agent.completed` | Apply output mapping and advance the workflow. |
| `agent.failed` | Trigger the step's failure transition (retry / compensate / fail). |

All workflow events follow the Standard Event Structure (`eventId`, `eventType`, `taskId`, `correlationId`, `producer`, `timestamp`, `version`, `payload`) and are immutable and auditable.

---

# Example Workflow: Document Ingestion & Indexing

A static workflow that fulfills FR-003 through FR-006.

```text
1. DocumentUploaded  (trigger)

↓

2. AgentStep        → Document Agent   (text + metadata extraction)

↓

3. DecisionStep     → is the document an image / scanned PDF?
                      ├── yes → AgentStep → OCR (via Document Agent)
                      └── no  → continue

↓

4. AgentStep        → Document Agent   (chunk generation)

↓

5. AgentStep        → Knowledge Agent  (embedding + indexing)

↓

6. ValidationStep   → Critic Agent     (quality / consistency check)

↓

7. WorkflowCompleted → emit document.indexed
```

---

# Example Workflow: Question Answering with Report

A dynamic workflow planned by the Orchestrator.

```text
1. AgentStep   → Memory Agent     (retrieve session + relevant context)

↓

2. AgentStep   → Knowledge Agent  (semantic retrieval)

↓

3. AgentStep   → QA Agent         (answer + citations)

↓

4. ValidationStep → Critic Agent  (hallucination / confidence check)
                    ├── pass → continue
                    └── fail → retry step 3 (max retries)

↓

5. DecisionStep   → did the user request a report?
                    ├── yes → AgentStep → Report Agent (PDF/DOCX/XLSX)
                    └── no  → end

↓

6. WorkflowCompleted
```

---

# Parallel Execution

## PE-001

A Parallel Step dispatches all of its branches at once, each as an independent agent task with the same `correlationId`.

## PE-002

The engine tracks a join condition: `all` (every branch must succeed) or `quorum` (a configured count).

## PE-003

Branch outputs are merged into the workflow context under named keys to avoid collisions.

## PE-004

If a required branch fails, the join fails and the step's `onFailure` transition is taken.

---

# Error Handling & Retries

## EH-001 Step Retry

A failed Agent Step is retried using the same backoff policy as the Event Bus:

* First failure → retry after 30 seconds
* Second failure → retry after 2 minutes
* Third failure → retry after 10 minutes
* Fourth failure → step is marked Exhausted

## EH-002 Exhausted Step

When retries are exhausted, the engine follows the step's `onFailure` target: an alternative branch, compensation, or workflow failure.

## EH-003 Timeout

If no completion event arrives within `timeoutSeconds`, the step is treated as failed and enters the retry policy.

## EH-004 Idempotency

Step dispatch and completion handling are idempotent. A duplicate completion event (At-Least-Once delivery) is detected by `eventId` and ignored, so a step is never advanced twice.

## EH-005 Dead Letter

If a workflow event itself cannot be processed after all retries, it is routed to the Dead Letter Queue defined in the Event Bus spec for manual review.

---

# Compensation (Saga Pattern)

## CO-001

For workflows that perform side effects (file operations, external integrations, database updates), each such step may declare a compensating step.

## CO-002

When a workflow enters the `Compensating` state, the engine runs the compensating steps of all completed steps in reverse order.

## CO-003

Compensation steps are themselves Agent Steps and follow the same retry and logging rules.

## CO-004

Once compensation completes, the instance transitions to `Cancelled` and a `workflow.failed` event is published with the failure cause.

---

# Human Approval Handling

## HA-001

A Human Approval Step moves the instance to `Waiting` and emits a notification (in-app / email, per FR-013).

## HA-002

The engine resumes only when it receives a matching approval or rejection event correlated by `taskId`.

## HA-003

Approval is mandatory for the sensitive actions listed in `AGENT_SPECIFICATIONS.md`. The Execution Agent must never act before the approval step has resolved.

## HA-004

Pending approvals may have an expiry; on expiry the step takes its `onFailure` transition (typically cancellation).

---

# State Persistence

## SP-001

Live instance state is held in the `Workflow State` cache key for fast step transitions.

## SP-002

State is persisted to the relational store after every step transition, so a crashed engine worker can resume an instance from its last committed step.

## SP-003

Definitions live in `WORKFLOWS` / `WORKFLOW_STEPS`; instance history is reconstructable from `TASK_EXECUTIONS`, `AGENT_RUNS`, `AGENT_OUTPUTS`, and `AGENT_LOGS`.

## SP-004

On worker restart, any instance in `Running` whose current step has no in-flight dispatch is re-dispatched (safe because step handling is idempotent).

---

# Scalability

## SC-001

Workflow instances are independent and may run on any engine worker.

## SC-002

Workers are stateless; all instance state lives in the cache and database, enabling horizontal scaling.

## SC-003

Step dispatch flows through the Event Bus, so agent capacity scales independently of the engine.

## SC-004

The engine must sustain the platform-level target of 1,000,000+ events per day and at least 100 concurrent users' workflows.

---

# Monitoring

## Metrics

* Active workflow instances
* Workflows started / completed / failed per period
* Average and p95 workflow duration
* Average step duration by agent type
* Step retry count
* Compensation count
* Pending human-approval count

## Logs

Every transition writes a structured log entry containing `instanceId`, `taskId`, `correlationId`, `stepId`, previous status, new status, and timestamp. These feed the Audit System (Roadmap Task 29) and the platform Audit Logs.

---

# Security

## Requirements

* Only the Orchestrator (or an authorized admin) may submit or cancel a workflow.
* Step dispatch events must be authenticated and authorized on the Event Bus.
* Workflow context may contain sensitive data and must be encrypted in transit and at rest.
* Sensitive steps require the Human Approval Step; the engine enforces this and cannot be bypassed.
* All workflow state changes are written to the audit trail.

---

# Failure Scenarios

## Engine Worker Failure

In-flight instances are resumed by another worker from the last persisted step.

## Agent Failure

The originating step receives an `agent.failed` event and enters the retry policy.

## Event Bus Failure

The engine pauses dispatch; persisted state ensures no progress is lost. Execution resumes when the bus recovers.

## Timeout with Lost Event

A missing completion event is handled by the step timeout, preventing a permanently stuck instance.

## Partial Side Effects

Handled by compensation, returning external systems to a consistent state.

---

# Out of Scope (MVP)

* Visual drag-and-drop workflow designer
* Cross-tenant shared workflows
* User-authored custom code steps
* Workflow marketplace

These align with the platform's broader Out-of-Scope and Future Extensions lists.

---

# Success Criteria

The Workflow Engine is considered successful if:

* Multi-agent workflows execute in the correct, deterministic order.
* No step is executed twice and no completed work is lost on failure.
* Failed steps retry and, when unrecoverable, trigger compensation or controlled failure.
* Both static templates and Orchestrator-planned dynamic workflows run with identical guarantees.
* Human approval is enforced for all sensitive actions.
* Every transition is logged and auditable.
* The engine scales horizontally to support the platform's concurrency and event-volume targets.

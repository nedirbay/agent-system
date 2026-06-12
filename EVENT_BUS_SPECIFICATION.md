# EVENT_BUS_SPECIFICATION.md

# Overview

This document defines the asynchronous communication between agents, workflow components, and other systems.

The Event Bus is the central communication layer of the system.

---

# Objectives

## OBJ-001

Ensure that agents operate independently of one another.

## OBJ-002

Enable horizontal scaling.

## OBJ-003

Avoid losing messages in failure scenarios.

## OBJ-004

Ensure that tasks are executed in order.

## OBJ-005

Support distributed workflows.

---

# Architecture

```text
Producer

↓

Event Bus

↓

Consumer

↓

Response Event

↓

Event Bus

↓

Interested Consumers
```

---

# Communication Principles

## CP-001

All agents must communicate through the Event Bus.

---

## CP-002

Direct agent-to-agent communication is forbidden.

---

## CP-003

Every message must be associated with a TaskId.

---

## CP-004

All events must be immutable.

---

## CP-005

Events must be retained for audit.

---

# Event Categories

## System Events

System states.

### Examples

* SystemStarted
* SystemStopped
* SystemError

---

## Task Events

Related to tasks.

### Examples

* TaskCreated
* TaskAssigned
* TaskStarted
* TaskCompleted
* TaskFailed

---

## Agent Events

Agent actions.

### Examples

* AgentStarted
* AgentCompleted
* AgentFailed

---

## Document Events

Documents.

### Examples

* DocumentUploaded
* DocumentParsed
* DocumentIndexed

---

## Knowledge Events

Knowledge base.

### Examples

* EmbeddingCreated
* KnowledgeIndexed

---

## Workflow Events

Workflow states.

### Examples

* WorkflowStarted
* WorkflowCompleted
* WorkflowFailed

---

## Security Events

Security.

### Examples

* LoginSuccess
* LoginFailed
* PermissionDenied

---

# Standard Event Structure

Every event must contain:

```json
{
  "eventId": "",
  "eventType": "",
  "taskId": "",
  "correlationId": "",
  "producer": "",
  "timestamp": "",
  "version": "",
  "payload": {}
}
```

---

# Field Definitions

## eventId

The unique identifier of the event.

---

## eventType

The type of the event.

---

## taskId

The associated task.

---

## correlationId

The link across a workflow.

---

## producer

The component that created the event.

---

## timestamp

The time it was created.

---

## version

The schema version.

---

## payload

The main data.

---

# Event Lifecycle

```text
Created

↓

Published

↓

Received

↓

Processed

↓

Acknowledged

↓

Archived
```

---

# Topics

## task.created

A new task.

---

## task.assigned

An agent was selected.

---

## task.started

The task started.

---

## task.completed

The task finished.

---

## task.failed

The task failed.

---

## agent.started

The agent started working.

---

## agent.completed

The agent finished.

---

## agent.failed

The agent ended with an error.

---

## document.uploaded

A document was uploaded.

---

## document.parsed

A document was processed.

---

## document.indexed

A document was indexed.

---

## workflow.started

The workflow started.

---

## workflow.completed

The workflow finished.

---

## workflow.failed

The workflow failed.

---

# Event Producers

## User Interface

Publishes:

* TaskCreated
* FileUploaded

---

## Orchestrator

Publishes:

* TaskAssigned
* WorkflowStarted
* WorkflowCompleted

---

## Document Agent

Publishes:

* DocumentParsed
* MetadataExtracted

---

## Knowledge Agent

Publishes:

* EmbeddingCreated
* KnowledgeIndexed

---

## Analysis Agent

Publishes:

* AnalysisCompleted

---

## QA Agent

Publishes:

* AnswerGenerated

---

## Report Agent

Publishes:

* ReportGenerated

---

## Execution Agent

Publishes:

* ExecutionStarted
* ExecutionCompleted

---

# Event Consumers

## Orchestrator

Consumes:

* TaskCreated
* AgentCompleted
* AgentFailed

---

## Memory Agent

Consumes:

* All completed events

---

## Audit Service

Consumes:

* All events

---

## Monitoring Service

Consumes:

* All events

---

# Retry Policy

## First Failure

Retry after 30 seconds.

---

## Second Failure

Retry after 2 minutes.

---

## Third Failure

Retry after 10 minutes.

---

## Fourth Failure

Move to Dead Letter Queue.

---

# Dead Letter Queue

## Purpose

Store messages that could not be processed.

---

## Retention

30 days.

---

## Actions

* Manual review
* Reprocess
* Discard

---

# Event Ordering

## Requirement

Event order must be preserved for a single task.

---

## Example

```text
TaskCreated

↓

TaskAssigned

↓

TaskStarted

↓

TaskCompleted
```

---

# Idempotency

## Requirement

When an event arrives multiple times, the result must not change.

---

## Strategy

Check by eventId.

---

# Delivery Guarantee

## Requirement

At-Least-Once Delivery

---

## Notes

The consumer must be idempotent.

---

# Event Versioning

## Rule

If the schema changes, a new version must be used.

---

## Example

```text
TaskCreated.v1

TaskCreated.v2
```

---

# Monitoring

## Metrics

* Published events
* Consumed events
* Failed events
* Retry count
* DLQ count

---

# Event Retention

## Operational Events

30 days.

---

## Audit Events

12 months.

---

## Security Events

24 months.

---

# Security

## Requirements

* Authentication
* Authorization
* Encryption in transit
* Encryption at rest

---

# Failure Scenarios

## Broker Failure

Messages must persist.

---

## Consumer Failure

Retry automatically.

---

## Agent Failure

Publish AgentFailed event.

---

## Workflow Failure

Publish WorkflowFailed event.

---

# Success Criteria

The Event Bus is considered successful if:

* Events are not lost
* Agents operate independently of one another
* Retry works
* The Dead Letter Queue works
* Workflow ordering is preserved
* Monitoring is fully operational
* 1,000,000+ events/day are supported

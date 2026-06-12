# DATABASE_DESIGN.md

# Overview

This document defines the logical data structure for the AI Multi-Agent Platform.

The system is composed of several storage layers:

* Relational Database
* Vector Database
* Cache Layer
* File Storage

---

# Storage Architecture

## Relational Database

Purpose:

* Users
* Tasks
* Agent executions
* Reports
* Audit logs
* Metadata

---

## Vector Database

Purpose:

* Embeddings
* Semantic search
* Knowledge retrieval

---

## Cache Layer

Purpose:

* Sessions
* Temporary context
* Active workflows

---

## File Storage

Purpose:

* Uploaded files
* Generated reports
* Screenshots
* Attachments

---

# Entity Relationship Overview

```text
Users
 ├── Sessions
 ├── Tasks
 ├── UploadedDocuments
 └── Reports

Tasks
 ├── TaskExecutions
 ├── AgentRuns
 ├── TaskMessages
 └── GeneratedReports

Documents
 ├── DocumentChunks
 ├── DocumentMetadata
 └── Embeddings

AgentRuns
 ├── AgentOutputs
 └── AgentLogs
```

---

# USERS

## Purpose

Store users.

### Fields

* Id
* Username
* Email
* FullName
* PasswordHash
* RoleId
* Status
* CreatedAt
* UpdatedAt

### Relationships

* One User -> Many Sessions
* One User -> Many Tasks
* One User -> Many Reports

---

# ROLES

## Purpose

Role-based permissions.

### Fields

* Id
* Name
* Description

---

# PERMISSIONS

## Purpose

List of permissions.

### Fields

* Id
* Name
* Code
* Description

---

# ROLE_PERMISSIONS

## Purpose

The link between roles and permissions.

### Fields

* RoleId
* PermissionId

---

# SESSIONS

## Purpose

Store active sessions.

### Fields

* Id
* UserId
* StartedAt
* LastActivityAt
* Status

---

# TASKS

## Purpose

Work items created by users.

### Fields

* Id
* UserId
* Title
* Description
* Priority
* Status
* CreatedAt
* UpdatedAt
* CompletedAt

### Status Values

* Pending
* Running
* Completed
* Failed
* Cancelled

---

# TASK_EXECUTIONS

## Purpose

Task execution history.

### Fields

* Id
* TaskId
* StartedAt
* FinishedAt
* Duration
* Status

---

# AGENTS

## Purpose

Registry of agents.

### Fields

* Id
* Name
* Type
* Description
* IsActive

---

# AGENT_RUNS

## Purpose

Record of agent executions.

### Fields

* Id
* TaskId
* AgentId
* StartedAt
* FinishedAt
* Status
* TokenUsage
* Cost

---

# AGENT_OUTPUTS

## Purpose

Agent results.

### Fields

* Id
* AgentRunId
* OutputType
* OutputContent
* CreatedAt

---

# AGENT_LOGS

## Purpose

Agent actions.

### Fields

* Id
* AgentRunId
* LogLevel
* Message
* CreatedAt

---

# DOCUMENTS

## Purpose

Uploaded documents.

### Fields

* Id
* UserId
* FileName
* OriginalName
* MimeType
* Size
* StoragePath
* Status
* UploadedAt

### Status

* Uploaded
* Processing
* Indexed
* Failed

---

# DOCUMENT_METADATA

## Purpose

Document metadata.

### Fields

* Id
* DocumentId
* Author
* Language
* Category
* Keywords
* CreatedDate

---

# DOCUMENT_CHUNKS

## Purpose

Document chunks.

### Fields

* Id
* DocumentId
* ChunkIndex
* Content
* TokenCount

### Notes

The embeddings of the chunks are stored in the Vector DB.

---

# DOCUMENT_TAGS

## Purpose

Tagging system.

### Fields

* Id
* Name

---

# DOCUMENT_TAG_RELATIONS

## Purpose

The link between documents and tags.

### Fields

* DocumentId
* TagId

---

# KNOWLEDGE_ITEMS

## Purpose

Elements of the knowledge base.

### Fields

* Id
* SourceType
* SourceId
* Title
* Content
* CreatedAt

---

# MEMORY_SESSIONS

## Purpose

Session memory.

### Fields

* Id
* SessionId
* Context
* CreatedAt

---

# MEMORY_LONG_TERM

## Purpose

Long-term memory.

### Fields

* Id
* MemoryType
* Content
* ImportanceScore
* CreatedAt

---

# MEMORY_REFERENCES

## Purpose

The link between memory and data.

### Fields

* Id
* MemoryId
* RelatedEntityType
* RelatedEntityId

---

# SEARCH_HISTORY

## Purpose

Search history.

### Fields

* Id
* UserId
* Query
* Timestamp

---

# QA_CONVERSATIONS

## Purpose

Chat sessions.

### Fields

* Id
* UserId
* StartedAt

---

# QA_MESSAGES

## Purpose

Question-and-answer history.

### Fields

* Id
* ConversationId
* SenderType
* Content
* Timestamp

---

# REPORTS

## Purpose

Generated reports.

### Fields

* Id
* UserId
* TaskId
* Name
* Format
* StoragePath
* CreatedAt

---

# REPORT_SECTIONS

## Purpose

Report sections.

### Fields

* Id
* ReportId
* Title
* Content

---

# WORKFLOWS

## Purpose

Workflow templates.

### Fields

* Id
* Name
* Description
* IsActive

---

# WORKFLOW_STEPS

## Purpose

Workflow steps.

### Fields

* Id
* WorkflowId
* StepOrder
* AgentType
* Configuration

---

# NOTIFICATIONS

## Purpose

User notifications.

### Fields

* Id
* UserId
* Title
* Message
* IsRead
* CreatedAt

---

# AUDIT_LOGS

## Purpose

Audit records.

### Fields

* Id
* UserId
* EntityType
* EntityId
* Action
* Details
* Timestamp

---

# SYSTEM_EVENTS

## Purpose

Event Bus records.

### Fields

* Id
* EventType
* Payload
* Status
* CreatedAt

---

# FILE_ATTACHMENTS

## Purpose

Additional files.

### Fields

* Id
* EntityType
* EntityId
* FilePath
* UploadedAt

---

# Vector Database Collections

## documents

Document embeddings.

---

## knowledge

Knowledge base embeddings.

---

## conversations

Conversation embeddings.

---

## reports

Report embeddings.

---

# Cache Keys

## Active Sessions

Active user sessions.

---

## Active Tasks

Running tasks.

---

## Agent State

Agent states.

---

## Workflow State

Workflow states.

---

# Retention Policy

## Audit Logs

12 months

---

## Agent Logs

6 months

---

## Session Memory

30 days

---

## Search History

12 months

---

## Reports

Not limited

---

# Future Extensions

* Multi-tenancy
* Organization hierarchy
* Team workspaces
* API keys
* Billing
* Usage tracking
* Knowledge graph
* Fine tuning datasets
* Agent marketplace

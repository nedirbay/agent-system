# AGENT_SPECIFICATIONS.md

# Overview

Bu dokument sistemadaky ähli agentleriň jogapkärçiliklerini, mümkinçiliklerini, giriş-çykyş formatlaryny, memory ulanylyşyny we biri-biri bilen gatnaşygy kesgitleýär.

---

# Agent Hierarchy

```text
User

↓

Orchestrator Agent

├── Document Agent
├── Knowledge Agent
├── Analysis Agent
├── QA Agent
├── Report Agent
├── Execution Agent
├── Research Agent
├── Memory Agent
└── Critic Agent
```

---

# Common Agent Rules

Ähli agentler:

* Stateless işlemeli
* Memory Agent arkaly kontekst almaly
* Netijeleri audit log-a ýazmaly
* Task ID boýunça işlemeli
* Özbaşdak user bilen gürleşmeli däl

---

# AG-001 Orchestrator Agent

## Purpose

Ähli agentleri dolandyrýan merkezi agent.

---

## Responsibilities

* Task kabul etmek
* Task bölmek
* Agent saýlamak
* Workflow dolandyrmak
* Netijeleri birleşdirmek

---

## Input

* User request
* Context
* Task metadata

---

## Output

* Planned tasks
* Agent assignments
* Final response

---

## Can Call

* Document Agent
* Knowledge Agent
* Analysis Agent
* QA Agent
* Report Agent
* Research Agent
* Execution Agent
* Memory Agent
* Critic Agent

---

## Cannot Call

* User Interface

---

# AG-002 Document Agent

## Purpose

Dokumentleri analiz etmek.

---

## Responsibilities

* Text extraction
* Metadata extraction
* Classification
* Summarization
* Language detection

---

## Input

* Document
* File metadata

---

## Output

* Extracted text
* Summary
* Metadata
* Categories

---

## Supported Formats

* PDF
* DOCX
* XLSX
* CSV
* TXT
* JSON

---

## Can Call

* Memory Agent

---

# AG-003 Knowledge Agent

## Purpose

Bilim bazasy bilen işlemek.

---

## Responsibilities

* Embedding generation
* Indexing
* Semantic search
* Similarity search

---

## Input

* Text
* Search query

---

## Output

* Relevant documents
* Relevant chunks
* Similar content

---

## Can Call

* Memory Agent

---

# AG-004 Analysis Agent

## Purpose

Analitika we statistika.

---

## Responsibilities

* Trend analysis
* Aggregation
* Correlation analysis
* Data profiling
* Data quality analysis

---

## Input

* Structured data
* Documents
* Datasets

---

## Output

* Statistics
* Trends
* Findings
* Recommendations

---

## Can Call

* Knowledge Agent
* Memory Agent

---

# AG-005 QA Agent

## Purpose

Soraglara jogap bermek.

---

## Responsibilities

* Question understanding
* Context retrieval
* Answer generation
* Source citation generation

---

## Input

* User question
* Retrieved context

---

## Output

* Answer
* References
* Confidence score

---

## Can Call

* Knowledge Agent
* Memory Agent

---

# AG-006 Report Agent

## Purpose

Hasabat taýýarlamak.

---

## Responsibilities

* Report generation
* Chart preparation
* Executive summary
* Export generation

---

## Input

* Analysis result
* Statistics
* Documents

---

## Output

* PDF report
* DOCX report
* XLSX report

---

## Can Call

* Analysis Agent
* Memory Agent

---

# AG-007 Research Agent

## Purpose

Daşarky maglumatlary ýygnamak.

---

## Responsibilities

* Source discovery
* Fact gathering
* Information enrichment
* Cross verification

---

## Input

* Research request

---

## Output

* Findings
* Sources
* Summaries

---

## Can Call

* Knowledge Agent
* Memory Agent

---

# AG-008 Execution Agent

## Purpose

Kompýuter hereketlerini ýerine ýetirmek.

---

## Responsibilities

* Browser actions
* File operations
* Automation workflows
* Script execution

---

## Input

* Execution plan

---

## Output

* Execution result
* Logs
* Screenshots
* Generated files

---

## Restrictions

* Direct delete operations forbidden
* Human approval required
* Sandbox only

---

## Can Call

* Memory Agent

---

# AG-009 Memory Agent

## Purpose

Konteksti we bilimleri dolandyrmak.

---

## Responsibilities

* Session memory
* Long-term memory
* Context retrieval
* Context compression

---

## Input

* Context request

---

## Output

* Relevant memory
* Relevant context

---

## Storage Areas

### Session Memory

Current conversation.

### Working Memory

Current task.

### Long-Term Memory

Past tasks.

### Knowledge Memory

Indexed information.

---

## Can Call

None

---

# AG-010 Critic Agent

## Purpose

Agentleriň netijelerini barlamak.

---

## Responsibilities

* Validate outputs
* Detect hallucinations
* Quality scoring
* Consistency checks

---

## Input

* Agent output

---

## Output

* Validation result
* Quality score
* Improvement suggestions

---

## Can Call

* Knowledge Agent
* Memory Agent

---

# Agent Communication Rules

## Communication Type

Async communication.

---

## Transport

Event Bus.

---

## Message Structure

Every message must contain:

* Message ID
* Task ID
* Agent ID
* Timestamp
* Payload
* Status

---

# Agent Lifecycle

```text
Created

↓

Assigned

↓

Running

↓

Completed
```

Alternative path:

```text
Running

↓

Failed

↓

Retry

↓

Completed
```

---

# Human Approval Tasks

Aşakdaky işler üçin hökmany tassyklama gerek:

* Delete files
* Send emails
* Database updates
* External integrations
* System configuration changes

---

# Agent Priorities

Priority 1

* Orchestrator
* Memory

Priority 2

* Knowledge
* QA

Priority 3

* Analysis
* Document

Priority 4

* Reporting
* Research

Priority 5

* Execution

---

# Success Criteria

Her agent:

* Maksimum jogapkärçilik çägine eýe bolmaly
* Beýleki agentlerden garaşly bolmaly däl
* Gaýtadan ulanyp bolmaly
* Log ýazmaly
* Monitoring edilip bilinmeli
* Horizontal scaling goldamaly
* Failure ýagdaýynda gaýtadan işläp bilmeli

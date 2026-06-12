# LLM_AND_RAG_STRATEGY.md

# Overview

This document defines how the platform uses Large Language Models and how Retrieval-Augmented Generation (RAG) is implemented. It is the "intelligence" layer that every agent in `AGENT_SPECIFICATIONS.md` depends on.

It specifies model selection and routing, the embedding and chunking pipeline, the retrieval and grounding strategy, prompt structure, cost and token control, evaluation, and safeguards against hallucination. The concrete products were chosen in `TECH_STACK_DECISION.md` (ADR-008, ADR-009); this document defines how they are used.

---

# Objectives

## OBJ-001

Produce grounded, citable answers from the knowledge base (`AIR-007`, `FR-007`).

## OBJ-002

Match the right model to each task to balance quality, latency, and cost.

## OBJ-003

Keep the model layer swappable so additional providers can be added (`AIR-006`).

## OBJ-004

Meet the latency budgets PER-001 (search ≤ 5 s) and PER-002 (QA ≤ 15 s).

## OBJ-005

Minimize hallucination through retrieval grounding, citation enforcement, and Critic-Agent validation.

---

# Model Provider Abstraction

## MP-001 Provider Interface

All model calls go through a single internal `LLMProvider` interface (`complete`, `stream`, `tool_call`). No agent calls a vendor SDK directly. This satisfies `AIR-006` (multi-model) and makes the provider a configuration choice.

## MP-002 Default Provider

The default provider is the Anthropic Claude family. The provider layer handles auth, retries, timeouts, token accounting, and structured tool-use.

## MP-003 Secondary Providers

Additional providers (other hosted models or a self-hosted open-weight model) can be registered behind the same interface for redundancy, cost, or data-residency reasons. Routing rules (below) decide which provider/model handles a given step.

---

# Model Routing

Each agent step declares a *task class*; the router maps the class to a model tier. This keeps premium models for hard reasoning and cheap models for high-volume work (OBJ-002).

| Task class | Used by | Default model | Why |
| --- | --- | --- | --- |
| Deep reasoning / planning | Orchestrator, Analysis, Critic | `claude-opus-4-8` | Multi-step decomposition, validation, correlation. |
| General generation | QA, Document, Report, Research | `claude-sonnet-4-6` | Strong quality at high volume and good latency. |
| Lightweight / high-throughput | Routing, classification, language detection, metadata tagging | `claude-haiku-4-5-20251001` | Cheap, fast, simple decisions. |
| Tool / computer use | Execution Agent | `claude-sonnet-4-6` (escalate to `claude-opus-4-8`) | Native tool-use; escalate for complex action plans. |

## MR-001 Escalation

If the Critic Agent rejects an output, the step may be retried one tier higher (e.g. Sonnet → Opus) before failing, within the retry budget.

## MR-002 Overrides

Routing is data-driven (config, not code) so the mapping can be tuned per deployment without redeploying agents.

---

# Embedding Pipeline

## EM-001 Model

Embeddings use the model chosen in ADR-009 (Voyage AI for cloud-allowed installs, BGE-M3 for strict on-prem). The model and its vector dimension are **pinned per deployment** and recorded in config.

## EM-002 Dimension Consistency

A vector collection may contain only vectors from one embedding model/dimension. Changing the embedding model requires a full re-index; mixing is forbidden.

## EM-003 What Gets Embedded

* Document chunks (`documents` collection)
* Curated knowledge items (`knowledge` collection)
* QA conversation turns (`conversations` collection)
* Report sections (`reports` collection)

## EM-004 Caching

Embeddings are cached by content hash so identical text is never re-embedded. Query embeddings are cached briefly in Redis to speed up repeated searches.

---

# Chunking Strategy

Chunk quality is the single biggest driver of RAG quality (Roadmap Task 8).

## CH-001 Default Strategy

Structure-aware chunking: split on document structure (headings, paragraphs, table rows) using the parser output, then pack into token-bounded chunks.

## CH-002 Parameters

* Target chunk size: ~512 tokens
* Overlap: ~64 tokens (preserves context across boundaries)
* Hard max: 1,024 tokens

These are configuration values, tunable per corpus.

## CH-003 Metadata on Chunks

Every chunk stores back-references for citation: `documentId`, `chunkIndex`, page/section, and `tokenCount` (matching `DOCUMENT_CHUNKS`). This is what lets answers cite a source and page.

## CH-004 Tables & Code

Tabular and code content is kept intact within a chunk where possible to avoid splitting rows or statements.

---

# Retrieval Strategy

## RT-001 Hybrid Retrieval

Retrieval combines **dense** (vector similarity) and **sparse** (keyword/BM25) search, merged by score. Hybrid retrieval outperforms pure vector search on exact terms, names, and codes.

## RT-002 Filtering

Retrieval applies metadata filters (category, tag, language, and — in future multi-tenancy — tenant) before/with the vector query, using the vector store's payload filtering.

## RT-003 Top-K and Re-ranking

* Initial retrieval: top-K (default 20) candidates.
* Re-ranking: a cross-encoder re-ranker narrows to the top-N (default 5–8) most relevant chunks passed to the model.

## RT-004 Context Assembly

Selected chunks are assembled into the prompt with their source labels, deduplicated, and truncated to a token budget that leaves room for the answer within the model's context window.

---

# Grounding & Prompt Structure

## PR-001 Grounded Answering Contract

QA answers must be grounded in retrieved context. The QA Agent prompt instructs the model to:

* Answer **only** from the provided context.
* Cite the source chunk(s) for each claim.
* Say "I don't have enough information" when the context does not support an answer — never invent facts.

## PR-002 Prompt Layout

A standard prompt is assembled as:

```text
[System]      role, rules, grounding contract, output format
[Context]     retrieved chunks, each tagged with a source id
[Memory]      relevant session / long-term context (from Memory Agent)
[User]        the question or task
```

## PR-003 Structured Output

When a step needs machine-readable output (e.g. classification, extracted metadata, decision-step results), the model is called with tool-use / JSON schema so the result is parseable, not free text.

## PR-004 Citations

The QA response carries `references` mapping each cited claim back to `documentId` + `chunkId` + page, exactly as returned by `POST /qa/.../messages` in `API_SPECIFICATION.md`.

---

# Memory Integration

## ME-001

The Memory Agent (AG-009) supplies session, working, long-term, and knowledge memory into the `[Memory]` prompt block.

## ME-002 Context Compression

When accumulated context exceeds the token budget, the Memory Agent compresses older turns into summaries (its "context compression" responsibility) so long conversations stay within the window.

---

# Token & Cost Control

## TC-001 Budgets

Each task class has a maximum input + output token budget. The context assembler enforces it by trimming the lowest-ranked chunks first.

## TC-002 Accounting

Every model call records token usage and cost into `AGENT_RUNS` (`TokenUsage`, `Cost`). This feeds the dashboard and future usage/billing extensions.

## TC-003 Prompt Caching

Stable prompt prefixes (system instructions, frequently reused context) use provider prompt caching to cut cost and latency on repeated calls.

## TC-004 Cheapest-Capable Routing

The router always selects the cheapest model tier that can meet the quality bar for the task class (OBJ-002), escalating only on validation failure (MR-001).

---

# Hallucination Safeguards

## HS-001 Retrieval Grounding

No-context or weak-context queries return an explicit "insufficient information" answer rather than an unsupported one (PR-001).

## HS-002 Critic Validation

The Critic Agent (AG-010) checks answers for hallucination, consistency, and citation validity before the workflow completes (Validation Step in the Workflow Engine).

## HS-003 Confidence Score

QA answers include a confidence score; low-confidence answers are flagged in the UI and may trigger a retrieval retry or escalation.

## HS-004 Source Verification

Citations are validated to point at chunks that actually exist and were in the retrieved context — fabricated citations are rejected.

---

# Latency Strategy

## LT-001 Streaming

QA responses stream token-by-token (SSE) so perceived latency is low even when full generation approaches the PER-002 budget.

## LT-002 Parallel Retrieval

Dense and sparse retrieval run in parallel; embedding of the query and metadata-filter construction overlap.

## LT-003 Model Tiering for Speed

Latency-sensitive interactive steps prefer faster tiers; heavy reasoning is reserved for steps where quality dominates.

---

# Evaluation

## EV-001 Retrieval Metrics

Track recall@k and precision of retrieval against a labeled question/answer set per corpus.

## EV-002 Answer Quality

Track groundedness (are claims supported by cited context), citation accuracy, and answer correctness via periodic LLM-as-judge plus human spot-checks.

## EV-003 Regression Gate

Changes to chunking, embedding model, retrieval parameters, or prompts must be evaluated against the benchmark set before rollout, since they affect every answer.

## EV-004 Operational Metrics

Per task class: average tokens, cost, latency, retry rate, and Critic rejection rate — surfaced on the dashboard.

---

# Failure Handling

## FH-001 Provider Outage

On provider failure the LLMProvider layer retries with backoff, then fails over to a registered secondary provider if configured (`SERVICE_UNAVAILABLE` surfaces only if all fail).

## FH-002 Timeout

Model calls respect per-step timeouts from the Workflow Engine; a timeout is treated as a step failure and follows the retry policy.

## FH-003 Embedding/Vector Outage

If retrieval is unavailable, QA returns a clear degraded-mode error rather than an ungrounded answer (HS-001).

---

# Out of Scope (MVP)

* Fine-tuning custom models (listed as a future extension).
* Self-hosted LLM as the primary provider (secondary only, optional).
* Knowledge-graph-augmented retrieval (future extension).

---

# Success Criteria

The LLM/RAG layer is successful if:

* QA answers are grounded and carry valid citations to source documents.
* The "insufficient information" path fires instead of hallucinating when context is missing.
* Model routing keeps cost down while meeting quality and the PER-001/PER-002 latency budgets.
* The provider and embedding model are swappable via configuration (`AIR-006`, on-prem support).
* Retrieval and answer quality are measured and gated against regression.

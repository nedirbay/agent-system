"""Agent registry and model-routing tiers (AGENT_SPECIFICATIONS / MR-001..MR-002).

The registry is the single source of truth for which agent types exist, what
each one does, and which model tier serves it. The Orchestrator plans against
these types and the router validates planned steps against this list.
"""
from __future__ import annotations

from dataclasses import dataclass, field

# --- Model tiers (LLM_AND_RAG_STRATEGY Model Routing table) ---
TIER_REASONING = "reasoning"  # deep decomposition / validation / correlation
TIER_GENERAL = "general"  # high-volume generation
TIER_LIGHT = "light"  # cheap, fast, simple decisions


@dataclass(frozen=True)
class AgentSpec:
    type: str
    description: str
    task_class: str
    tier: str
    capabilities: tuple[str, ...] = field(default_factory=tuple)
    # Sensitive agents require a Human Approval step before acting (HA-003).
    requires_approval: bool = False


# Order roughly follows AGENT_SPECIFICATIONS AG-002..AG-010.
AGENT_REGISTRY: dict[str, AgentSpec] = {
    "DocumentAgent": AgentSpec(
        type="DocumentAgent",
        description="Extract text, metadata, classification and summaries from documents.",
        task_class="general generation",
        tier=TIER_GENERAL,
        capabilities=("text_extraction", "metadata", "classification", "summarization"),
    ),
    "KnowledgeAgent": AgentSpec(
        type="KnowledgeAgent",
        description="Chunk, embed and index content; perform semantic retrieval.",
        task_class="general generation",
        tier=TIER_GENERAL,
        capabilities=("chunking", "embedding", "indexing", "retrieval", "search"),
    ),
    "AnalysisAgent": AgentSpec(
        type="AnalysisAgent",
        description="Correlate and reason over data to produce insights.",
        task_class="deep reasoning",
        tier=TIER_REASONING,
        capabilities=("analysis", "correlation", "reasoning", "comparison"),
    ),
    "QAAgent": AgentSpec(
        type="QAAgent",
        description="Answer questions grounded in retrieved context, with citations.",
        task_class="general generation",
        tier=TIER_GENERAL,
        capabilities=("question_answering", "grounding", "citation"),
    ),
    "ReportAgent": AgentSpec(
        type="ReportAgent",
        description="Generate reports/exports (PDF/DOCX/XLSX) from prior outputs.",
        task_class="general generation",
        tier=TIER_GENERAL,
        capabilities=("report_generation", "export", "formatting"),
    ),
    "ResearchAgent": AgentSpec(
        type="ResearchAgent",
        description="Gather and synthesise information from external sources.",
        task_class="general generation",
        tier=TIER_GENERAL,
        capabilities=("research", "web_search", "synthesis"),
    ),
    "ExecutionAgent": AgentSpec(
        type="ExecutionAgent",
        description="Perform actions / computer & browser use. Sensitive: needs approval.",
        task_class="tool use",
        tier=TIER_GENERAL,
        capabilities=("computer_use", "browser", "file_ops", "external_integration"),
        requires_approval=True,
    ),
    "MemoryAgent": AgentSpec(
        type="MemoryAgent",
        description="Retrieve and store session / long-term context for other agents.",
        task_class="lightweight",
        tier=TIER_LIGHT,
        capabilities=("session_memory", "long_term_memory", "context"),
    ),
    "CriticAgent": AgentSpec(
        type="CriticAgent",
        description="Validate outputs for hallucination, consistency and citations.",
        task_class="deep reasoning",
        tier=TIER_REASONING,
        capabilities=("validation", "hallucination_check", "confidence"),
    ),
}

# Agents the Orchestrator may plan into a workflow (it cannot route to itself).
PLANNABLE_AGENTS: tuple[str, ...] = tuple(AGENT_REGISTRY.keys())


def get_spec(agent_type: str) -> AgentSpec | None:
    return AGENT_REGISTRY.get(agent_type)


def registry_summary() -> str:
    """Compact catalogue string for grounding the planner prompt."""
    return "\n".join(
        f"- {s.type}: {s.description}" for s in AGENT_REGISTRY.values()
    )

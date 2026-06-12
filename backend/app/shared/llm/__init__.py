"""Shared LLM provider layer (MP-001)."""
from __future__ import annotations

from app.core.config import get_settings
from app.shared.llm.ollama import OllamaLLMProvider
from app.shared.llm.provider import (
    ChatMessage,
    CompletionResult,
    LLMProvider,
)

__all__ = [
    "ChatMessage",
    "CompletionResult",
    "LLMProvider",
    "OllamaLLMProvider",
    "get_llm_provider",
]


def get_llm_provider() -> LLMProvider:
    """Factory: returns the configured LLM provider (default: Ollama)."""
    provider = get_settings().llm_provider
    if provider == "ollama":
        return OllamaLLMProvider()
    raise ValueError(f"Unknown llm_provider: {provider}")

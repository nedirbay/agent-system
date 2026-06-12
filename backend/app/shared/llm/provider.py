"""LLM provider port (MP-001).

Every model call in the platform goes through this single interface; no service
or agent talks to a vendor/runtime SDK directly. This makes the provider a
configuration choice (AIR-006) and keeps the model layer swappable.
"""
from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass


@dataclass
class ChatMessage:
    role: str  # "system" | "user" | "assistant"
    content: str


@dataclass
class CompletionResult:
    text: str
    model: str
    prompt_tokens: int = 0
    completion_tokens: int = 0


class LLMProvider(ABC):
    @abstractmethod
    async def complete(
        self,
        messages: list[ChatMessage],
        *,
        model: str | None = None,
        temperature: float = 0.2,
        max_tokens: int | None = None,
    ) -> CompletionResult:
        """Return a chat completion for the given messages."""

    @abstractmethod
    async def complete_json(
        self,
        messages: list[ChatMessage],
        *,
        model: str | None = None,
        temperature: float = 0.0,
        schema: dict | None = None,
    ) -> dict:
        """Return a parsed JSON object (PR-003 structured output)."""

"""Session memory port (Roadmap Task 18 / AG-009 "Session Memory").

Session memory holds the *current conversation* — short-lived, fast, and keyed
by a session id. Per TECH_STACK_DECISION it lives in Redis with a 30-day TTL
(DATABASE_DESIGN retention), so the store is abstracted behind this port and the
application layer never depends on the Redis client directly.
"""
from __future__ import annotations

import uuid
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime, timezone


def _now() -> datetime:
    return datetime.now(timezone.utc)


@dataclass(frozen=True)
class SessionTurn:
    """One conversation turn kept in session memory."""

    role: str  # "user" | "assistant" | "system" | "tool"
    content: str
    created_at: datetime = field(default_factory=_now)


class SessionMemoryStore(ABC):
    """Persistence port for per-session conversation turns + running summary."""

    @abstractmethod
    async def append(self, session_id: str, turn: SessionTurn) -> None:
        """Append a turn to the session's ordered history."""

    @abstractmethod
    async def turns(self, session_id: str) -> list[SessionTurn]:
        """Return the session's turns in chronological order."""

    @abstractmethod
    async def replace_turns(self, session_id: str, turns: list[SessionTurn]) -> None:
        """Overwrite the session's turns (used by compression)."""

    @abstractmethod
    async def get_summary(self, session_id: str) -> str | None:
        """Return the running summary of compressed older turns, if any."""

    @abstractmethod
    async def set_summary(self, session_id: str, summary: str) -> None:
        """Store/replace the running summary."""

    @abstractmethod
    async def clear(self, session_id: str) -> None:
        """Forget everything for a session."""

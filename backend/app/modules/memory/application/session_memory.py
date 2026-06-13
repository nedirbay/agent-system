"""Session memory service (Roadmap Task 18 / AG-009).

Records conversation turns and assembles the session portion of the `[Memory]`
prompt block. Implements context compression (ME-002): once a session grows past
`session_memory_max_turns`, the oldest turns are folded into a running summary so
long conversations stay within the context window while recent turns survive
verbatim.
"""
from __future__ import annotations

from dataclasses import dataclass

from app.core.config import get_settings
from app.core.exceptions import AppError
from app.modules.memory.domain.session import SessionMemoryStore, SessionTurn

_VALID_ROLES = {"user", "assistant", "system", "tool"}
_SUMMARY_SNIPPET = 160


@dataclass(frozen=True)
class SessionContext:
    """Assembled session memory for one session."""

    session_id: str
    summary: str | None
    turns: list[SessionTurn]
    text: str


class SessionMemoryService:
    def __init__(
        self,
        store: SessionMemoryStore,
        *,
        max_turns: int | None = None,
        recent_turns: int | None = None,
    ) -> None:
        settings = get_settings()
        self._store = store
        self._max_turns = max_turns or settings.session_memory_max_turns
        self._recent_turns = recent_turns or settings.session_memory_recent_turns

    async def append_turn(self, session_id: str, role: str, content: str) -> SessionContext:
        session_id = (session_id or "").strip()
        if not session_id:
            raise AppError("session_id is required")
        role = (role or "").strip().lower()
        if role not in _VALID_ROLES:
            raise AppError(f"role must be one of {sorted(_VALID_ROLES)}")
        if not (content or "").strip():
            raise AppError("content must not be empty")

        await self._store.append(session_id, SessionTurn(role=role, content=content.strip()))
        await self._maybe_compress(session_id)
        return await self.get_context(session_id)

    async def get_context(self, session_id: str) -> SessionContext:
        session_id = (session_id or "").strip()
        if not session_id:
            raise AppError("session_id is required")
        summary = await self._store.get_summary(session_id)
        turns = await self._store.turns(session_id)
        return SessionContext(
            session_id=session_id,
            summary=summary,
            turns=turns,
            text=self._render(summary, turns),
        )

    async def clear(self, session_id: str) -> None:
        session_id = (session_id or "").strip()
        if not session_id:
            raise AppError("session_id is required")
        await self._store.clear(session_id)

    async def _maybe_compress(self, session_id: str) -> None:
        """ME-002: fold older turns into the running summary."""
        turns = await self._store.turns(session_id)
        if len(turns) <= self._max_turns:
            return
        keep = turns[-self._recent_turns :] if self._recent_turns else []
        older = turns[: len(turns) - len(keep)]
        if not older:
            return
        existing = await self._store.get_summary(session_id)
        merged = self._summarize(older, existing)
        await self._store.set_summary(session_id, merged)
        await self._store.replace_turns(session_id, keep)

    @staticmethod
    def _summarize(turns: list[SessionTurn], existing: str | None) -> str:
        lines: list[str] = []
        if existing:
            lines.append(existing.strip())
        for turn in turns:
            snippet = turn.content.strip().replace("\n", " ")
            if len(snippet) > _SUMMARY_SNIPPET:
                snippet = snippet[: _SUMMARY_SNIPPET - 1].rstrip() + "…"
            lines.append(f"- {turn.role}: {snippet}")
        return "\n".join(lines)

    @staticmethod
    def _render(summary: str | None, turns: list[SessionTurn]) -> str:
        parts: list[str] = []
        if summary:
            parts.append(f"Earlier conversation summary:\n{summary}")
        if turns:
            convo = "\n".join(f"{t.role}: {t.content}" for t in turns)
            parts.append(f"Recent turns:\n{convo}")
        return "\n\n".join(parts)

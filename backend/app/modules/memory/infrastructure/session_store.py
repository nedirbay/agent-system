"""Session-memory store adapters (Roadmap Task 18).

`RedisSessionMemoryStore` is the production adapter: turns are pushed onto a
Redis list and the running summary into a sibling key, both refreshed to the
configured TTL on every write (30-day retention). `InMemorySessionMemoryStore`
is a process-local fallback used in tests and when Redis is unavailable
(graceful degradation, FH-001).
"""
from __future__ import annotations

import json
from datetime import datetime
from typing import TYPE_CHECKING

from app.core.config import get_settings
from app.modules.memory.domain.session import SessionMemoryStore, SessionTurn

if TYPE_CHECKING:  # pragma: no cover
    from redis.asyncio import Redis


def _turn_to_json(turn: SessionTurn) -> str:
    return json.dumps(
        {
            "role": turn.role,
            "content": turn.content,
            "created_at": turn.created_at.isoformat(),
        }
    )


def _turn_from_json(raw: str) -> SessionTurn:
    data = json.loads(raw)
    return SessionTurn(
        role=data["role"],
        content=data["content"],
        created_at=datetime.fromisoformat(data["created_at"]),
    )


class RedisSessionMemoryStore(SessionMemoryStore):
    def __init__(self, redis: "Redis", *, ttl_seconds: int | None = None) -> None:
        self._redis = redis
        self._ttl = ttl_seconds or get_settings().session_memory_ttl_seconds

    @staticmethod
    def _turns_key(session_id: str) -> str:
        return f"session:{session_id}:turns"

    @staticmethod
    def _summary_key(session_id: str) -> str:
        return f"session:{session_id}:summary"

    async def append(self, session_id: str, turn: SessionTurn) -> None:
        key = self._turns_key(session_id)
        await self._redis.rpush(key, _turn_to_json(turn))
        await self._redis.expire(key, self._ttl)

    async def turns(self, session_id: str) -> list[SessionTurn]:
        raw = await self._redis.lrange(self._turns_key(session_id), 0, -1)
        return [_turn_from_json(r) for r in raw]

    async def replace_turns(self, session_id: str, turns: list[SessionTurn]) -> None:
        key = self._turns_key(session_id)
        async with self._redis.pipeline(transaction=True) as pipe:
            pipe.delete(key)
            if turns:
                pipe.rpush(key, *[_turn_to_json(t) for t in turns])
                pipe.expire(key, self._ttl)
            await pipe.execute()

    async def get_summary(self, session_id: str) -> str | None:
        return await self._redis.get(self._summary_key(session_id))

    async def set_summary(self, session_id: str, summary: str) -> None:
        key = self._summary_key(session_id)
        await self._redis.set(key, summary, ex=self._ttl)

    async def clear(self, session_id: str) -> None:
        await self._redis.delete(
            self._turns_key(session_id), self._summary_key(session_id)
        )


class InMemorySessionMemoryStore(SessionMemoryStore):
    """Process-local store for tests / Redis-down fallback."""

    def __init__(self) -> None:
        self._turns: dict[str, list[SessionTurn]] = {}
        self._summaries: dict[str, str] = {}

    async def append(self, session_id: str, turn: SessionTurn) -> None:
        self._turns.setdefault(session_id, []).append(turn)

    async def turns(self, session_id: str) -> list[SessionTurn]:
        return list(self._turns.get(session_id, []))

    async def replace_turns(self, session_id: str, turns: list[SessionTurn]) -> None:
        self._turns[session_id] = list(turns)

    async def get_summary(self, session_id: str) -> str | None:
        return self._summaries.get(session_id)

    async def set_summary(self, session_id: str, summary: str) -> None:
        self._summaries[session_id] = summary

    async def clear(self, session_id: str) -> None:
        self._turns.pop(session_id, None)
        self._summaries.pop(session_id, None)

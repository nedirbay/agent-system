"""Structure-aware, token-bounded chunker (CH-001..CH-004).

Splits text on document structure (blank-line-separated blocks: paragraphs,
table rows, code blocks) then greedily packs blocks into chunks near a target
token budget, with overlap carried across boundaries to preserve context. A
block larger than the hard max is split on sentence/line boundaries; tables and
code are kept intact whenever they fit (CH-004).

Tokens are estimated as ``len(text) / chars_per_token`` — good enough for budget
control without pulling in a tokenizer; the divisor is configurable.
"""
from __future__ import annotations

import re

from app.core.config import get_settings
from app.modules.knowledge.domain.chunk import ChunkDraft, Chunker

# Blank line(s) delimit structural blocks.
_BLOCK_SPLIT = re.compile(r"\n\s*\n")
# Sentence-ish boundaries for over-long prose blocks.
_SENTENCE_SPLIT = re.compile(r"(?<=[.!?])\s+")


class StructureAwareChunker(Chunker):
    def __init__(
        self,
        *,
        target_tokens: int | None = None,
        overlap_tokens: int | None = None,
        max_tokens: int | None = None,
        chars_per_token: int | None = None,
    ) -> None:
        settings = get_settings()
        cpt = chars_per_token or settings.chunk_chars_per_token
        self._chars_per_token = max(1, cpt)
        self._target = (target_tokens or settings.chunk_target_tokens) * self._chars_per_token
        self._overlap = (overlap_tokens or settings.chunk_overlap_tokens) * self._chars_per_token
        self._max = (max_tokens or settings.chunk_max_tokens) * self._chars_per_token

    def _tokens(self, text: str) -> int:
        return max(1, round(len(text) / self._chars_per_token))

    def split(self, text: str) -> list[ChunkDraft]:
        if not text or not text.strip():
            return []

        blocks = self._blocks(text)
        chunks: list[str] = []
        current = ""

        for block in blocks:
            if not current:
                current = block
            elif len(current) + 2 + len(block) <= self._target:
                current = f"{current}\n\n{block}"
            else:
                chunks.append(current)
                # Start the next chunk with a trailing slice of the previous one
                # so context spans the boundary (CH-002 overlap).
                tail = self._tail(current)
                current = f"{tail}\n\n{block}" if tail else block

        if current:
            chunks.append(current)

        return [
            ChunkDraft(chunk_index=i, content=c.strip(), token_count=self._tokens(c.strip()))
            for i, c in enumerate(chunks)
            if c.strip()
        ]

    def _blocks(self, text: str) -> list[str]:
        """Structural blocks, with any over-long block hard-split to fit ``_max``."""
        blocks: list[str] = []
        for raw in _BLOCK_SPLIT.split(text):
            block = raw.strip()
            if not block:
                continue
            if len(block) <= self._max:
                blocks.append(block)
            else:
                blocks.extend(self._hard_split(block))
        return blocks

    def _hard_split(self, block: str) -> list[str]:
        """Split a block too big for one chunk on sentence then word boundaries."""
        units = _SENTENCE_SPLIT.split(block)
        pieces: list[str] = []
        buf = ""
        for unit in units:
            unit = unit.strip()
            if not unit:
                continue
            if len(unit) > self._max:
                # A single sentence still too long — fall back to word packing.
                if buf:
                    pieces.append(buf)
                    buf = ""
                pieces.extend(self._pack_words(unit))
                continue
            if not buf:
                buf = unit
            elif len(buf) + 1 + len(unit) <= self._max:
                buf = f"{buf} {unit}"
            else:
                pieces.append(buf)
                buf = unit
        if buf:
            pieces.append(buf)
        return pieces

    def _pack_words(self, text: str) -> list[str]:
        pieces: list[str] = []
        buf = ""
        for word in text.split():
            if not buf:
                buf = word
            elif len(buf) + 1 + len(word) <= self._max:
                buf = f"{buf} {word}"
            else:
                pieces.append(buf)
                buf = word
        if buf:
            pieces.append(buf)
        return pieces

    def _tail(self, chunk: str) -> str:
        """Last ``_overlap`` characters of a chunk, snapped to a word boundary."""
        if self._overlap <= 0 or len(chunk) <= self._overlap:
            return chunk if self._overlap > 0 else ""
        tail = chunk[-self._overlap :]
        # Avoid starting mid-word: drop up to the first whitespace.
        space = tail.find(" ")
        if space != -1:
            tail = tail[space + 1 :]
        return tail.strip()

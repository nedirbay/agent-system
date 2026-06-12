"""Offline feature-hashing embedding provider (Roadmap Task 9).

This is the default, fully offline `EmbeddingProvider`: it needs no API key and
no GPU, so the whole chunk → embed → store → search pipeline runs and can be
verified end-to-end. It hashes word unigrams + bigrams into a fixed-dimension
vector (the "hashing trick") and L2-normalises, so cosine similarity reflects
lexical overlap — enough to demonstrate retrieval.

Per EM-001 the production provider is Voyage AI (cloud) or BGE-M3 (on-prem);
either drops in behind the same `EmbeddingProvider` interface. EM-004: results
are cached by content hash so identical text is never re-embedded.
"""
from __future__ import annotations

import hashlib
import re
from collections import OrderedDict

import numpy as np
from starlette.concurrency import run_in_threadpool

from app.core.config import get_settings
from app.modules.knowledge.domain.embedding import EmbeddingProvider

_TOKEN = re.compile(r"\w+", re.UNICODE)
_CACHE_MAX = 4096


class HashingEmbeddingProvider(EmbeddingProvider):
    def __init__(self, *, dimension: int | None = None, model_name: str | None = None) -> None:
        settings = get_settings()
        self._dim = dimension or settings.embedding_dim
        self._model = model_name or settings.embedding_model
        # Small LRU cache keyed by sha256(text) → vector (EM-004).
        self._cache: "OrderedDict[str, list[float]]" = OrderedDict()

    @property
    def model_name(self) -> str:
        return self._model

    @property
    def dimension(self) -> int:
        return self._dim

    async def embed(self, texts: list[str]) -> list[list[float]]:
        results: list[list[float] | None] = [None] * len(texts)
        misses: list[tuple[int, str]] = []
        for i, text in enumerate(texts):
            key = hashlib.sha256(text.encode("utf-8")).hexdigest()
            cached = self._cache.get(key)
            if cached is not None:
                self._cache.move_to_end(key)
                results[i] = cached
            else:
                misses.append((i, key))

        if misses:
            vectors = await run_in_threadpool(
                self._embed_sync, [texts[i] for i, _ in misses]
            )
            for (i, key), vec in zip(misses, vectors):
                results[i] = vec
                self._cache[key] = vec
                self._cache.move_to_end(key)
                while len(self._cache) > _CACHE_MAX:
                    self._cache.popitem(last=False)

        return [r for r in results if r is not None]

    def _embed_sync(self, texts: list[str]) -> list[list[float]]:
        return [self._vectorize(t) for t in texts]

    def _vectorize(self, text: str) -> list[float]:
        vec = np.zeros(self._dim, dtype=np.float32)
        tokens = _TOKEN.findall(text.lower())
        if not tokens:
            return vec.tolist()
        features = list(tokens)
        # Word bigrams capture a little ordering/phrase information.
        features += [f"{a}_{b}" for a, b in zip(tokens, tokens[1:])]
        for feat in features:
            h = hashlib.md5(feat.encode("utf-8")).digest()
            idx = int.from_bytes(h[:8], "little") % self._dim
            sign = 1.0 if h[8] & 1 else -1.0
            vec[idx] += sign
        norm = float(np.linalg.norm(vec))
        if norm > 0:
            vec /= norm
        return vec.tolist()

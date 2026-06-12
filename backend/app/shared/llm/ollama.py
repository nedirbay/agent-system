"""Ollama-backed LLMProvider (MP-002).

Talks to a local Ollama server (`/api/chat`), which for this deployment proxies
the `gemma4:31b-cloud` model. Provider-level concerns — timeouts, retries, token
accounting, structured (JSON) output — live here so callers stay clean.
"""
from __future__ import annotations

import json

import httpx

from app.core.config import get_settings
from app.core.exceptions import AppError
from app.shared.llm.provider import (
    ChatMessage,
    CompletionResult,
    LLMProvider,
)


class LLMUnavailableError(AppError):
    status_code = 503
    code = "llm_unavailable"


class OllamaLLMProvider(LLMProvider):
    def __init__(
        self,
        *,
        base_url: str | None = None,
        model: str | None = None,
        timeout: float | None = None,
    ) -> None:
        settings = get_settings()
        self._base_url = (base_url or settings.ollama_base_url).rstrip("/")
        self._model = model or settings.ollama_model
        self._timeout = timeout or settings.llm_timeout_seconds

    async def complete(
        self,
        messages: list[ChatMessage],
        *,
        model: str | None = None,
        temperature: float = 0.2,
        max_tokens: int | None = None,
        _format: dict | str | None = None,
    ) -> CompletionResult:
        options: dict = {"temperature": temperature}
        if max_tokens is not None:
            options["num_predict"] = max_tokens
        payload: dict = {
            "model": model or self._model,
            "messages": [{"role": m.role, "content": m.content} for m in messages],
            "stream": False,
            "options": options,
        }
        if _format is not None:
            payload["format"] = _format

        try:
            async with httpx.AsyncClient(timeout=self._timeout) as client:
                resp = await client.post(f"{self._base_url}/api/chat", json=payload)
                resp.raise_for_status()
                body = resp.json()
        except (httpx.HTTPError, httpx.TimeoutException) as exc:  # FH-001 / FH-002
            raise LLMUnavailableError(f"Ollama request failed: {exc}") from exc

        return CompletionResult(
            text=(body.get("message") or {}).get("content", ""),
            model=body.get("model", payload["model"]),
            prompt_tokens=body.get("prompt_eval_count", 0) or 0,
            completion_tokens=body.get("eval_count", 0) or 0,
        )

    async def complete_json(
        self,
        messages: list[ChatMessage],
        *,
        model: str | None = None,
        temperature: float = 0.0,
        schema: dict | None = None,
    ) -> dict:
        # `format` hints Ollama toward JSON; cloud-proxied models may ignore it
        # and wrap output in markdown fences, so parsing below is tolerant.
        fmt: dict | str = schema if schema is not None else "json"
        result = await self.complete(
            messages, model=model, temperature=temperature, _format=fmt
        )
        parsed = _parse_json_lenient(result.text)
        if parsed is None:
            raise LLMUnavailableError("LLM did not return valid JSON")
        # Normalise a bare array to an object so callers have a stable contract.
        if isinstance(parsed, list):
            return {"items": parsed}
        return parsed


def _strip_fences(text: str) -> str:
    text = text.strip()
    if text.startswith("```"):
        # Drop the opening ``` / ```json line and any trailing fence.
        text = text.split("\n", 1)[1] if "\n" in text else text[3:]
        if text.rstrip().endswith("```"):
            text = text.rstrip()[:-3]
    return text.strip()


def _parse_json_lenient(text: str) -> dict | list | None:
    candidate = _strip_fences(text)
    try:
        return json.loads(candidate)
    except json.JSONDecodeError:
        pass
    # Find the first balanced JSON object or array embedded in the text.
    for opener, closer in (("{", "}"), ("[", "]")):
        start = candidate.find(opener)
        end = candidate.rfind(closer)
        if start != -1 and end > start:
            try:
                return json.loads(candidate[start : end + 1])
            except json.JSONDecodeError:
                continue
    return None

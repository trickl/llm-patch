"""Thin Ollama client helpers shared across scripts and strategies."""
from __future__ import annotations

import json
import os
import time
from dataclasses import dataclass, field
from typing import Optional
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


class OllamaError(RuntimeError):
    """Raised when the Ollama HTTP API cannot satisfy a request."""


@dataclass(slots=True)
class OllamaUsage:
    """Best-effort usage metrics for Ollama /api/generate calls.

    Ollama streams JSON objects. The final object (done=true) typically includes:
      - prompt_eval_count (input tokens)
      - eval_count (output tokens)
      - total_duration / eval_duration / prompt_eval_duration (nanoseconds)

    Not all providers/models return all fields, so these are optional.
    """

    requests: int = 0
    prompt_tokens: int = 0
    completion_tokens: int = 0
    total_duration_s: float = 0.0  # server-reported, if present
    wall_time_s: float = 0.0  # client-measured

    @property
    def total_tokens(self) -> int:
        return self.prompt_tokens + self.completion_tokens

    def to_dict(self) -> dict[str, object]:
        return {
            "requests": self.requests,
            "prompt_tokens": self.prompt_tokens,
            "completion_tokens": self.completion_tokens,
            "total_tokens": self.total_tokens,
            "total_duration_s": round(self.total_duration_s, 6),
            "wall_time_s": round(self.wall_time_s, 6),
        }


def _safe_int(value: object) -> int | None:
    if isinstance(value, bool):
        return None
    if isinstance(value, int):
        return value
    if isinstance(value, float):
        return int(value)
    if isinstance(value, str):
        try:
            return int(value)
        except ValueError:
            return None
    return None


def _safe_ns_to_seconds(value: object) -> float | None:
    ns = _safe_int(value)
    if ns is None:
        return None
    return ns / 1_000_000_000.0


def _call_ollama_with_stats(
    model: str,
    prompt: str,
    temperature: float = 0.0,
    *,
    host: str | None = None,
    response_format: str | None = None,
) -> tuple[str, OllamaUsage]:
    """Send a completion request to Ollama and return (response_text, usage)."""

    resolved_host = (host or os.environ.get("OLLAMA_HOST", "http://localhost:11434")).rstrip("/")
    url = f"{resolved_host}/api/generate"
    payload: dict[str, object] = {
        "model": model,
        "prompt": prompt,
        "options": {"temperature": temperature},
        "stream": True,
    }
    if response_format:
        # Ollama supports JSON mode via "format": "json".
        # See: https://github.com/ollama/ollama/blob/main/docs/api.md (generate)
        payload["format"] = response_format
    request = Request(url, data=json.dumps(payload).encode("utf-8"), headers={"Content-Type": "application/json"})

    chunks: list[str] = []
    usage = OllamaUsage(requests=1)
    start = time.perf_counter()
    done_payload: dict[str, object] | None = None
    try:
        with urlopen(request) as response:  # noqa: S310 - trusted local endpoint
            for raw_line in response:
                line = raw_line.decode("utf-8").strip()
                if not line:
                    continue
                data = json.loads(line)
                if isinstance(data, dict):
                    done_payload = data
                chunk = data.get("response") if isinstance(data, dict) else None
                if chunk:
                    chunks.append(str(chunk))
                if isinstance(data, dict) and data.get("done"):
                    break
    except (HTTPError, URLError) as err:  # pragma: no cover - thin transport shim
        raise OllamaError(f"Failed to contact Ollama at {url}: {err}") from err
    finally:
        usage.wall_time_s = time.perf_counter() - start

    if not chunks:
        raise OllamaError("Ollama returned an empty response")

    # Best-effort usage extraction from the final payload.
    if isinstance(done_payload, dict):
        prompt_tokens = _safe_int(done_payload.get("prompt_eval_count"))
        completion_tokens = _safe_int(done_payload.get("eval_count"))
        if prompt_tokens is not None:
            usage.prompt_tokens = max(0, prompt_tokens)
        if completion_tokens is not None:
            usage.completion_tokens = max(0, completion_tokens)

        # Prefer total_duration if present; else add eval + prompt_eval durations.
        total_s = _safe_ns_to_seconds(done_payload.get("total_duration"))
        if total_s is None:
            eval_s = _safe_ns_to_seconds(done_payload.get("eval_duration")) or 0.0
            prompt_eval_s = _safe_ns_to_seconds(done_payload.get("prompt_eval_duration")) or 0.0
            total_s = eval_s + prompt_eval_s if (eval_s or prompt_eval_s) else None
        if total_s is not None:
            usage.total_duration_s = max(0.0, float(total_s))

    return "".join(chunks).strip(), usage


def call_ollama(
    model: str,
    prompt: str,
    temperature: float = 0.0,
    *,
    host: str | None = None,
    response_format: str | None = None,
) -> str:
    """Send a completion request to Ollama and return the concatenated response."""

    text, _usage = _call_ollama_with_stats(
        model,
        prompt,
        temperature,
        host=host,
        response_format=response_format,
    )
    return text


@dataclass
class OllamaLLMClient:
    """Adapter that satisfies ``GuidedConvergenceStrategy``'s ``LLMClient`` protocol."""

    model: str
    temperature: float = 0.0
    host: Optional[str] = None

    # Accumulated usage for the lifetime of this client instance.
    usage: OllamaUsage = field(default_factory=OllamaUsage)

    def reset_usage(self) -> None:
        self.usage = OllamaUsage()

    def usage_snapshot(self) -> dict[str, object]:
        return self.usage.to_dict()

    def complete(
        self,
        *,
        prompt: str,
        temperature: float | None = None,
        model: str | None = None,
        response_format: str | None = None,
    ) -> str:
        effective_model = model or self.model
        effective_temperature = self.temperature if temperature is None else temperature

        text, usage = _call_ollama_with_stats(
            effective_model,
            prompt,
            effective_temperature,
            host=self.host,
            response_format=response_format,
        )

        # Accumulate best-effort stats.
        self.usage.requests += usage.requests
        self.usage.prompt_tokens += usage.prompt_tokens
        self.usage.completion_tokens += usage.completion_tokens
        self.usage.total_duration_s += usage.total_duration_s
        self.usage.wall_time_s += usage.wall_time_s
        return text

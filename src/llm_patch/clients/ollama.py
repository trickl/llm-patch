"""Thin Ollama client helpers shared across scripts and strategies."""
from __future__ import annotations

import json
import os
from dataclasses import dataclass
from typing import Optional
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


class OllamaError(RuntimeError):
    """Raised when the Ollama HTTP API cannot satisfy a request."""


def call_ollama(model: str, prompt: str, temperature: float = 0.0, *, host: str | None = None) -> str:
    """Send a completion request to Ollama and return the concatenated response."""

    resolved_host = (host or os.environ.get("OLLAMA_HOST", "http://localhost:11434")).rstrip("/")
    url = f"{resolved_host}/api/generate"
    payload = {
        "model": model,
        "prompt": prompt,
        "options": {"temperature": temperature},
        "stream": True,
    }
    request = Request(url, data=json.dumps(payload).encode("utf-8"), headers={"Content-Type": "application/json"})
    chunks: list[str] = []
    try:
        with urlopen(request) as response:  # noqa: S310 - trusted local endpoint
            for raw_line in response:
                line = raw_line.decode("utf-8").strip()
                if not line:
                    continue
                data = json.loads(line)
                chunk = data.get("response")
                if chunk:
                    chunks.append(chunk)
                if data.get("done"):
                    break
    except (HTTPError, URLError) as err:  # pragma: no cover - thin transport shim
        raise OllamaError(f"Failed to contact Ollama at {url}: {err}") from err
    if not chunks:
        raise OllamaError("Ollama returned an empty response")
    return "".join(chunks).strip()


@dataclass
class OllamaLLMClient:
    """Adapter that satisfies ``GuidedConvergenceStrategy``'s ``LLMClient`` protocol."""

    model: str
    temperature: float = 0.0
    host: Optional[str] = None

    def complete(self, *, prompt: str, temperature: float | None = None, model: str | None = None) -> str:
        effective_model = model or self.model
        effective_temperature = self.temperature if temperature is None else temperature
        return call_ollama(effective_model, prompt, effective_temperature, host=self.host)

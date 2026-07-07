"""Swappable runtime-LLM provider interface (C4).

CASCABEL's runtime detection synthesis never hardcodes a paid API. The
default provider is a local OSS model served by Ollama; the interface is
abstract so it can be swapped, and a deterministic offline MockProvider
lets the whole test suite run with no model, no key, and no network.
"""
from __future__ import annotations

import json
import urllib.request
from abc import ABC, abstractmethod
from typing import Optional

from cascabel.config import CONFIG, Config


class LLMUnavailableError(RuntimeError):
    """Raised when a runtime LLM provider cannot be reached."""


class LLMProvider(ABC):
    """Contract every runtime-LLM provider must satisfy."""

    name: str = "abstract"

    @abstractmethod
    def complete(self, prompt: str) -> str:
        """Return the model's raw text completion for a prompt."""
        raise NotImplementedError


class OllamaProvider(LLMProvider):
    """Local, free, offline OSS model via Ollama (the documented default)."""

    name = "ollama"

    def __init__(self, config: Config | None = None):
        cfg = config or CONFIG
        self.url = cfg.ollama_url
        self.model = cfg.ollama_model
        self.timeout = cfg.llm_timeout_s

    def complete(self, prompt: str) -> str:
        payload = {"model": self.model, "prompt": prompt, "stream": False}
        data = json.dumps(payload).encode("utf-8")
        req = urllib.request.Request(
            self.url,
            data=data,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        try:
            with urllib.request.urlopen(req, timeout=self.timeout) as response:
                body = json.loads(response.read().decode("utf-8"))
        except Exception as exc:  # network/model errors are recoverable upstream
            raise LLMUnavailableError(
                f"Ollama provider unreachable at {self.url}: {exc}"
            ) from exc
        return body.get("response", "")


class MockProvider(LLMProvider):
    """Deterministic offline provider for tests and no-model environments.

    It echoes a caller-supplied canned response (or empty string), so tests
    control exactly what the "model" returns and stay network-free.
    """

    name = "mock"

    def __init__(self, response: str = ""):
        self.response = response
        self.last_prompt: Optional[str] = None

    def complete(self, prompt: str) -> str:
        self.last_prompt = prompt
        return self.response


def get_provider(config: Config | None = None) -> LLMProvider:
    """Resolve the configured runtime-LLM provider (local default)."""
    cfg = config or CONFIG
    provider = (cfg.llm_provider or "ollama").lower()
    if provider == "ollama":
        return OllamaProvider(cfg)
    if provider == "mock":
        return MockProvider()
    raise ValueError(f"Unknown LLM provider '{cfg.llm_provider}'")

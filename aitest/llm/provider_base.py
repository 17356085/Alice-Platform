"""Backward-compatible LLM provider base facade."""

from __future__ import annotations

from aitest.adapters.llm.provider_base import (  # noqa: F401
    LLMProvider,
    LLMResponse,
    StreamEvent,
)
from aitest.runtime.config import config as _runtime_config


class _CompatConfig:
    """Expose legacy provider config attributes expected by old providers."""

    @property
    def anthropic_api_key(self) -> str:
        return _runtime_config.get_env("ANTHROPIC_API_KEY", "")

    @property
    def deepseek_api_key(self) -> str:
        return _runtime_config.get_env("DEEPSEEK_API_KEY", "")

    @property
    def openai_api_key(self) -> str:
        return _runtime_config.get_env("OPENAI_API_KEY", "")

    @property
    def mimo_api_key(self) -> str:
        return _runtime_config.get_env("MIMO_API_KEY", "")

    @property
    def mimo_base_url(self) -> str:
        return _runtime_config.get_env("MIMO_BASE_URL", "")

    @property
    def ollama_base_url(self) -> str:
        return _runtime_config.ollama_base_url


def _get_config() -> _CompatConfig:
    return _CompatConfig()


__all__ = ["LLMProvider", "LLMResponse", "StreamEvent", "_get_config"]

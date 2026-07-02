# Re-export — 原文件已搬到 adapters/llm/interface.py
from aitest.adapters.llm.interface import (  # noqa: F401
    LLMResponse, StreamEvent, LLMProvider, _get_config,
    PROVIDER_REGISTRY, get_provider, list_providers,
    ClaudeProvider, OpenAIProvider, OllamaProvider, DeepSeekProvider, MiMoProvider,
)

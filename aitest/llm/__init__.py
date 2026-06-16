"""
LLM Provider 抽象层 — 统一 Claude / OpenAI / Ollama 调用接口。

用法:
    from aitest.llm import get_provider

    llm = get_provider("claude")
    response = llm.complete("你是测试专家", "分析这个页面")

    llm = get_provider("openai", model="gpt-4o-mini")
    llm = get_provider("ollama", model="qwen3")
"""
from aitest.llm.provider import (
    LLMProvider,
    LLMResponse,
    ClaudeProvider,
    OpenAIProvider,
    OllamaProvider,
    get_provider,
    list_providers,
)

# [LAYER:Adapter/LLM] 从 aitest/llm/provider.py 搬入
"""
LLM Provider — 统一 Claude / OpenAI / Ollama / DeepSeek 调用接口。

设计原则:
  1. 所有 Provider 实现相同的 LLMProvider 接口
  2. LLMResponse 是统一的返回格式
  3. get_provider() 工厂函数根据名称创建实例
  4. API Key 从环境变量读取（.env 或系统环境变量）

架构 (v2.7+):
  provider_base.py     — LLMResponse, StreamEvent, LLMProvider(ABC)
  providers/claude.py  — ClaudeProvider (Anthropic SDK)
  providers/openai.py  — OpenAIProvider (OpenAI SDK)
  providers/ollama.py  — OllamaProvider (local models)
  providers/deepseek.py — DeepSeekProvider (OpenAI-compatible)
  provider.py          — 工厂函数 + 向后兼容 re-exports

用法:
    llm = get_provider("claude")
    response = llm.complete("system prompt", "user prompt")
"""

# ── Backward-compatible re-exports ──────────────────────────────────
from aitest.adapters.llm.provider_base import LLMResponse, StreamEvent, LLMProvider, _get_config  # noqa: F401
from aitest.llm.providers.claude import ClaudeProvider
from aitest.llm.providers.openai import OpenAIProvider
from aitest.llm.providers.ollama import OllamaProvider
from aitest.llm.providers.deepseek import DeepSeekProvider
from aitest.llm.providers.mimo import MiMoProvider
from aitest.llm.providers.mock import MockProvider

# ══════════════════════════════════════════════════════════════════════════
#  工厂函数
# ══════════════════════════════════════════════════════════════════════════

PROVIDER_REGISTRY = {
    "claude": ClaudeProvider,
    "openai": OpenAIProvider,
    "ollama": OllamaProvider,
    "deepseek": DeepSeekProvider,
    "mimo": MiMoProvider,
    "mock": MockProvider,
}


def get_provider(name: str = "claude", **kwargs) -> LLMProvider:
    """
    工厂函数：根据名称创建 LLM Provider 实例。

    参数:
        name: Provider 名称 — "claude" | "openai" | "ollama" | "deepseek"
        **kwargs: 传递给 Provider __init__ 的额外参数（如 model, api_key, base_url）

    返回:
        LLMProvider 实例（已自动包装 tracer）

    用法:
        llm = get_provider("claude")
        llm = get_provider("openai", model="gpt-4o-mini")
        llm = get_provider("ollama", model="qwen3:14b", base_url="http://localhost:11434")
        llm = get_provider("deepseek", model="deepseek-chat")
    """
    if name not in PROVIDER_REGISTRY:
        available = list(PROVIDER_REGISTRY.keys())
        raise ValueError(f"Unknown provider: '{name}'. Available: {available}")

    instance = PROVIDER_REGISTRY[name](**kwargs)

    # P1-1: 用 tracer 装饰器包装 complete() 方法
    try:
        from aitest.infra.trace import _trace_llm_call
        instance.complete = _trace_llm_call(instance.complete)
    except Exception:
        pass  # 追踪包装失败不影响 LLM 调用

    return instance


def list_providers() -> list[str]:
    """列出所有可用的 Provider 名称。"""
    return list(PROVIDER_REGISTRY.keys())

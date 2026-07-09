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

# Legacy imports for backward compatibility (deprecated, will be removed in Phase 9)
from aitest.llm.providers.claude import ClaudeProvider
from aitest.llm.providers.openai import OpenAIProvider
from aitest.llm.providers.ollama import OllamaProvider
from aitest.llm.providers.deepseek import DeepSeekProvider
from aitest.llm.providers.mimo import MiMoProvider
from aitest.llm.providers.mock import MockProvider
from alice_engine.providers import list_providers as _sdk_list_providers
from alice_engine.providers import get_provider as _sdk_get_provider


PROVIDER_REGISTRY = {name: None for name in _sdk_list_providers()}

# ══════════════════════════════════════════════════════════════════════════
#  工厂函数 (PH8-PR-8.6: 委托给 SDK 层)
# ══════════════════════════════════════════════════════════════════════════


def get_provider(name: str = "claude", **kwargs) -> LLMProvider:
    """
    工厂函数：根据名称创建 LLM Provider 实例。

    参数:
        name: Provider 名称 — "claude" | "openai" | "ollama" | "deepseek" | "mimo" | "mock"
        **kwargs: 传递给 Provider __init__ 的额外参数（如 model, api_key, base_url）

    返回:
        LLMProvider 实例（已自动包装 tracer）

    架构 (PH8-PR-8.6+):
        委托给 alice_engine.providers.get_provider() (单一事实源)，
        平台层仅负责：API key 注入、trace 装饰器包装。

    用法:
        llm = get_provider("claude")
        llm = get_provider("openai", model="gpt-4o-mini")
        llm = get_provider("ollama", model="qwen3:14b", base_url="http://localhost:11434")
        llm = get_provider("deepseek", model="deepseek-v4-flash")
    """
    # 注入平台密钥（如果 kwargs 未提供 api_key）
    if "api_key" not in kwargs:
        from aitest.runtime.config import config as _cfg
        key_map = {
            "claude": _cfg.get_env("ANTHROPIC_API_KEY", ""),
            "anthropic": _cfg.get_env("ANTHROPIC_API_KEY", ""),
            "openai": _cfg.get_env("OPENAI_API_KEY", ""),
            "deepseek": _cfg.get_env("DEEPSEEK_API_KEY", ""),
            "mimo": _cfg.get_env("MIMO_API_KEY", ""),
        }
        if name in key_map and key_map[name]:
            kwargs["api_key"] = key_map[name]

    # MiMo 特殊处理：注入 base_url
    if name == "mimo" and "base_url" not in kwargs:
        from aitest.runtime.config import config as _cfg
        base_url = _cfg.get_env("MIMO_BASE_URL", "")
        if base_url:
            kwargs["base_url"] = base_url

    # Ollama 特殊处理：注入 base_url
    if name == "ollama" and "base_url" not in kwargs:
        from aitest.runtime.config import config as _cfg
        base_url = _cfg.ollama_base_url
        if base_url:
            kwargs["base_url"] = base_url

    # 获取 SDK provider 实例
    instance = _sdk_get_provider(name, **kwargs)

    # 包装 tracer（平台层专属逻辑）
    try:
        from aitest.infra.trace import _trace_llm_call
        instance.complete = _trace_llm_call(instance.complete)
        if hasattr(instance, "stream"):
            instance.stream = _trace_llm_call(instance.stream)
    except Exception:
        pass  # tracer 包装失败不影响核心功能

    return instance


def list_providers() -> list[str]:
    """列出所有可用的 Provider 名称。"""
    return _sdk_list_providers()

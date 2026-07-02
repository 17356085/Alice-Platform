"""Provider 注册表。"""

from alice_engine.providers.base import LLMProvider
from alice_engine.providers.mock import MockProvider

# 内置 providers
_PROVIDERS: dict[str, type[LLMProvider]] = {
    "mock": MockProvider,
}

# 延迟加载的 providers (需要额外依赖)
_LAZY_PROVIDERS: dict[str, tuple[str, str]] = {
    "claude": ("alice_engine.providers.claude", "ClaudeProvider"),
    "anthropic": ("alice_engine.providers.claude", "ClaudeProvider"),
    "openai": ("alice_engine.providers.openai", "OpenAIProvider"),
    "deepseek": ("alice_engine.providers.deepseek", "DeepSeekProvider"),
    "ollama": ("alice_engine.providers.ollama", "OllamaProvider"),
}


def get_provider(name: str, **kwargs) -> LLMProvider:
    """获取 LLM Provider 实例。

    Args:
        name: Provider 名称 ("mock", "claude", "openai", "deepseek", "ollama")
        **kwargs: 传递给 Provider 构造函数的参数

    Returns:
        LLMProvider 实例
    """
    name = name.lower()

    # 内置 providers
    if name in _PROVIDERS:
        return _PROVIDERS[name](**kwargs)

    # 延迟加载 providers
    if name in _LAZY_PROVIDERS:
        module_path, class_name = _LAZY_PROVIDERS[name]
        try:
            import importlib
            module = importlib.import_module(module_path)
            cls = getattr(module, class_name)
            return cls(**kwargs)
        except ImportError as e:
            from alice_engine.exceptions import LLMProviderError
            raise LLMProviderError(
                f"Provider '{name}' 需要额外依赖。"
                f"请安装: pip install alice-engine[llm-{name}]"
            ) from e

    from alice_engine.exceptions import LLMProviderError
    available = list(_PROVIDERS.keys()) + list(_LAZY_PROVIDERS.keys())
    raise LLMProviderError(
        f"未知 Provider: '{name}'。可用: {available}"
    )


def register_provider(name: str, provider_cls: type[LLMProvider]) -> None:
    """注册自定义 Provider。"""
    _PROVIDERS[name.lower()] = provider_cls


def list_providers() -> list[str]:
    """列出所有可用 Provider。"""
    return list(_PROVIDERS.keys()) + list(_LAZY_PROVIDERS.keys())

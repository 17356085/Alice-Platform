"""Provider 注册表。"""

from dataclasses import replace
from typing import Any

from alice_engine.providers.base import LLMProvider, ProviderContract
from alice_engine.providers.mock import MockProvider

# 内置 providers
_PROVIDERS: dict[str, type[LLMProvider]] = {
    "mock": MockProvider,
}

_CONTRACTS: dict[str, ProviderContract] = {
    "mock": MockProvider.contract(),
}

# 延迟加载的 providers (需要额外依赖)
_LAZY_PROVIDERS: dict[str, tuple[str, str]] = {
    "claude": ("alice_engine.providers.claude", "ClaudeProvider"),
    "anthropic": ("alice_engine.providers.claude", "ClaudeProvider"),
    "openai": ("alice_engine.providers.openai", "OpenAIProvider"),
    "deepseek": ("alice_engine.providers.deepseek", "DeepSeekProvider"),
    "ollama": ("alice_engine.providers.ollama", "OllamaProvider"),
    "mimo": ("alice_engine.providers.mimo", "MiMoProvider"),
}


def _build_lazy_contract(name: str, module_path: str, class_name: str) -> ProviderContract:
    return ProviderContract(
        name=name,
        module=module_path,
        class_name=class_name,
        description=f"Lazy-loaded provider: {name}",
        kind="llm",
        supports_tools=False,
        supports_streaming=False,
        available=False,
        source="lazy",
    )


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
            _PROVIDERS[name] = cls
            _CONTRACTS[name] = cls.contract(name=name)
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
    _CONTRACTS[name.lower()] = provider_cls.contract(name=name.lower())


def register_provider_contract(name: str, contract: ProviderContract) -> None:
    """注册 Provider 契约描述，不要求 provider 可立即实例化。"""
    _CONTRACTS[name.lower()] = replace(contract, name=name.lower())


def list_providers() -> list[str]:
    """列出所有可用 Provider。"""
    return list(_PROVIDERS.keys()) + list(_LAZY_PROVIDERS.keys())


def list_provider_contracts() -> list[ProviderContract]:
    """列出所有已知 Provider 契约。"""
    contracts: dict[str, ProviderContract] = dict(_CONTRACTS)
    for name, (module_path, class_name) in _LAZY_PROVIDERS.items():
        contracts.setdefault(name, _build_lazy_contract(name, module_path, class_name))
    return list(contracts.values())


def get_provider_contract(name: str) -> ProviderContract | None:
    """Get provider contract by name, without instantiating the provider."""
    name = name.lower()
    if name in _CONTRACTS:
        return _CONTRACTS[name]
    if name in _LAZY_PROVIDERS:
        module_path, class_name = _LAZY_PROVIDERS[name]
        return _build_lazy_contract(name, module_path, class_name)
    return None

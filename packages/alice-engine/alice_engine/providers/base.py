"""LLMProvider — LLM 提供者抽象。"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any


@dataclass
class LLMResponse:
    """LLM 响应。"""

    content: str = ""
    tool_calls: list[dict] = field(default_factory=list)
    tool_results: list[dict] = field(default_factory=list)
    usage: dict = field(default_factory=dict)
    model: str = ""
    finish_reason: str = "stop"
    latency_ms: int = 0


@dataclass
class ProviderContract:
    """Provider 插件契约描述。

    这个对象用于注册表发现，不要求实例化 provider。
    """

    name: str
    module: str = ""
    class_name: str = ""
    description: str = ""
    kind: str = "llm"
    supports_tools: bool = False
    supports_streaming: bool = False
    available: bool = True
    source: str = "builtin"
    extra: dict[str, Any] = field(default_factory=dict)


class LLMProvider(ABC):
    """LLM Provider 抽象基类。"""

    provider_name: str = ""
    provider_description: str = ""
    provider_kind: str = "llm"
    provider_supports_tools: bool = False
    provider_supports_streaming: bool = False

    @classmethod
    def contract(cls, name: str | None = None, **extra: Any) -> ProviderContract:
        """Build a discovery contract without instantiating the provider."""
        provider_name = name or getattr(cls, "provider_name", "") or cls.__name__.removesuffix("Provider").lower()
        return ProviderContract(
            name=provider_name,
            module=cls.__module__,
            class_name=cls.__name__,
            description=getattr(cls, "provider_description", ""),
            kind=getattr(cls, "provider_kind", "llm"),
            supports_tools=bool(getattr(cls, "provider_supports_tools", False)),
            supports_streaming=bool(getattr(cls, "provider_supports_streaming", False)),
            available=True,
            source="registered",
            extra=extra,
        )

    @abstractmethod
    def complete(
        self,
        system_prompt: str,
        user_prompt: str,
        tools: list[dict] | None = None,
        **kwargs,
    ) -> LLMResponse:
        """发送 completion 请求。"""
        ...

    @abstractmethod
    def supports_tools(self) -> bool:
        """是否支持 tool calling。"""
        ...

    @classmethod
    def provider_id(cls) -> str:
        """Standardized provider identity."""
        return getattr(cls, "provider_name", "") or cls.__name__.removesuffix("Provider").lower()

    def stream(self, system_prompt: str, user_prompt: str, **kwargs):
        """流式输出（可选实现）。"""
        raise NotImplementedError(f"{type(self).__name__} does not support streaming")

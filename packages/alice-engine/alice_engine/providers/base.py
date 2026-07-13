"""LLMProvider — LLM 提供者抽象。"""

from abc import ABC, abstractmethod
from collections.abc import Generator
from dataclasses import dataclass, field
from typing import Any, Literal, Optional


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

    @property
    def token_usage(self) -> dict:
        """Backward-compatible normalized token usage.

        The SDK stores provider usage in ``usage`` while the platform API
        historically consumed ``token_usage``.  Keep both contracts usable
        at the boundary so a real provider response cannot fail after the
        model call has already succeeded.
        """
        usage = self.usage or {}
        input_tokens = usage.get("input", usage.get("prompt_tokens", usage.get("input_tokens", 0)))
        output_tokens = usage.get("output", usage.get("completion_tokens", usage.get("output_tokens", 0)))
        total_tokens = usage.get("total", usage.get("total_tokens", input_tokens + output_tokens))
        return {
            **usage,
            "input": input_tokens,
            "output": output_tokens,
            "total": total_tokens,
        }

    @token_usage.setter
    def token_usage(self, value: dict) -> None:
        self.usage = dict(value or {})


# ── 流式事件类型 ──
StreamEventType = Literal[
    "content_start", "content_chunk", "content_end",
    "tool_use_start", "tool_input_chunk", "tool_use_end",
    "done", "error",
]


@dataclass
class StreamEvent:
    """流式 LLM 调用的单个事件。

    典型流:
      content_start → content_chunk* → content_end → done
      或 tool_use_start → tool_input_chunk* → tool_use_end → done
    """
    type: StreamEventType
    content: str = ""                         # text delta / tool_input partial JSON
    tool_name: str = ""                       # tool_use_start
    tool_id: str = ""                         # tool_use_start
    tool_input: dict = field(default_factory=dict)  # tool_use_end (final)
    finish_reason: str = ""                   # done (stop/length/tool_use)
    token_usage: dict = field(default_factory=dict)  # done (final usage)
    error_message: str = ""                   # error


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

    def stream(
        self,
        system_prompt: str,
        user_prompt: str,
        tools: Optional[list[dict]] = None,
        **kwargs,
    ) -> Generator[StreamEvent, None, LLMResponse]:
        """流式输出（可选实现）。

        yield StreamEvent 逐块输出，最后 return LLMResponse（聚合结果）。

        yield 顺序:
          content_start → content_chunk* → content_end → done
          或 tool_use_start → tool_input_chunk* → tool_use_end → done
        """
        raise NotImplementedError(f"{type(self).__name__} does not support streaming")

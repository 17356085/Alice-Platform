"""LLMProvider — LLM 提供者抽象。"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any


@dataclass
class LLMResponse:
    """LLM 响应。"""

    content: str = ""
    tool_calls: list[dict] = field(default_factory=list)
    usage: dict = field(default_factory=dict)
    model: str = ""
    finish_reason: str = "stop"


class LLMProvider(ABC):
    """LLM Provider 抽象基类。"""

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

    def stream(self, system_prompt: str, user_prompt: str, **kwargs):
        """流式输出（可选实现）。"""
        raise NotImplementedError(f"{type(self).__name__} does not support streaming")

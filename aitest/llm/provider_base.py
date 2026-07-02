"""LLM Provider 基类 — 保持原始代码。"""

from dataclasses import dataclass, field
from typing import Any, Optional
from abc import ABC, abstractmethod


@dataclass
class LLMResponse:
    """LLM 响应。"""
    content: str = ""
    tool_calls: list = field(default_factory=list)
    token_usage: dict = field(default_factory=dict)
    model: str = ""
    finish_reason: str = "stop"
    latency_ms: int = 0


@dataclass
class StreamEvent:
    """流式事件。"""
    type: str = ""
    content: str = ""
    delta: str = ""
    tool_calls: list = field(default_factory=list)
    finish_reason: str = ""


class LLMProvider(ABC):
    """LLM Provider 抽象基类。"""

    @abstractmethod
    def complete(self, system_prompt, user_prompt, tools=None, **kwargs) -> LLMResponse:
        ...

    @abstractmethod
    def supports_tools(self) -> bool:
        ...


def _get_config():
    """获取配置。"""
    return {}

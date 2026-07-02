# [LAYER:Adapter/LLM] 从 aitest/llm/provider_base.py 搬入
"""
LLM Provider — 统一 Claude / OpenAI / Ollama 调用接口。

设计原则:
  1. 所有 Provider 实现相同的 LLMProvider 接口
  2. LLMResponse 是统一的返回格式
  3. get_provider() 工厂函数根据名称创建实例
  4. API Key 从环境变量读取（.env 或系统环境变量）

用法:
    llm = get_provider("claude")
    response = llm.complete("system prompt", "user prompt")
    logger.info(response.content)
"""
from pathlib import Path
from abc import ABC, abstractmethod
from collections.abc import Generator
from dataclasses import dataclass, field
from typing import Optional, Literal


import logging

logger = logging.getLogger(__name__)

# .env loaded once by aitest.config (imported on demand via _get_config)
_CONFIG = None


def _get_config():
    global _CONFIG
    if _CONFIG is None:
        from aitest.runtime.config import config as _cfg
        _CONFIG = _cfg
    return _CONFIG


# ══════════════════════════════════════════════════════════════════════════
#  数据结构
# ══════════════════════════════════════════════════════════════════════════

@dataclass
class LLMResponse:
    """统一的 LLM 调用返回格式。"""
    content: str                              # 模型输出文本
    tool_calls: list[dict] = field(default_factory=list)  # Tool calling 结果
    token_usage: dict = field(default_factory=dict)       # {"input": N, "output": N}
    model: str = ""                           # 实际使用的模型名
    finish_reason: str = ""                   # stop | length | tool_calls | error


# ── 流式事件类型 ──
StreamEventType = Literal[
    "content_start", "content_chunk", "content_end",
    "tool_use_start", "tool_input_chunk", "tool_use_end",
    "done", "error",
]


@dataclass
class StreamEvent:
    """
    流式 LLM 调用的单个事件。

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


# ══════════════════════════════════════════════════════════════════════════
#  抽象基类
# ══════════════════════════════════════════════════════════════════════════

class LLMProvider(ABC):
    """LLM Provider 抽象基类。所有 Provider 需实现 complete() 和 stream_complete() 方法。"""

    @abstractmethod
    def complete(
        self,
        system_prompt: str,
        user_prompt: str,
        tools: Optional[list[dict]] = None,
        temperature: float = 0.7,
        max_tokens: int = 8192,
    ) -> LLMResponse:
        """
        执行一次 LLM 调用（同步，返回完整响应）。

        参数:
            system_prompt: 系统提示词（设定角色和规则）
            user_prompt:   用户提示词（具体任务描述）
            tools:         Tool definitions（支持 tool calling 的 Provider）
            temperature:   随机性控制 (0.0-1.0)
            max_tokens:    最大输出 token 数

        返回:
            LLMResponse: 统一格式的响应
        """
        pass

    @abstractmethod
    def stream_complete(
        self,
        system_prompt: str,
        user_prompt: str,
        tools: Optional[list[dict]] = None,
        temperature: float = 0.7,
        max_tokens: int = 8192,
    ) -> Generator[StreamEvent, None, LLMResponse]:
        """
        执行一次流式 LLM 调用。

        yield StreamEvent 逐块输出，最后 return LLMResponse（聚合结果）。

        yield 顺序:
          content_start → content_chunk* → content_end → done
          或 tool_use_start → tool_input_chunk* → tool_use_end → done

        用法:
            llm = get_provider("claude")
            for event in llm.stream_complete("system", "user"):
                logger.info(event.content, end="", flush=True)
            final = event  # 最后一次 yield 后的 return 值通过 PEP 342 不可直接取，
                           # 建议用累积方式或包装函数获取最终 LLMResponse
        """
        pass

    @abstractmethod
    def supports_tools(self) -> bool:
        """是否支持原生 tool calling / function calling。"""
        pass


"""Deprecated provider implementation.

Retained only for backward compatibility with older CLI/runtime paths.
"""

from typing import Optional, Literal
from collections.abc import Generator
from dataclasses import dataclass, field
import json
import time
import os
from aitest.llm.provider_base import LLMProvider, LLMResponse, StreamEvent, _get_config

# ══════════════════════════════════════════════════════════════════════════
#  Ollama Provider (本地模型)
# ══════════════════════════════════════════════════════════════════════════

class OllamaProvider(LLMProvider):
    """
    Ollama 本地模型 Provider（通过 OpenAI 兼容 API）。

    前置条件: 本地运行 Ollama 服务且已拉取模型
      ollama serve                  # 启动服务
      ollama pull qwen3:8b         # 拉取模型

    默认地址: http://localhost:11434
    默认模型: qwen3:8b
    """

    def __init__(self, model: str = "qwen3:8b", base_url: str = ""):
        base_url = base_url or _get_config().ollama_base_url

        try:
            from openai import OpenAI
        except ImportError:
            raise ImportError("请安装 openai: pip install openai")

        self.client = OpenAI(
            base_url=f"{base_url.rstrip('/')}/v1",
            api_key="ollama"  # Ollama 不需要真实 API Key
        )
        self.model = model

    def complete(
        self,
        system_prompt: str,
        user_prompt: str,
        tools: Optional[list[dict]] = None,
        temperature: float = 0.7,
        max_tokens: int = 4096,  # 本地模型 context 较小
    ) -> LLMResponse:
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ]

        try:
            completion = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
            )
        except Exception as e:
            return LLMResponse(
                content=f"[Ollama Error] {str(e)}。请确认 Ollama 服务已启动且模型 {self.model} 已拉取。",
                model=self.model,
                finish_reason="error",
            )

        choice = completion.choices[0]
        return LLMResponse(
            content=choice.message.content or "",
            token_usage={
                "input": completion.usage.prompt_tokens if completion.usage else 0,
                "output": completion.usage.completion_tokens if completion.usage else 0,
            },
            model=completion.model,
            finish_reason=choice.finish_reason or "stop",
        )

    def stream_complete(
        self,
        system_prompt: str,
        user_prompt: str,
        tools: Optional[list[dict]] = None,
        temperature: float = 0.7,
        max_tokens: int = 4096,
    ) -> Generator[StreamEvent, None, LLMResponse]:
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ]

        kwargs = dict(
            model=self.model,
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
            stream=True,
        )

        try:
            stream = self.client.chat.completions.create(**kwargs)
        except Exception as e:
            yield StreamEvent(type="error", error_message=str(e))
            return LLMResponse(
                content=f"[Ollama Error] {str(e)}。请确认 Ollama 服务已启动且模型 {self.model} 已拉取。",
                model=self.model,
                finish_reason="error",
            )

        accumulated_text = ""
        final_model = self.model
        final_usage = {"input": 0, "output": 0}
        finish_reason = ""
        content_started = False

        for chunk in stream:
            if not chunk.choices:
                continue
            delta = chunk.choices[0].delta
            chunk_finish = chunk.choices[0].finish_reason

            if hasattr(chunk, "usage") and chunk.usage:
                final_usage["input"] = chunk.usage.prompt_tokens
                final_usage["output"] = chunk.usage.completion_tokens

            if delta.content:
                if not content_started:
                    yield StreamEvent(type="content_start")
                    content_started = True
                accumulated_text += delta.content
                yield StreamEvent(type="content_chunk", content=delta.content)

            if chunk_finish:
                finish_reason = chunk_finish
                if content_started:
                    yield StreamEvent(type="content_end")

        if not finish_reason:
            finish_reason = "stop"

        yield StreamEvent(
            type="done",
            finish_reason=finish_reason,
            token_usage=final_usage,
        )

        return LLMResponse(
            content=accumulated_text,
            token_usage=final_usage,
            model=final_model,
            finish_reason=finish_reason,
        )

    def supports_tools(self) -> bool:
        # 部分 Ollama 模型支持 tool calling（如 qwen3 某些版本）
        # 保守起见返回 False
        return False

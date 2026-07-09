"""Ollama Provider — 本地 Ollama 模型。

用法:
    from alice_engine.providers.ollama import OllamaProvider

    provider = OllamaProvider(model="qwen3:14b")
    response = provider.complete("system", "user")
"""

import os
import logging
from collections.abc import Generator
from typing import Optional

from alice_engine.providers.base import LLMProvider, LLMResponse, StreamEvent

logger = logging.getLogger(__name__)


class OllamaProvider(LLMProvider):
    """Ollama 本地模型 Provider。"""

    provider_name = "ollama"
    provider_description = "Local Ollama model provider"
    provider_supports_tools = False
    provider_supports_streaming = True

    def __init__(self, model: str = "qwen3:8b", base_url: str = ""):
        base_url = base_url or os.environ.get("OLLAMA_BASE_URL", "http://localhost:11434")

        try:
            from openai import OpenAI
        except ImportError:
            raise ImportError("请安装: pip install openai")

        self.client = OpenAI(
            base_url=f"{base_url.rstrip('/')}/v1",
            api_key="ollama"  # Ollama 不需要真实 API Key
        )
        self.model = model

    def supports_tools(self) -> bool:
        return False

    def complete(
        self,
        system_prompt: str,
        user_prompt: str,
        tools: Optional[list[dict]] = None,
        temperature: float = 0.7,
        max_tokens: int = 4096,
        **kwargs,
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
            logger.error("Ollama error: %s", e)
            return LLMResponse(
                content=f"[Ollama Error] {str(e)}。请确认 Ollama 服务已启动且模型 {self.model} 已拉取。",
                model=self.model,
                finish_reason="error",
            )

        choice = completion.choices[0]
        return LLMResponse(
            content=choice.message.content or "",
            usage={
                "input": completion.usage.prompt_tokens if completion.usage else 0,
                "output": completion.usage.completion_tokens if completion.usage else 0,
            },
            model=completion.model,
            finish_reason=choice.finish_reason or "stop",
        )

    def stream(
        self,
        system_prompt: str,
        user_prompt: str,
        tools: Optional[list[dict]] = None,
        temperature: float = 0.7,
        max_tokens: int = 4096,
        **kwargs,
    ) -> Generator[StreamEvent, None, LLMResponse]:
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ]

        try:
            stream = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
                stream=True,
            )
        except Exception as e:
            logger.error("Ollama streaming error: %s", e)
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
            usage=final_usage,
            model=final_model,
            finish_reason=finish_reason,
        )

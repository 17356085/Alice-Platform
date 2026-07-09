"""MiMo Provider — MiMo API (OpenAI-compatible)。

用法:
    from alice_engine.providers.mimo import MiMoProvider

    provider = MiMoProvider(api_key="tp-...")
    response = provider.complete("system", "user")
"""

import os
import logging
from collections.abc import Generator
from typing import Optional

from alice_engine.providers.base import LLMProvider, LLMResponse, StreamEvent

logger = logging.getLogger(__name__)


class MiMoProvider(LLMProvider):
    """MiMo API Provider (OpenAI-compatible)。"""

    provider_name = "mimo"
    provider_description = "Xiaomi MiMo OpenAI-compatible API provider"
    provider_supports_tools = True
    provider_supports_streaming = True

    BASE_URL = "https://token-plan-cn.xiaomimimo.com/v1"

    def __init__(self, model: str = "mimo-v2.5-pro", api_key: str = "", base_url: str = ""):
        api_key = api_key or os.environ.get("MIMO_API_KEY", "")
        if not api_key:
            self.client = None
            self.model = model
            return

        base_url = base_url or os.environ.get("MIMO_BASE_URL", "") or self.BASE_URL

        try:
            from openai import OpenAI
        except ImportError:
            raise ImportError("请安装: pip install openai")

        # MiMo URL already includes /v1, use as-is
        self.client = OpenAI(
            api_key=api_key,
            base_url=base_url,
        )
        self.model = model

    def supports_tools(self) -> bool:
        return True

    def complete(
        self,
        system_prompt: str,
        user_prompt: str,
        tools: Optional[list[dict]] = None,
        temperature: float = 0.7,
        max_tokens: int = 8192,
        **kwargs,
    ) -> LLMResponse:
        if self.client is None:
            return LLMResponse(content="MIMO_API_KEY 未设置", model=self.model, finish_reason="error")

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ]

        api_kwargs = dict(
            model=self.model,
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
        )

        if tools and self.supports_tools():
            api_kwargs["tools"] = tools

        try:
            completion = self.client.chat.completions.create(**api_kwargs)
        except Exception as e:
            logger.error("MiMo API error: %s", e)
            return LLMResponse(
                content=f"[MiMo API Error] {str(e)}",
                model=self.model,
                finish_reason="error",
            )

        choice = completion.choices[0]
        message = choice.message

        tool_calls = []
        if message.tool_calls:
            for tc in message.tool_calls:
                tool_calls.append({
                    "id": tc.id,
                    "name": tc.function.name,
                    "input": tc.function.arguments,
                })

        content = message.content or ""
        if not content:
            reasoning = getattr(message, "reasoning_content", None)
            if reasoning:
                content = reasoning

        return LLMResponse(
            content=content,
            tool_calls=tool_calls,
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
        max_tokens: int = 8192,
        **kwargs,
    ) -> Generator[StreamEvent, None, LLMResponse]:
        if self.client is None:
            yield StreamEvent(type="error", error_message="MIMO_API_KEY 未设置")
            return LLMResponse(content="MIMO_API_KEY 未设置", model=self.model, finish_reason="error")

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ]

        api_kwargs = dict(
            model=self.model,
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
            stream=True,
            stream_options={"include_usage": True},
        )

        if tools and self.supports_tools():
            api_kwargs["tools"] = tools

        try:
            stream = self.client.chat.completions.create(**api_kwargs)
        except Exception as e:
            logger.error("MiMo API streaming error: %s", e)
            yield StreamEvent(type="error", error_message=str(e))
            return LLMResponse(
                content=f"[MiMo API Error] {str(e)}",
                model=self.model,
                finish_reason="error",
            )

        accumulated_text = ""
        tool_calls_acc: dict[int, dict] = {}
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

            if delta.tool_calls:
                for tc in delta.tool_calls:
                    idx = tc.index
                    if idx not in tool_calls_acc:
                        tool_calls_acc[idx] = {"id": tc.id or "", "name": "", "arguments_str": ""}
                        if tc.function and tc.function.name:
                            tool_calls_acc[idx]["name"] = tc.function.name
                        if tc.id:
                            tool_calls_acc[idx]["id"] = tc.id
                        yield StreamEvent(
                            type="tool_use_start",
                            tool_name=tool_calls_acc[idx]["name"],
                            tool_id=tool_calls_acc[idx]["id"],
                        )
                    if tc.function and tc.function.arguments:
                        tool_calls_acc[idx]["arguments_str"] += tc.function.arguments
                        yield StreamEvent(
                            type="tool_input_chunk",
                            content=tc.function.arguments,
                        )

            if chunk_finish:
                finish_reason = chunk_finish
                if content_started:
                    yield StreamEvent(type="content_end")

        tool_calls = []
        import json as _json
        for idx in sorted(tool_calls_acc.keys()):
            tc = tool_calls_acc[idx]
            args_str = tc["arguments_str"]
            try:
                parsed = _json.loads(args_str) if args_str else {}
            except _json.JSONDecodeError:
                parsed = {"raw": args_str}
            yield StreamEvent(
                type="tool_use_end",
                tool_name=tc["name"],
                tool_id=tc["id"],
                tool_input=parsed,
            )
            tool_calls.append({"id": tc["id"], "name": tc["name"], "input": parsed})

        if not finish_reason:
            finish_reason = "stop"

        yield StreamEvent(
            type="done",
            finish_reason=finish_reason,
            token_usage=final_usage,
        )

        return LLMResponse(
            content=accumulated_text,
            tool_calls=tool_calls,
            usage=final_usage,
            model=final_model,
            finish_reason=finish_reason,
        )

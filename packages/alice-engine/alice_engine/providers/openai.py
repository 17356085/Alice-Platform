"""OpenAI Provider — OpenAI API。

用法:
    from alice_engine.providers.openai import OpenAIProvider

    provider = OpenAIProvider(api_key="sk-...")
    response = provider.complete("system", "user")
"""

import os
import logging
from collections.abc import Generator
from typing import Optional

from alice_engine.providers.base import LLMProvider, LLMResponse, StreamEvent

logger = logging.getLogger(__name__)

try:
    from openai import OpenAI
except ImportError:  # pragma: no cover - optional dependency
    OpenAI = None


def _resolve_name(obj, default: str = "") -> str:
    name = getattr(obj, "name", default)
    if isinstance(name, str):
        return name
    mock_name = getattr(obj, "_mock_name", "")
    if isinstance(mock_name, str) and mock_name:
        return mock_name
    return default if isinstance(default, str) else ""


class OpenAIProvider(LLMProvider):
    """OpenAI API Provider。"""

    provider_name = "openai"
    provider_description = "OpenAI API provider"
    provider_supports_tools = True
    provider_supports_streaming = True

    def __init__(self, model: str = "gpt-4o-mini", api_key: str = "", base_url: str = ""):
        api_key = api_key or os.environ.get("OPENAI_API_KEY", "")
        if not api_key:
            self.client = None
            self.model = model
            return

        if OpenAI is None:
            raise ImportError("请安装: pip install alice-engine[llm-openai]")

        kwargs = {"api_key": api_key}
        if base_url:
            kwargs["base_url"] = base_url
        self.client = OpenAI(**kwargs)
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
            return LLMResponse(content="OPENAI_API_KEY 未设置", model=self.model, finish_reason="error")

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
            logger.error("OpenAI API error: %s", e)
            return LLMResponse(
                content=f"[API Error] {str(e)}",
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
                    "name": _resolve_name(tc.function),
                    "input": tc.function.arguments,
                })

        # ★ Reasoning models (o1, etc.) may return empty content with reasoning_content
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
            yield StreamEvent(type="error", error_message="OPENAI_API_KEY 未设置")
            return LLMResponse(content="OPENAI_API_KEY 未设置", model=self.model, finish_reason="error")

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
            logger.error("OpenAI API streaming error: %s", e)
            yield StreamEvent(type="error", error_message=str(e))
            return LLMResponse(
                content=f"[API Error] {str(e)}",
                model=self.model,
                finish_reason="error",
            )

        # ── 累积状态 ──
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
                            tool_calls_acc[idx]["name"] = _resolve_name(tc.function)
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

        # ── 收尾 tool_calls ──
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

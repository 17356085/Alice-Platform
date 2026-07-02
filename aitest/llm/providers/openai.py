from typing import Optional, Literal
from collections.abc import Generator
from dataclasses import dataclass, field
import json
import time
import os
from aitest.llm.provider_base import LLMProvider, LLMResponse, StreamEvent, _get_config

# ══════════════════════════════════════════════════════════════════════════
#  OpenAI Provider
# ══════════════════════════════════════════════════════════════════════════

class OpenAIProvider(LLMProvider):
    """
    OpenAI API Provider（同时兼容 Azure OpenAI）。

    环境变量: OPENAI_API_KEY
    默认模型: gpt-4o

    使用 Azure OpenAI:
        provider = OpenAIProvider(
            model="gpt-4o",
            api_key="...",
            base_url="https://<your-resource>.openai.azure.com/openai/deployments/<deployment>/chat/completions?api-version=2024-02-01"
        )
    """

    def __init__(self, model: str = "gpt-4o", api_key: str = "", base_url: str = ""):
        api_key = api_key or _get_config().openai_api_key
        if not api_key:
            raise ValueError("OPENAI_API_KEY 未设置。请在 .env 文件或环境变量中配置。")

        try:
            from openai import OpenAI
        except ImportError:
            raise ImportError("请安装 openai: pip install openai")

        kwargs = {"api_key": api_key}
        if base_url:
            kwargs["base_url"] = base_url
        self.client = OpenAI(**kwargs)
        self.model = model

    def complete(
        self,
        system_prompt: str,
        user_prompt: str,
        tools: Optional[list[dict]] = None,
        temperature: float = 0.7,
        max_tokens: int = 8192,
    ) -> LLMResponse:
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ]

        kwargs = dict(
            model=self.model,
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
        )

        if tools and self.supports_tools():
            kwargs["tools"] = tools

        try:
            completion = self.client.chat.completions.create(**kwargs)
        except Exception as e:
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
                    "name": tc.function.name,
                    "input": tc.function.arguments,
                })

        # ★ v2.7: Reasoning models (DeepSeek-v4, o1, etc.) may return
        # empty content with reasoning_content holding the actual answer.
        content = message.content or ""
        if not content:
            reasoning = getattr(message, "reasoning_content", None)
            if reasoning:
                content = reasoning

        return LLMResponse(
            content=content,
            tool_calls=tool_calls,
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
        max_tokens: int = 8192,
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
            stream_options={"include_usage": True},
        )

        if tools and self.supports_tools():
            kwargs["tools"] = tools

        try:
            stream = self.client.chat.completions.create(**kwargs)
        except Exception as e:
            yield StreamEvent(type="error", error_message=str(e))
            return LLMResponse(
                content=f"[API Error] {str(e)}",
                model=self.model,
                finish_reason="error",
            )

        # ── 累积状态 ──
        accumulated_text = ""
        tool_calls_acc: dict[int, dict] = {}  # index → {id, name, arguments_str}
        final_model = self.model
        final_usage = {"input": 0, "output": 0}
        finish_reason = ""
        content_started = False

        for chunk in stream:
            if not chunk.choices:
                continue
            delta = chunk.choices[0].delta
            chunk_finish = chunk.choices[0].finish_reason

            # Token 使用（仅最后一个 chunk 包含，需 stream_options={"include_usage": True}）
            if hasattr(chunk, "usage") and chunk.usage:
                final_usage["input"] = chunk.usage.prompt_tokens
                final_usage["output"] = chunk.usage.completion_tokens

            # ── 文本增量 ──
            if delta.content:
                if not content_started:
                    yield StreamEvent(type="content_start")
                    content_started = True
                accumulated_text += delta.content
                yield StreamEvent(type="content_chunk", content=delta.content)

            # ── Tool call 增量 ──
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

            # ── 结束 ──
            if chunk_finish:
                finish_reason = chunk_finish
                if content_started:
                    yield StreamEvent(type="content_end")

        # ── 收尾 tool_calls ──
        tool_calls = []
        for idx in sorted(tool_calls_acc.keys()):
            tc = tool_calls_acc[idx]
            import json as _json
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
            token_usage=final_usage,
            model=final_model,
            finish_reason=finish_reason,
        )

    def supports_tools(self) -> bool:
        return True


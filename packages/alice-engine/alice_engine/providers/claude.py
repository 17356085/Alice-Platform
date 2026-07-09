"""Claude Provider — Anthropic Claude API。

用法:
    from alice_engine.providers.claude import ClaudeProvider

    provider = ClaudeProvider(api_key="sk-...")
    response = provider.complete("system", "user")
"""

import os
import logging
from collections.abc import Generator
from typing import Optional

from alice_engine.providers.base import LLMProvider, LLMResponse, StreamEvent

logger = logging.getLogger(__name__)

try:
    from anthropic import Anthropic
except ImportError:  # pragma: no cover - optional dependency
    Anthropic = None


def _resolve_name(obj, default: str = "") -> str:
    name = getattr(obj, "name", default)
    if isinstance(name, str):
        return name
    mock_name = getattr(obj, "_mock_name", "")
    if isinstance(mock_name, str) and mock_name:
        return mock_name
    return default if isinstance(default, str) else ""


class ClaudeProvider(LLMProvider):
    """Anthropic Claude API Provider。"""

    provider_name = "claude"
    provider_description = "Anthropic Claude API provider"
    provider_supports_tools = True
    provider_supports_streaming = True

    def __init__(self, model: str = "claude-sonnet-4-6", api_key: str = ""):
        api_key = api_key or os.environ.get("ANTHROPIC_API_KEY", "")
        if not api_key:
            self.client = None
            self.model = model
            return

        if Anthropic is None:
            raise ImportError("请安装: pip install alice-engine[llm-anthropic]")

        self.client = Anthropic(api_key=api_key)
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
        cache_system: bool = True,   # ★ Prompt Caching
        **kwargs,
    ) -> LLMResponse:
        if self.client is None:
            return LLMResponse(content="ANTHROPIC_API_KEY 未设置", model=self.model, finish_reason="error")

        # Build system block with Prompt Caching support
        # Threshold: ≥1024 tokens. AITest skill prompts typically 2K-5K tokens → always cacheable.
        # Cache TTL: 5 minutes. Cost reduction: 90% on cached input tokens.
        system_block = system_prompt
        if cache_system and len(system_prompt) >= 1024:
            system_block = [
                {
                    "type": "text",
                    "text": system_prompt,
                    "cache_control": {"type": "ephemeral"},
                }
            ]

        api_kwargs = dict(
            model=self.model,
            system=system_block,
            messages=[{"role": "user", "content": user_prompt}],
            temperature=temperature,
            max_tokens=max_tokens,
        )

        if tools and self.supports_tools():
            anthropic_tools = []
            for t in tools:
                func = t.get("function", t)
                params = func.get("parameters") or {}
                if not params or not params.get("type"):
                    params = {"type": "object", "properties": {}, "required": []}
                anthropic_tools.append({
                    "name": func.get("name", "unknown"),
                    "description": func.get("description", ""),
                    "input_schema": params,
                })
            api_kwargs["tools"] = anthropic_tools

        try:
            message = self.client.messages.create(**api_kwargs)
        except Exception as e:
            logger.error("Claude API error: %s", e)
            return LLMResponse(
                content=f"[API Error] {str(e)}",
                model=self.model,
                finish_reason="error",
            )

        content = ""
        tool_calls = []

        for block in message.content:
            if block.type == "text":
                content += block.text
            elif block.type == "tool_use":
                tool_calls.append({
                    "id": block.id,
                    "name": _resolve_name(block),
                    "input": block.input,
                })

        usage = message.usage
        return LLMResponse(
            content=content,
            tool_calls=tool_calls,
            usage={
                "input": usage.input_tokens if usage else 0,
                "output": usage.output_tokens if usage else 0,
                "cache_read_input_tokens": getattr(usage, 'cache_read_input_tokens', 0) if usage else 0,
                "cache_creation_input_tokens": getattr(usage, 'cache_creation_input_tokens', 0) if usage else 0,
            },
            model=message.model,
            finish_reason=message.stop_reason or "stop",
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
            yield StreamEvent(type="error", error_message="ANTHROPIC_API_KEY 未设置")
            return LLMResponse(content="ANTHROPIC_API_KEY 未设置", model=self.model, finish_reason="error")

        api_kwargs = dict(
            model=self.model,
            system=system_prompt,
            messages=[{"role": "user", "content": user_prompt}],
            temperature=temperature,
            max_tokens=max_tokens,
            stream=True,
        )

        if tools and self.supports_tools():
            anthropic_tools = []
            for t in tools:
                func = t.get("function", t)
                params = func.get("parameters") or {}
                if not params or not params.get("type"):
                    params = {"type": "object", "properties": {}, "required": []}
                anthropic_tools.append({
                    "name": func.get("name", "unknown"),
                    "description": func.get("description", ""),
                    "input_schema": params,
                })
            api_kwargs["tools"] = anthropic_tools

        try:
            stream = self.client.messages.create(**api_kwargs)
        except Exception as e:
            logger.error("Claude API streaming error: %s", e)
            yield StreamEvent(type="error", error_message=str(e))
            return LLMResponse(
                content=f"[API Error] {str(e)}",
                model=self.model,
                finish_reason="error",
            )

        # ── 累积状态 ──
        accumulated_text = ""
        tool_calls: list[dict] = []
        current_tool_name = ""
        current_tool_id = ""
        current_tool_input = ""
        final_model = self.model
        final_usage = {"input": 0, "output": 0}
        finish_reason = ""

        for event in stream:
            # ── message_start ──
            if event.type == "message_start":
                if hasattr(event, "message") and hasattr(event.message, "model"):
                    final_model = event.message.model
                if hasattr(event, "message") and hasattr(event.message, "usage"):
                    final_usage["input"] = event.message.usage.input_tokens

            # ── content_block_start ──
            elif event.type == "content_block_start":
                block = event.content_block
                if block.type == "text":
                    yield StreamEvent(type="content_start")
                elif block.type == "tool_use":
                    current_tool_name = block.name
                    current_tool_id = block.id
                    current_tool_input = ""
                    yield StreamEvent(
                        type="tool_use_start",
                        tool_name=block.name,
                        tool_id=block.id,
                    )

            # ── content_block_delta ──
            elif event.type == "content_block_delta":
                delta = event.delta
                if delta.type == "text_delta":
                    accumulated_text += delta.text
                    yield StreamEvent(type="content_chunk", content=delta.text)
                elif delta.type == "input_json_delta":
                    current_tool_input += delta.partial_json
                    yield StreamEvent(type="tool_input_chunk", content=delta.partial_json)

            # ── content_block_stop ──
            elif event.type == "content_block_stop":
                if current_tool_id:
                    import json as _json
                    try:
                        parsed_input = _json.loads(current_tool_input) if current_tool_input else {}
                    except _json.JSONDecodeError:
                        parsed_input = {"raw": current_tool_input}
                    tool_calls.append({
                        "id": current_tool_id,
                        "name": current_tool_name,
                        "input": parsed_input,
                    })
                    yield StreamEvent(
                        type="tool_use_end",
                        tool_name=current_tool_name,
                        tool_id=current_tool_id,
                        tool_input=parsed_input,
                    )
                    current_tool_id = ""
                else:
                    yield StreamEvent(type="content_end")

            # ── message_delta ──
            elif event.type == "message_delta":
                finish_reason = event.delta.stop_reason or "stop"
                if hasattr(event, "usage"):
                    final_usage["output"] = event.usage.output_tokens

        # ── 最终 done 事件 ──
        yield StreamEvent(
            type="done",
            finish_reason=finish_reason or "stop",
            token_usage=final_usage,
        )

        return LLMResponse(
            content=accumulated_text,
            tool_calls=tool_calls,
            usage=final_usage,
            model=final_model,
            finish_reason=finish_reason or "stop",
        )

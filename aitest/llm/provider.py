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
    print(response.content)
"""
import os
from pathlib import Path
from abc import ABC, abstractmethod
from collections.abc import Generator
from dataclasses import dataclass, field
from typing import Optional, Literal

# 自动加载 .env 文件（从项目根目录，确保无论从哪启动都能加载）
try:
    from dotenv import load_dotenv
    _PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
    _ENV_FILE = _PROJECT_ROOT / ".env"
    if _ENV_FILE.exists():
        load_dotenv(_ENV_FILE)
except ImportError:
    pass


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
                print(event.content, end="", flush=True)
            final = event  # 最后一次 yield 后的 return 值通过 PEP 342 不可直接取，
                           # 建议用累积方式或包装函数获取最终 LLMResponse
        """
        pass

    @abstractmethod
    def supports_tools(self) -> bool:
        """是否支持原生 tool calling / function calling。"""
        pass


# ══════════════════════════════════════════════════════════════════════════
#  Claude Provider
# ══════════════════════════════════════════════════════════════════════════

class ClaudeProvider(LLMProvider):
    """
    Anthropic Claude API Provider。

    环境变量: ANTHROPIC_API_KEY
    默认模型: claude-sonnet-4-6
    """

    def __init__(self, model: str = "claude-sonnet-4-6", api_key: str = ""):
        api_key = api_key or os.getenv("ANTHROPIC_API_KEY", "")
        if not api_key:
            raise ValueError("ANTHROPIC_API_KEY 未设置。请在 .env 文件或环境变量中配置。")

        try:
            from anthropic import Anthropic
        except ImportError:
            raise ImportError("请安装 anthropic: pip install anthropic")

        self.client = Anthropic(api_key=api_key)
        self.model = model

    def complete(
        self,
        system_prompt: str,
        user_prompt: str,
        tools: Optional[list[dict]] = None,
        temperature: float = 0.7,
        max_tokens: int = 8192,
    ) -> LLMResponse:
        kwargs = dict(
            model=self.model,
            system=system_prompt,
            messages=[{"role": "user", "content": user_prompt}],
            temperature=temperature,
            max_tokens=max_tokens,
        )

        if tools and self.supports_tools():
            # 转换 OpenAI tool format → Anthropic tool format
            anthropic_tools = []
            for t in tools:
                func = t.get("function", t)
                # DeepSeek 等兼容端点对 schema 校验严格：parameters 为空时也必须显式声明 type:object
                params = func.get("parameters") or {}
                if not params or not params.get("type"):
                    params = {"type": "object", "properties": {}, "required": []}
                anthropic_tools.append({
                    "name": func.get("name", "unknown"),
                    "description": func.get("description", ""),
                    "input_schema": params,
                })
            kwargs["tools"] = anthropic_tools

        try:
            message = self.client.messages.create(**kwargs)
        except Exception as e:
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
                    "name": block.name,
                    "input": block.input,
                })

        return LLMResponse(
            content=content,
            tool_calls=tool_calls,
            token_usage={
                "input": message.usage.input_tokens if hasattr(message, 'usage') else 0,
                "output": message.usage.output_tokens if hasattr(message, 'usage') else 0,
            },
            model=message.model,
            finish_reason=message.stop_reason or "stop",
        )

    def stream_complete(
        self,
        system_prompt: str,
        user_prompt: str,
        tools: Optional[list[dict]] = None,
        temperature: float = 0.7,
        max_tokens: int = 8192,
    ) -> Generator[StreamEvent, None, LLMResponse]:
        kwargs = dict(
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
            kwargs["tools"] = anthropic_tools

        try:
            stream = self.client.messages.create(**kwargs)
        except Exception as e:
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
                    # 解析累积的 JSON 输入
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
                else:
                    yield StreamEvent(type="content_end")

            # ── message_delta ──
            elif event.type == "message_delta":
                finish_reason = event.delta.stop_reason or "stop"
                if hasattr(event, "usage"):
                    final_usage["output"] = event.usage.output_tokens

            # ── message_stop ── (not normally reached before message_delta)
            elif event.type == "message_stop":
                pass

        # ── 最终 done 事件 ──
        yield StreamEvent(
            type="done",
            finish_reason=finish_reason or "stop",
            token_usage=final_usage,
        )

        return LLMResponse(
            content=accumulated_text,
            tool_calls=tool_calls,
            token_usage=final_usage,
            model=final_model,
            finish_reason=finish_reason or "stop",
        )

    def supports_tools(self) -> bool:
        return True


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
        api_key = api_key or os.getenv("OPENAI_API_KEY", "")
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

        return LLMResponse(
            content=message.content or "",
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
        base_url = base_url or os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")

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


# ══════════════════════════════════════════════════════════════════════════
#  DeepSeek Provider
# ══════════════════════════════════════════════════════════════════════════

class DeepSeekProvider(LLMProvider):
    """
    DeepSeek API Provider（OpenAI 兼容接口）。

    环境变量: DEEPSEEK_API_KEY
    默认模型: deepseek-chat (DeepSeek-V3)
    备选模型: deepseek-reasoner (DeepSeek-R1, 推理模型)

    用法:
        llm = get_provider("deepseek")
        llm = get_provider("deepseek", model="deepseek-reasoner")
    """

    BASE_URL = "https://api.deepseek.com"

    def __init__(self, model: str = "deepseek-chat", api_key: str = "", base_url: str = ""):
        api_key = api_key or os.getenv("DEEPSEEK_API_KEY", "")
        if not api_key:
            raise ValueError(
                "DEEPSEEK_API_KEY 未设置。请在 .env 文件或环境变量中配置。\n"
                "获取 API Key: https://platform.deepseek.com/api_keys"
            )

        try:
            from openai import OpenAI
        except ImportError:
            raise ImportError("请安装 openai: pip install openai")

        base_url = base_url or self.BASE_URL
        self.client = OpenAI(
            api_key=api_key,
            base_url=f"{base_url.rstrip('/')}/v1",
        )
        self.model = model
        self._supports_tools = self._detect_tool_support(model)

    @staticmethod
    def _detect_tool_support(model: str) -> bool:
        """Detect whether the model supports tool calling."""
        # DeepSeek-V3+ supports tool calling; R1 (reasoner) does not
        no_tool_models = {"deepseek-reasoner", "deepseek-r1"}
        return model not in no_tool_models

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

        if tools and self._supports_tools:
            kwargs["tools"] = tools

        try:
            completion = self.client.chat.completions.create(**kwargs)
        except Exception as e:
            return LLMResponse(
                content=f"[DeepSeek API Error] {str(e)}",
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

        return LLMResponse(
            content=message.content or "",
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

        if tools and self._supports_tools:
            kwargs["tools"] = tools

        try:
            stream = self.client.chat.completions.create(**kwargs)
        except Exception as e:
            yield StreamEvent(type="error", error_message=str(e))
            return LLMResponse(
                content=f"[DeepSeek API Error] {str(e)}",
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
            token_usage=final_usage,
            model=final_model,
            finish_reason=finish_reason,
        )

    def supports_tools(self) -> bool:
        return self._supports_tools


# ══════════════════════════════════════════════════════════════════════════
#  工厂函数
# ══════════════════════════════════════════════════════════════════════════

PROVIDER_REGISTRY = {
    "claude": ClaudeProvider,
    "openai": OpenAIProvider,
    "ollama": OllamaProvider,
    "deepseek": DeepSeekProvider,
}


def get_provider(name: str = "claude", **kwargs) -> LLMProvider:
    """
    工厂函数：根据名称创建 LLM Provider 实例。

    参数:
        name: Provider 名称 — "claude" | "openai" | "ollama" | "deepseek"
        **kwargs: 传递给 Provider __init__ 的额外参数（如 model, api_key, base_url）

    返回:
        LLMProvider 实例（已自动包装 tracer）

    用法:
        llm = get_provider("claude")
        llm = get_provider("openai", model="gpt-4o-mini")
        llm = get_provider("ollama", model="qwen3:14b", base_url="http://localhost:11434")
        llm = get_provider("deepseek", model="deepseek-chat")
    """
    if name not in PROVIDER_REGISTRY:
        available = list(PROVIDER_REGISTRY.keys())
        raise ValueError(f"Unknown provider: '{name}'. Available: {available}")

    instance = PROVIDER_REGISTRY[name](**kwargs)

    # P1-1: 用 tracer 装饰器包装 complete() 方法
    # 装饰器应用在工厂中，不修改 Provider 类定义，零影响子类化和测试 mock
    try:
        from aitest.trace import _trace_llm_call
        instance.complete = _trace_llm_call(instance.complete)
    except Exception:
        pass  # 追踪包装失败不影响 LLM 调用

    return instance


def list_providers() -> list[str]:
    """列出所有可用的 Provider 名称。"""
    return list(PROVIDER_REGISTRY.keys())

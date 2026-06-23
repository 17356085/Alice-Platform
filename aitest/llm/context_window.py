"""Context Window Management — 上下文窗口监控与自动续跑。

Week 1 Day 3: Token 估算 + 阈值检查 + 对话压缩 + continuation prompt。

参考:
  - Aperant session/continuation.ts (runContinuableSession, compactSessionMessages)
  - Aperant session/runner.ts (85%/90% thresholds, stream inactivity timeout)

用法:
    from aitest.llm.context_window import ContextWindowMonitor, SessionCompactor
    monitor = ContextWindowMonitor(model="claude-sonnet-4-6")
    monitor.add_usage(50000, 10000)
    if monitor.should_continue():
        compactor = SessionCompactor()
        summary = compactor.compact(messages)
"""
import re
import time
from dataclasses import dataclass, field
from typing import Optional, Callable
from enum import Enum

# ══════════════════════════════════════════════════════════════════════════
#  Model Context Limits
# ══════════════════════════════════════════════════════════════════════════

MODEL_CONTEXT_LIMITS: dict[str, int] = {
    "claude-sonnet-4-6-20250514":   200_000,
    "claude-sonnet-4-5-20250929":   200_000,
    "claude-opus-4-8-20251101":     200_000,
    "claude-haiku-4-5-20251001":    200_000,
    "claude-sonnet-4-6":            200_000,  # short name alias
    "claude-opus-4-8":              200_000,
    "deepseek-chat":                 64_000,
    "deepseek-reasoner":             64_000,
    "gpt-4o":                       128_000,
    "gpt-4o-mini":                  128_000,
}

DEFAULT_CONTEXT_LIMIT = 128_000


class WindowStatus(Enum):
    OK = "ok"
    WARN = "warn"    # 85% — 发出警告，继续运行
    HARD = "hard"    # 90% — 触发 continuation


@dataclass
class WindowState:
    estimated_tokens: int = 0
    model_limit: int = DEFAULT_CONTEXT_LIMIT
    status: WindowStatus = WindowStatus.OK
    warn_count: int = 0
    continuation_count: int = 0
    max_continuations: int = 5


# ══════════════════════════════════════════════════════════════════════════
#  ContextWindowMonitor
# ══════════════════════════════════════════════════════════════════════════

class ContextWindowMonitor:
    """上下文窗口监控器。

    追踪 Agent session 的 token 消耗，在接近窗口限制时发出警告或触发 continuation。

    用法:
        monitor = ContextWindowMonitor(model="claude-sonnet-4-6")
        monitor.add_message("system", system_prompt)
        monitor.add_message("user", user_prompt)
        status = monitor.check()  # OK / WARN / HARD
        if status == WindowStatus.HARD:
            raise ContextWindowExceededError(...)
    """

    WARN_RATIO = 0.85
    HARD_RATIO = 0.90

    def __init__(self, model: str = None, model_limit: int = None):
        self.model = model or "unknown"
        self.limit = model_limit or MODEL_CONTEXT_LIMITS.get(model, DEFAULT_CONTEXT_LIMIT)
        self._cumulative_input: int = 0
        self._cumulative_output: int = 0
        self._message_count: int = 0

    # ── Token 估算 ─────────────────────────────────────────────────

    @staticmethod
    def estimate_tokens(text: str) -> int:
        """快速估算 token 数。

        中文: ~1.5 tokens/char | 英文: ~0.25 tokens/char (4 chars/token)。
        生产环境可用 tiktoken 精确计算。
        """
        if not text:
            return 0
        chinese_chars = sum(1 for c in text if '一' <= c <= '鿿')
        other_chars = len(text) - chinese_chars
        return int(chinese_chars * 1.5 + other_chars / 4)

    # ── 计数方法 ───────────────────────────────────────────────────

    def add_message(self, role: str, content: str) -> None:
        """估算并累加一条消息的 token 数。"""
        tokens = self.estimate_tokens(content)
        self._cumulative_input += tokens
        self._message_count += 1

    def add_usage(self, input_tokens: int, output_tokens: int) -> None:
        """从 LLM API response 更新精确 token 计数。"""
        self._cumulative_input += input_tokens
        self._cumulative_output += output_tokens

    # ── 状态查询 ───────────────────────────────────────────────────

    @property
    def current_tokens(self) -> int:
        return self._cumulative_input + self._cumulative_output

    @property
    def usage_ratio(self) -> float:
        return self.current_tokens / self.limit if self.limit > 0 else 0.0

    def check(self) -> WindowStatus:
        """检查窗口状态。"""
        ratio = self.usage_ratio
        if ratio >= self.HARD_RATIO:
            return WindowStatus.HARD
        if ratio >= self.WARN_RATIO:
            return WindowStatus.WARN
        return WindowStatus.OK

    def should_continue(self) -> bool:
        """是否需要触发 continuation。"""
        return self.check() == WindowStatus.HARD

    def remaining_tokens(self) -> int:
        """剩余可用 token 估算。"""
        return max(0, self.limit - self.current_tokens)

    def status_summary(self) -> str:
        return (
            f"Context: {self.current_tokens:,}/{self.limit:,} tokens "
            f"({self.usage_ratio:.1%}) | {self._message_count} msgs | "
            f"remaining: ~{self.remaining_tokens():,}"
        )


# ══════════════════════════════════════════════════════════════════════════
#  Session Compactor — 对话压缩
# ══════════════════════════════════════════════════════════════════════════

class SessionCompactor:
    """对话压缩器 — 用便宜模型将长对话摘要为精简上下文。

    参考 Aperant continuation.ts:206-257 (compactSessionMessages):
      - 用便宜模型做摘要 (DeepSeek, ~$0.001/call)
      - 输入截断到 30K 字符
      - 输出目标 800 words
      - 失败时 fallback: raw text truncation
    """

    MAX_INPUT_CHARS = 30_000
    TARGET_WORDS = 800
    RAW_TRUNCATION_CHARS = 3_000

    SUMMARIZER_SYSTEM = (
        "You are a concise technical summarizer. Given a conversation between an AI agent "
        "and its tools, extract the key information needed to continue the work. Focus on: "
        "what has been accomplished, what files were modified, what remains to be done, "
        "and any critical decisions or findings. Use bullet points. Be thorough but concise."
    )

    def __init__(self, summarizer_provider: str = "deepseek"):
        self.summarizer_provider = summarizer_provider

    def compact(
        self,
        messages: list[dict],
        agent_memory: dict = None,
        abort_check: Callable[[], bool] = None,
    ) -> str:
        """压缩对话历史为摘要字符串。

        Args:
            messages: [{"role": "user/assistant", "content": "..."}]
            agent_memory: Agent 当前 memory 状态（可选，注入额外上下文）
            abort_check: 可选的取消检查回调

        Returns:
            摘要字符串 (800 words target)
        """
        # 1. Check abort
        if abort_check and abort_check():
            return self._raw_truncation(messages)

        # 2. Serialize + truncate
        serialized = self._serialize(messages)
        if len(serialized) > self.MAX_INPUT_CHARS:
            serialized = serialized[:self.MAX_INPUT_CHARS] + "\n\n[... truncated ...]"

        # 3. Inject memory context if available
        if agent_memory:
            mem_context = self._format_memory(agent_memory)
            serialized = mem_context + "\n\n" + serialized

        # 4. Try LLM summarization
        try:
            from aitest.llm.provider import get_provider
            llm = get_provider(self.summarizer_provider)

            prompt = (
                f"Summarize this AI agent conversation in approximately {self.TARGET_WORDS} words.\n\n"
                f"Focus on:\n"
                f"- What tasks/skills have been completed\n"
                f"- What files were created, modified, or read\n"
                f"- Key decisions made and their rationale\n"
                f"- What work remains to be done\n"
                f"- Any errors encountered and how they were resolved\n\n"
                f"## Conversation:\n{serialized}\n\n## Summary:"
            )

            response = llm.complete(self.SUMMARIZER_SYSTEM, prompt, max_tokens=1500)
            if response.content.strip() and response.finish_reason != "error":
                return response.content.strip()
        except Exception:
            pass  # Summarization failed → fallback

        return self._raw_truncation(messages)

    def _serialize(self, messages: list[dict]) -> str:
        """序列化消息列表为可读文本。取最近 50 条，每条最多 500 字符。"""
        lines = []
        for msg in messages[-50:]:
            role = msg.get("role", "unknown").upper()
            content = str(msg.get("content", ""))[:500]
            lines.append(f"[{role}]\n{content}")
        return "\n\n---\n\n".join(lines)

    def _format_memory(self, memory: dict) -> str:
        """格式化 Agent memory 为上下文。"""
        parts = []
        if memory.get("completed_skills"):
            parts.append(f"Completed skills: {memory['completed_skills']}")
        if memory.get("failed_skills"):
            parts.append(f"Failed skills: {memory['failed_skills']}")
        if memory.get("prev_output"):
            prev = str(memory["prev_output"])[:500]
            parts.append(f"Last output preview: {prev}")
        return "\n".join(parts) if parts else ""

    def _raw_truncation(self, messages: list[dict]) -> str:
        """Fallback: 截取最近 5 条消息。参考 Aperant continuation.ts:271-278。"""
        last = messages[-5:]
        text = self._serialize(last)
        if len(text) <= self.RAW_TRUNCATION_CHARS:
            return text
        return text[-self.RAW_TRUNCATION_CHARS:] + "\n\n[... truncated ...]"


# ══════════════════════════════════════════════════════════════════════════
#  Continuation Prompt Builder
# ══════════════════════════════════════════════════════════════════════════

def build_continuation_prompt(summary: str, continuation_number: int) -> str:
    """构建 continuation 提示词。

    参考 Aperant continuation.ts:288-297 (buildContinuationPrompt)。
    """
    return (
        f"## Session Continuation ({continuation_number})\n\n"
        f"You are continuing a previous session that ran out of context window space. "
        f"Here is a summary of your prior work:\n\n"
        f"{summary}\n\n"
        f"Continue where you left off. Do NOT repeat completed work. "
        f"Focus on what remains to be done."
    )


# ══════════════════════════════════════════════════════════════════════════
#  Exception
# ══════════════════════════════════════════════════════════════════════════

class ContextWindowExceededError(Exception):
    """上下文窗口超限，需要 continuation。"""
    def __init__(self, message: str, current_tokens: int = 0, limit: int = 0):
        super().__init__(message)
        self.current_tokens = current_tokens
        self.limit = limit

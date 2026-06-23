# Context Window Management — 上下文窗口管理与自动续跑

> 参考: Aperant `session/continuation.ts` — 核心 continuation 模式 (几乎可直接翻译)
>       + `session/runner.ts` — context window threshold (85%/90%) + stream inactivity timeout
> 适配: AITest LangGraph checkpoint + Python 技术栈
> 状态: v1.0-draft | 优先级: P1

## 1. 问题

### 1.1 AITest 的 SOP 场景

一个完整的 8-Agent SOP Run 典型 token 消耗：

```
Phase 1  Preflight           →  2K tokens  (metadata)
Phase 2  Project Init        →  8K tokens  (PROJECT_CONTEXT.md + module docs)
Phase 3  Requirement         → 15K tokens  (PAGE_CONTEXT + business rules)
Phase 4  Test Design         → 20K tokens  (page analysis + risk model + test cases)
Phase 5  Automation          → 30K tokens  (PO gen + script gen + code review)
Phase 6  Execution           → 25K tokens  (pytest output + Allure results)
Phase 7  Bug Analysis        → 15K tokens  (failure analysis + diagnosis)
Phase 8  Report              → 10K tokens  (report generation)
Phase 9  Knowledge           →  5K tokens  (RAG update)
                          ─────────────────
                           ~130K tokens (单页面)
                           页面数 × 130K → 4 页 ≈ 520K tokens!
```

**问题**：Claude Sonnet 上下文窗口 200K tokens。4 页面 SOP 轻松超过。

### 1.2 当前状态

AITest 完全无窗口感知：
- 不知道已消耗多少 token
- 不知道是否接近 limit
- 超了就直接报 `context_length_exceeded` 错误
- LangGraph checkpoint 存在但没有被用于 continuation

## 2. 设计

### 2.1 整体思路

参考 Aperant `continuation.ts` 的核心模式，适配 LangGraph：

```
Aperant 模式:
  runContinuableSession()
    → runAgentSession()
      → 85%: warn
      → 90%: return outcome='context_window'
    → compactSessionMessages()  ← 用 Haiku 做摘要
    → buildContinuationPrompt()  ← 注入为新 session 的 initialMessage
    → 循环 (最多 5 次)

AITest 适配:
  SOPGraph node
    → AgentLoop.run()
      → 85%: emit warning event
      → 90%: raise ContextWindowError
    → _handle_context_window()
      → compact_agent_memory()  ← 用 DeepSeek 做摘要 (便宜)
      → save_checkpoint()       ← LangGraph SqliteSaver
      → resume_with_summary()   ← 新 AgentLoop 注入摘要
      → 循环 (最多 5 次)
```

### 2.2 架构组件

```
┌─────────────────────────────────────────────────────┐
│              ContextWindowMonitor                     │
│                                                       │
│  estimate_tokens(system, user, history) → int         │
│  check_threshold(current, limit) → "ok"|"warn"|"hard"│
│  should_continue(current, limit) → bool               │
│                                                       │
│  LIMITS:                                              │
│    - claude-sonnet: 200_000                           │
│    - claude-opus:   200_000                           │
│    - claude-haiku:  200_000                           │
│    - deepseek-chat:  64_000                           │
│    - gpt-4o:        128_000                           │
│    - gpt-4o-mini:   128_000                           │
│                                                       │
│  THRESHOLDS:                                          │
│    WARN_RATIO: 0.85  (85%)                            │
│    HARD_RATIO: 0.90  (90%)                            │
└─────────────────────────────────────────────────────┘
         │
         ▼
┌─────────────────────────────────────────────────────┐
│              SessionCompactor                         │
│                                                       │
│  compact(messages, memory) → summary: str             │
│                                                       │
│  策略:                                                │
│    1. 使用便宜的 LLM 做摘要 (DeepSeek / Haiku)          │
│    2. 摘要长度目标: 800 words                          │
│    3. 失败时 fallback: 原始文本 truncation             │
│                                                       │
│  摘要内容:                                             │
│    - 已完成哪些 Skill                                   │
│    - 产出了哪些文件                                     │
│    - 关键决策和发现                                     │
│    - 待完成的工作                                       │
│    - 遇到的错误及解决方案                                │
└─────────────────────────────────────────────────────┘
         │
         ▼
┌─────────────────────────────────────────────────────┐
│              ContinuationManager                      │
│                                                       │
│  MAX_CONTINUATIONS: 5                                 │
│                                                       │
│  should_continue(outcome, count) → bool               │
│  build_prompt(summary, count) → str                   │
│  merge_results(results: list) → FinalResult           │
│                                                       │
│  终止条件:                                             │
│    - Agent 正常完成 (outcome != 'context_window')       │
│    - 达到 MAX_CONTINUATIONS                           │
│    - abort signal                                     │
│    - fatal error                                      │
└─────────────────────────────────────────────────────┘
```

### 2.3 核心类

```python
# aitest/llm/context_window.py

import time
from dataclasses import dataclass, field
from typing import Optional, Callable
from enum import Enum


# ══════════════════════════════════════════════════════════════════════════
#  Model Limits
# ══════════════════════════════════════════════════════════════════════════

MODEL_CONTEXT_LIMITS = {
    "claude-sonnet-4-6-20250514":   200_000,
    "claude-sonnet-4-5-20250929":   200_000,
    "claude-opus-4-8-20251101":     200_000,
    "claude-haiku-4-5-20251001":    200_000,
    "deepseek-chat":                 64_000,
    "deepseek-reasoner":             64_000,
    "gpt-4o":                       128_000,
    "gpt-4o-mini":                  128_000,
    "qwen3-14b":                     32_000,  # Ollama
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
        monitor.add_message(system_prompt, user_prompt)
        status = monitor.check()  # OK / WARN / HARD
    """

    WARN_RATIO = 0.85
    HARD_RATIO = 0.90

    def __init__(self, model: str = None, model_limit: int = None):
        self.model = model or "unknown"
        self.limit = model_limit or MODEL_CONTEXT_LIMITS.get(model, DEFAULT_CONTEXT_LIMIT)
        self._cumulative_input: int = 0
        self._cumulative_output: int = 0
        self._message_count: int = 0

    def estimate_tokens(self, text: str) -> int:
        """估算文本的 token 数。

        快速估算: 字符数 / 4 (英文) 或 字符数 / 2 (中文)。
        生产环境可用 tiktoken 或 Anthropic count_tokens API。

        参考: Aperant 不显式 count，而是依赖 AI SDK 的 usage 回调。
        AITest 需要自己估算，因为 Python SDK 的 usage 只在 response 中返回。
        """
        if not text:
            return 0
        # 中文字符密度更高：每个中文字符 ≈ 1.5 tokens
        chinese_chars = sum(1 for c in text if '一' <= c <= '鿿')
        other_chars = len(text) - chinese_chars
        return int(chinese_chars * 1.5 + other_chars / 4)

    def add_message(self, role: str, content: str) -> None:
        """添加一条消息到 token 计数。"""
        tokens = self.estimate_tokens(content)
        self._cumulative_input += tokens
        self._message_count += 1

    def add_usage(self, input_tokens: int, output_tokens: int) -> None:
        """从 LLM API response 更新精确 token 计数。"""
        self._cumulative_input += input_tokens
        self._cumulative_output += output_tokens

    @property
    def current_tokens(self) -> int:
        return self._cumulative_input + self._cumulative_output

    @property
    def usage_ratio(self) -> float:
        return self.current_tokens / self.limit

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

    def status_summary(self) -> str:
        return (
            f"Context window: {self.current_tokens:,}/{self.limit:,} tokens "
            f"({self.usage_ratio:.1%}) | {self._message_count} messages"
        )


# ══════════════════════════════════════════════════════════════════════════
#  Session Compactor
# ══════════════════════════════════════════════════════════════════════════

class SessionCompactor:
    """对话压缩器。

    用便宜模型 (DeepSeek) 将长对话摘要为精简上下文，供 continuation session 使用。

    参考 Aperant continuation.ts:206-257 (compactSessionMessages):
      - 用 Haiku 摘要 (AITest 用 DeepSeek，更便宜)
      - 输入截断到 30K 字符
      - 输出目标 800 words
      - 失败时 raw truncation fallback
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
            messages: 对话历史 [{"role": "user/assistant", "content": "..."}]
            agent_memory: Agent 当前 memory 状态
            abort_check: 可选的取消检查回调

        Returns:
            摘要字符串
        """
        # 1. 检查 abort
        if abort_check and abort_check():
            return self._raw_truncation(messages)

        # 2. 序列化 + 截断
        serialized = self._serialize(messages)
        if len(serialized) > self.MAX_INPUT_CHARS:
            serialized = serialized[:self.MAX_INPUT_CHARS] + "\n\n[... conversation truncated ...]"

        # 3. 尝试 LLM 摘要
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
            if response.content.strip():
                return response.content.strip()
        except Exception as e:
            # 摘要失败 → fallback 到原始截断
            pass

        return self._raw_truncation(messages)

    def _serialize(self, messages: list[dict]) -> str:
        """序列化消息列表为文本。"""
        lines = []
        for msg in messages[-50:]:  # 最近 50 条
            role = msg.get("role", "unknown").upper()
            content = msg.get("content", "")[:500]  # 每条最多 500 字符
            lines.append(f"[{role}]\n{content}")
        return "\n\n---\n\n".join(lines)

    def _raw_truncation(self, messages: list[dict]) -> str:
        """Fallback: 截取最近的消息。"""
        last = messages[-5:]  # 最近 5 条
        text = self._serialize(last)
        if len(text) <= self.RAW_TRUNCATION_CHARS:
            return text
        return text[-self.RAW_TRUNCATION_CHARS:] + "\n\n[... truncated ...]"


# ══════════════════════════════════════════════════════════════════════════
#  Continuation Prompt Builder
# ══════════════════════════════════════════════════════════════════════════

def build_continuation_prompt(summary: str, continuation_number: int) -> str:
    """构建 continuation 提示词，注入为新 session 的第一条 user message。

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
```

## 3. 与 AgentLoop 的集成

```python
# aitest/agents/agent_runner.py — 改造后

class AgentLoop:
    MAX_CONTINUATIONS = 5  # 参考 Aperant DEFAULT_MAX_CONTINUATIONS

    def __init__(self, ..., model: str = None):
        self.monitor = ContextWindowMonitor(model=model)
        self.compactor = SessionCompactor()
        self._continuation_count = 0
        self._session_messages: list[dict] = []

    def run(self) -> AgentState:
        """带 continuation 的 Agent 执行循环。"""
        while True:
            try:
                self._run_single_session()
                break  # 正常完成
            except ContextWindowExceededError:
                if self._continuation_count >= self.MAX_CONTINUATIONS:
                    self._log(f"Max continuations ({self.MAX_CONTINUATIONS}) reached. Stopping.")
                    break
                self._do_continuation()

        return self.state

    def _run_single_session(self):
        """执行单次 Agent session。"""
        for skill_id in self._remaining_skills():
            # Perceive
            system, user = self._prepare_prompts(skill_id)

            # 检查窗口
            self.monitor.add_message("system", system)
            self.monitor.add_message("user", user)
            status = self.monitor.check()

            if status == WindowStatus.HARD:
                raise ContextWindowExceededError(
                    f"Context at {self.monitor.usage_ratio:.1%}: "
                    f"{self.monitor.current_tokens:,}/{self.monitor.limit:,}"
                )
            if status == WindowStatus.WARN:
                self._log(f"[WARN] {self.monitor.status_summary()}")

            # Act
            response = self._act(system, user, skill_id)
            self.monitor.add_usage(
                response.token_usage.get("input", 0),
                response.token_usage.get("output", 0),
            )

            # 记录消息历史 (供 continuation 摘要使用)
            self._session_messages.append({"role": "user", "content": user[:500]})
            self._session_messages.append({"role": "assistant", "content": response.content[:500]})

            # Observe + Update
            self._observe(skill_id, response)
            self._update(skill_id, response)

    def _do_continuation(self):
        """执行 continuation。"""
        self._continuation_count += 1
        self._log(f"[CONTINUE] Session continuation #{self._continuation_count}...")

        # 压缩对话历史
        summary = self.compactor.compact(
            self._session_messages,
            agent_memory=self.state.memory,
        )

        # 构建 continuation prompt
        continuation_msg = build_continuation_prompt(summary, self._continuation_count)

        # 重置状态（保留 agent 进度，清空消息历史）
        self._session_messages = [{"role": "user", "content": continuation_msg}]
        self.monitor = ContextWindowMonitor(model=self.monitor.model)
        self.monitor.add_message("user", continuation_msg)

        # 设置 focused_context 为摘要（使 Agent 能快速理解上下文）
        self._focused_context = continuation_msg

        # 保存 LangGraph checkpoint (如果从 SOP Graph 调用)
        self._save_continuation_checkpoint(summary)


class ContextWindowExceededError(Exception):
    """上下文窗口超限，需要 continuation。"""
    pass
```

## 4. 与 LangGraph SOP 的集成

```python
# aitest/graphs/sop_graph.py — 增强

def _run_agent_with_continuation(state: SOPState, agent_name: str) -> dict:
    """运行 Agent，带 continuation 支持。"""
    agent = AgentLoop(
        agent_name,
        provider=state.get("provider", "claude"),
        module=state["module"],
        page=state.get("current_page", ""),
        model=state.get("model"),
    )

    try:
        result = agent.run()
    except ContextWindowExceededError:
        # Agent 层尽了最大努力 (5 次 continuation)
        # 在 SOP 层标记为需要人工介入
        return {
            "status": "needs_continuation",
            "current_phase": state["current_phase"],
            "error": "Context window exhausted after max continuations",
        }

    return {
        "status": "completed" if result.success else "failed",
        "current_phase": state["current_phase"],
    }
```

## 5. Token 估算策略对比

| 方法 | 准确性 | 性能 | 推荐场景 |
|------|--------|------|----------|
| 字符数/4 | ±50% | 极快 | 实时检查 |
| tiktoken (o200k_base) | ±5% | 快 | OpenAI 模型 |
| Anthropic count_tokens API | 精确 | 慢 (API 调用) | 关键决策点 |
| LLM SDK usage 回调 | 精确 | 无开销 | **首选** (事后累加) |

**AITest 推荐**：优先用 API response 的 `token_usage.input` 做精确累加 (post-hoc)，辅以 tiktoken 或字符估算做 pre-check。

```python
# 预检查: 快速估算 (字符法)
estimated = monitor.estimate_tokens(system + user)
if estimated > limit * 0.9:
    # 可能超限，用精确方法确认
    ...

# 事后累加: 精确计数 (API response)
monitor.add_usage(response.token_usage.input, response.token_usage.output)
```

## 6. 参考来源

| 特性 | 参考 |
|------|------|
| Continuation 循环 | Aperant `continuation.ts:95-196` — `runContinuableSession()` |
| 阈值 85%/90% | Aperant `session/runner.ts` — context window threshold monitoring |
| Haiku 摘要 | Aperant `continuation.ts:225-230` — `createProviderFromModelId('claude-haiku-4-5')` |
| Raw truncation fallback | Aperant `continuation.ts:271-278` — `rawTruncation()` |
| Continuation prompt 格式 | Aperant `continuation.ts:288-297` — `buildContinuationPrompt()` |
| MAX_CONTINUATIONS=5 | Aperant `continuation.ts:30` — `DEFAULT_MAX_CONTINUATIONS` |
| MAX_SUMMARY_INPUT=30K | Aperant `continuation.ts:33` — `MAX_SUMMARY_INPUT_CHARS` |
| LangGraph checkpoint | AITest 现有 `graphs/checkpoint.py` — `SqliteSaver` |

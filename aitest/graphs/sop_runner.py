"""
SOPRunner — 将 LangGraph SOP 图执行包装为 AgentEvent 生成器。

与 AgentLoop.run_interactive() 相同的 Generator[AgentEvent] 接口，
可直接被 chat.py 的现有 asyncio.Queue + SSE 桥接复用。

用法:
    runner = SOPRunner(module="equipment", pages=["alarm-config"])
    for event in runner.run_interactive():
        print(event.type, event.content)
"""

import json
import subprocess
import sys
import time
import queue
import uuid as _uuid
from pathlib import Path
from collections.abc import Generator

from aitest.agents.agent_runner import AgentEvent
from aitest.graphs.state import create_initial_state
from aitest.graphs.sop_graph import build_compiled_graph

# Path to sync script
_SYNC_SCRIPT = Path(__file__).resolve().parent.parent.parent / "tools" / "sync_progress.py"


# ── 节点名 → 阶段显示名 + 索引映射 ──
# 与 sop_graph.py 的 PHASE_TO_NODE 对齐
PHASE_DISPLAY: list[tuple[str, str, int]] = [
    # (node_name, display_name, 1-based index)
    ("project_agent",       "项目初始化",      1),
    ("requirement_agent",   "需求分析",        2),
    ("test_design_agent",   "测试设计",        3),
    ("automation_agent_pre","自动化(策略分析)", 4),
    ("automation_agent_post","自动化(代码生成)", 5),
    ("execution_agent",     "执行与调试",      6),
    ("bug_analysis_agent",  "Bug分析",         7),
    ("report_agent",        "报告生成",        8),
    ("knowledge_agent",     "知识沉淀",        9),
]

# 总阶段数（用于进度百分比）
TOTAL_PHASES = len(PHASE_DISPLAY)

# node_name → display_name 快速查找
_NODE_TO_DISPLAY: dict[str, str] = {n: d for n, d, _ in PHASE_DISPLAY}
_NODE_TO_INDEX: dict[str, int] = {n: i for n, _, i in PHASE_DISPLAY}


class SOPRunner:
    """
    SOP 流水线执行器 — 包装 LangGraph compiled.stream() 为 AgentEvent 流。

    与 AgentLoop 共享鸭子类型接口:
      - send_interaction(response) — 响应 HITL 中断
      - run_interactive() → Generator[AgentEvent]

    生命周期:
      1. yield sop_start
      2. 循环: compiled.stream(stream_mode="updates")
         → sop_phase(running) / sop_phase(pass|fail)
         → interaction_required (HITL 中断时) → 阻塞等待
      3. yield sop_complete
    """

    INTERACTION_TIMEOUT = 300  # 5 分钟超时

    def __init__(
        self,
        module: str,
        pages: list[str] = None,
        mode: str = "full",
        provider: str = "claude",
        run_id: str = "",
    ):
        self.module = module
        self.pages = pages or []
        self.mode = mode
        self.provider = provider
        self._interaction_queue: queue.Queue = queue.Queue()
        self._run_id = run_id or f"sop-{module}-{int(time.time())}"

    def send_interaction(self, response: str) -> None:
        """供 chat.py 的 /interact 端点调用，向暂停中的 run_interactive() 发送用户输入。"""
        self._interaction_queue.put(response)

    def run_interactive(self) -> Generator[AgentEvent, None, dict]:
        """
        执行 SOP 流水线（交互式版本）。

        yield AgentEvent 各种类型（sop_start, sop_phase, interaction_required, sop_complete）。
        最后 return 最终 state dict（成功时）或 None（异常时）。
        """
        # ── 1. 构建状态 + 编译图 ──
        initial_state = create_initial_state(
            module=self.module,
            pages=self.pages,
            mode=self.mode,
            provider=self.provider,
            run_id=self._run_id,
        )
        thread = {"configurable": {"thread_id": self._run_id}}

        try:
            compiled = build_compiled_graph()
        except Exception as e:
            yield AgentEvent(
                type="sop_complete",
                status="fail",
                content=f"SOP 图构建失败: {str(e)[:200]}",
                error=str(e),
            )
            return None

        # ── 2. 启动 ──
        yield AgentEvent(
            type="sop_start",
            content=f"🚀 SOP 流水线启动: {self.module}" +
                    (f" ({', '.join(self.pages)})" if self.pages else ""),
            progress={"step": 0, "total": TOTAL_PHASES},
        )

        # ── 3. 主循环 ──
        # 追踪哪些阶段的 "running" 事件已发出
        yielded_running: set[str] = set()
        # 追踪当前正在运行的节点
        current_node: str = ""
        # 累积的阶段摘要
        phase_summaries: list[str] = []
        # 当前 stream 迭代器
        stream = compiled.stream(initial_state, thread, stream_mode="updates")

        try:
            while True:
                try:
                    raw_event = next(stream)
                except StopIteration:
                    break

                # ── HITL 中断处理 ──
                if "__interrupt__" in raw_event:
                    interrupt_items = raw_event["__interrupt__"]
                    # Save interrupt options for timeout fallback
                    self._last_interrupt_options = ["approve"]
                    for ev in self._yield_interaction_events(interrupt_items):
                        opts = getattr(ev, 'interaction_options', []) or []
                        if opts:
                            self._last_interrupt_options = list(opts)
                        yield ev

                    # 阻塞等待用户响应
                    try:
                        response = self._interaction_queue.get(
                            timeout=self.INTERACTION_TIMEOUT
                        )
                    except queue.Empty:
                        # Smart timeout: pick most permissive option
                        opts = getattr(self, '_last_interrupt_options', ["approve"])
                        preferred = [o for o in opts if o in ("approve", "force_continue", "proceed", "accept")]
                        response = preferred[0] if preferred else (opts[0] if opts else "approve")

                    # 用 Command(resume=...) 创建新 stream 继续
                    from langgraph.types import Command
                    stream = compiled.stream(
                        Command(resume=response),
                        thread,
                        stream_mode="updates",
                    )
                    continue

                # ── 节点更新处理 ──
                for node_name, update in raw_event.items():
                    if not isinstance(update, dict):
                        continue

                    current_node = node_name

                    # 检查是否有 fatal_error
                    if update.get("fatal_error"):
                        yield AgentEvent(
                            type="sop_phase",
                            content=f"❌ 致命错误: {update['fatal_error'][:200]}",
                            status="fail",
                            progress={"step": _NODE_TO_INDEX.get(node_name, 0),
                                      "total": TOTAL_PHASES},
                            error=update["fatal_error"],
                        )
                        yield AgentEvent(
                            type="sop_complete",
                            status="failed",
                            content=f"SOP 流水线中断: {update['fatal_error'][:200]}",
                            error=update["fatal_error"],
                        )
                        return None

                    # ── 提前 yield "running"（在首次遇到该节点时）──
                    if node_name in _NODE_TO_DISPLAY and node_name not in yielded_running:
                        yielded_running.add(node_name)
                        idx = _NODE_TO_INDEX[node_name]
                        display = _NODE_TO_DISPLAY[node_name]
                        yield AgentEvent(
                            type="sop_phase",
                            content=f"运行中: {display}",
                            status="running",
                            progress={"step": idx, "total": TOTAL_PHASES},
                            skill_id=node_name,
                        )

                    # ── 提取 completed_phases / failed_phases ──
                    completed = update.get("completed_phases", [])
                    failed = update.get("failed_phases", [])

                    # 也检查 agent_outputs 中是否有阶段完成信息
                    agent_outputs = update.get("agent_outputs", {})
                    for agent_name, agent_result in agent_outputs.items():
                        if isinstance(agent_result, dict):
                            if agent_result.get("success"):
                                # 映射 agent_name → phase_name
                                phase_name = _agent_to_phase(agent_name)
                                if phase_name and phase_name not in completed:
                                    completed.append(phase_name)
                            elif agent_result.get("termination_reason"):
                                phase_name = _agent_to_phase(agent_name)
                                if phase_name and phase_name not in failed:
                                    failed.append(phase_name)

                    # 对 skip_phases 中的项 — 忽略它们（它们被有意跳过）
                    skipped = set(update.get("skip_phases", []))

                    for phase in completed:
                        if phase in skipped:
                            continue
                        idx = _phase_to_index(phase)
                        display = _phase_to_display(phase)
                        summary = f"✅ {display}: 完成"
                        phase_summaries.append(summary)
                        yield AgentEvent(
                            type="sop_phase",
                            content=summary,
                            status="pass",
                            progress={"step": idx, "total": TOTAL_PHASES},
                            skill_id=phase,
                        )

                    for phase in failed:
                        if phase in skipped:
                            continue
                        idx = _phase_to_index(phase)
                        display = _phase_to_display(phase)
                        summary = f"❌ {display}: 失败"
                        phase_summaries.append(summary)
                        yield AgentEvent(
                            type="sop_phase",
                            content=summary,
                            status="fail",
                            progress={"step": idx, "total": TOTAL_PHASES},
                            skill_id=phase,
                        )

                    # ── 检查 execution_failed 标志 ──
                    if agent_outputs.get("execution_failed"):
                        yield AgentEvent(
                            type="agent_message",
                            content="⚠️ 测试执行存在失败，将触发 Bug 分析阶段",
                        )

        except Exception as e:
            import traceback
            tb = traceback.format_exc()
            yield AgentEvent(
                type="sop_phase",
                content=f"流水线异常: {str(e)[:200]}",
                status="fail",
                error=tb[:500],
            )

        # ── 4. 完成 ──
        # 尝试获取最终状态
        try:
            final_state = compiled.get_state(thread)
            final_values = final_state.values if final_state else {}
        except Exception:
            final_values = {}

        final_status = final_values.get("status", "completed")
        all_completed = final_values.get("completed_phases", [])
        all_failed = final_values.get("failed_phases", [])

        completed_count = len(all_completed)
        failed_count = len(all_failed)
        summary = (
            f"🏁 SOP 流水线完成: {completed_count} 成功 / {failed_count} 失败\n"
            + "\n".join(phase_summaries)
            if phase_summaries
            else "无阶段执行记录"
        )

        yield AgentEvent(
            type="sop_complete",
            status="pass" if final_status == "completed" else "fail",
            content=summary,
            summary=summary,
            progress={"step": TOTAL_PHASES, "total": TOTAL_PHASES},
        )

        # ── 自动同步进度追踪 ──
        self._sync_progress()

        return final_values

    def _sync_progress(self) -> None:
        """SOP 完成后自动调用 sync_progress.py 更新 progress-tracking.md。"""
        if not _SYNC_SCRIPT.exists():
            return
        try:
            subprocess.run(
                [sys.executable, str(_SYNC_SCRIPT), "--sync-all"],
                capture_output=True,
                timeout=15,
                cwd=str(_SYNC_SCRIPT.parent.parent),
            )
        except Exception:
            pass  # Silent — sync is best-effort, don't block SOP completion

    def _yield_interaction_events(self, interrupt_items) -> Generator[AgentEvent, None, None]:
        """将 LangGraph interrupt 数据转换为 AgentEvent。"""
        for item in interrupt_items:
            # item 可能是 Interrupt 对象或原始值
            payload = getattr(item, 'value', None) or item

            if not isinstance(payload, dict):
                yield AgentEvent(
                    type="interaction_required",
                    interaction_id=f"int-{_uuid.uuid4().hex[:8]}",
                    interaction_type="approve_retry",
                    interaction_prompt=f"需要决策:\n{str(payload)[:500]}",
                    interaction_options=["approve", "reject", "skip"],
                )
                continue

            interrupt_type = payload.get("type", "approve_retry")
            iid = f"int-{_uuid.uuid4().hex[:8]}"

            # 构建用户友好的提示文本
            prompt_parts = []
            if interrupt_type == "automation_strategy_approval":
                prompt_parts.append("📋 **自动化策略审批**")
                prompt_parts.append(f"模块: {payload.get('module', '?')}")
                prompt_parts.append(f"页面: {payload.get('page', '?')}")
                strategy = payload.get("strategy_summary", "")[:400]
                if strategy:
                    prompt_parts.append(f"\n策略摘要:\n{strategy}")
                prompt_parts.append(f"\n{payload.get('hint', '请审批自动化策略')}")
            elif interrupt_type == "testcase_approval":
                prompt_parts.append("📋 **测试用例审批 (P0)**")
                prompt_parts.append(f"模块: {payload.get('module', '?')}")
                prompt_parts.append(f"页面: {payload.get('page', '?')}")
                prompt_parts.append(f"P0 用例数: {payload.get('p0_case_count', 0)}")
                prompt_parts.append(f"\n{payload.get('hint', '请审批测试用例')}")
            else:
                prompt_parts.append(f"📋 **{interrupt_type}**")
                for k, v in payload.items():
                    if k not in ("type", "options"):
                        prompt_parts.append(f"{k}: {str(v)[:200]}")

            yield AgentEvent(
                type="interaction_required",
                interaction_id=iid,
                interaction_type=interrupt_type,
                interaction_prompt="\n".join(prompt_parts),
                interaction_options=list(payload.get("options", ["approve", "reject", "skip"])),
            )


# ══════════════════════════════════════════════════════════════════════════
#  辅助映射
# ══════════════════════════════════════════════════════════════════════════

# Agent → Phase 映射（与 state.py 的 AGENT_PHASE_MAP 对齐）
_AGENT_TO_PHASE: dict[str, str] = {
    "project-agent": "Project Init",
    "requirement-agent": "Requirement",
    "test-design-agent": "Test Design",
    "automation-agent": "Automation",
    "execution-agent": "Execute & Debug",
    "bug-analysis-agent": "Bug Analysis",
    "report-agent": "Report",
    "knowledge-agent": "Knowledge",
}

# Phase → 索引
_PHASE_TO_INDEX: dict[str, int] = {
    "Project Init": 1,
    "Requirement": 2,
    "Test Design": 3,
    "Automation": 4,
    "Execute & Debug": 5,
    "Bug Analysis": 6,
    "Report": 7,
    "Knowledge": 8,
}

# Phase → 显示名
_PHASE_TO_DISPLAY: dict[str, str] = {
    "Project Init": "项目初始化",
    "Requirement": "需求分析",
    "Test Design": "测试设计",
    "Automation": "自动化",
    "Execute & Debug": "执行与调试",
    "Bug Analysis": "Bug分析",
    "Report": "报告生成",
    "Knowledge": "知识沉淀",
}


def _agent_to_phase(agent_name: str) -> str:
    return _AGENT_TO_PHASE.get(agent_name, "")


def _phase_to_index(phase_name: str) -> int:
    return _PHASE_TO_INDEX.get(phase_name, 0)


def _phase_to_display(phase_name: str) -> str:
    return _PHASE_TO_DISPLAY.get(phase_name, phase_name)

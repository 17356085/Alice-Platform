"""LangGraph 编排 — SOP 图构建和执行。"""

from __future__ import annotations

import logging
from typing import Any, Callable

logger = logging.getLogger(__name__)


class SOPGraph:
    """SOP 执行图。

    如果 langgraph 可用，使用 StateGraph 编排；
    否则退化为简单的串行执行。
    """

    def __init__(self, phases: list[str] | None = None):
        self.phases = phases or [
            "observe",      # 页面探索
            "plan",         # 测试计划
            "po_generate",  # PO 生成
            "script",       # 脚本生成
            "execute",      # 执行
            "review",       # 审查
            "gate",         # 质量门禁
            "report",       # 报告
        ]
        self._phase_handlers: dict[str, Callable] = {}

    def register_phase(self, phase: str, handler: Callable) -> None:
        """注册 phase 处理函数。"""
        self._phase_handlers[phase] = handler

    def run(self, state: dict, event_bus=None) -> dict:
        """串行执行所有 phases。

        Args:
            state: 初始状态
            event_bus: 事件总线（可选）

        Returns:
            最终状态
        """
        for phase in self.phases:
            logger.info("Phase: %s", phase)

            if event_bus:
                event_bus.emit("phase_start", {
                    "phase": phase,
                    "module": state.get("module"),
                })

            handler = self._phase_handlers.get(phase)
            if handler:
                try:
                    result = handler(state)
                    if isinstance(result, dict):
                        state.update(result)
                    state.setdefault("completed_phases", []).append(phase)
                except Exception as e:
                    logger.error("Phase %s failed: %s", phase, e)
                    state.setdefault("failed_phases", []).append(phase)
                    state["status"] = "failed"

                    if event_bus:
                        event_bus.emit("error", {
                            "phase": phase,
                            "error": str(e),
                        })
                    break
            else:
                # 无 handler 的 phase 标记为跳过
                state.setdefault("completed_phases", []).append(phase)

            if event_bus:
                event_bus.emit("phase_complete", {
                    "phase": phase,
                    "module": state.get("module"),
                    "status": state.get("status", "running"),
                })

        if state.get("status") != "failed":
            state["status"] = "completed"

        return state


def build_sop_graph(phases: list[str] | None = None) -> SOPGraph:
    """构建 SOP 图。

    如果 langgraph 可用，返回基于 StateGraph 的实现；
    否则返回简单的串行执行器。
    """
    try:
        from alice_engine._internal.langgraph_impl import build_langgraph_sop
        return build_langgraph_sop(phases)
    except ImportError:
        logger.info("langgraph not available, using simple serial executor")
        return SOPGraph(phases)

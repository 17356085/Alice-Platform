"""
Standalone Engine — 最小可运行的 SOP 执行引擎。

三层架构:
  - Core:       串行必须，SOP 编排 + Agent 执行 + LLM 调用
  - Extensions:  可插拔子引擎 (audit, complexity, knowledge, memory)
  - Platform:    不属于引擎 (Web API, Dashboard, Auth, Tenant, ...)

用法:
    from aitest.engine import Engine

    # Core only
    engine = Engine()
    result = engine.run("equipment", ["alarm-config", "camera"])

    # With Extensions
    engine = Engine()
    engine.add_extension(AuditExtension())
    result = engine.run("equipment", ["alarm-config", "camera"])
"""

import os
import logging
import time
import uuid
from pathlib import Path
from typing import Optional, Protocol

from aitest.engine.event_bus import EventBus, get_event_bus

logger = logging.getLogger(__name__)


# ── Extension 接口 ─────────────────────────────────────────────────

class EngineExtension(Protocol):
    """Engine Extension 接口。

    Extensions 在 Engine 生命周期钩子中运行:
      - on_init:       Engine 初始化后
      - on_preflight:  Preflight 完成后
      - on_phase_end:  每个 Phase 完成后
      - on_cycle_end:  整个 SOP 流水线完成后
    """

    def on_init(self, engine: "Engine") -> None:
        """Engine 初始化后调用。"""
        ...

    def on_preflight(self, module: str, preflight_result: dict) -> None:
        """Preflight 完成后调用。"""
        ...

    def on_phase_end(self, module: str, phase: str, result: dict) -> None:
        """每个 Phase 完成后调用。"""
        ...

    def on_cycle_end(self, module: str, result: dict) -> None:
        """整个 SOP 流水线完成后调用。"""
        ...


# ── Engine 类 ──────────────────────────────────────────────────────

class Engine:
    """Standalone Engine — 最小可运行的 SOP 执行引擎。

    三层架构:
      - Core:       串行必须，SOP 编排 + Agent 执行 + LLM 调用
      - Extensions:  可插拔子引擎，增强但不串入核心链路
      - Platform:    不属于引擎，Web API / Dashboard / Auth 等

    用法:
        engine = Engine()
        result = engine.run("equipment", ["alarm-config", "camera"])

    带 Extension:
        engine = Engine()
        engine.add_extension(AuditExtension())
        engine.add_extension(ComplexityExtension())
        result = engine.run("equipment", ["alarm-config", "camera"])
    """

    def __init__(
        self,
        workstudy: str = None,
        governance: str = None,
        llm_provider: str = None,
        event_bus=None,
    ):
        """
        Args:
            workstudy: 工作目录路径 (默认: 环境变量 ENGINE_WORKSTUDY 或 ".")
            governance: Governance 目录路径 (默认: workstudy/governance)
            llm_provider: LLM Provider 名称 (默认: 环境变量 LLM_PROVIDER 或 "anthropic")
            event_bus: 事件总线 (默认: 使用全局 EventBus)
        """
        self.workstudy = Path(workstudy or os.environ.get("ENGINE_WORKSTUDY", "."))
        self.governance = Path(governance or os.environ.get(
            "ENGINE_GOVERNANCE", self.workstudy / "governance"))

        # Mock LLM 模式
        if os.environ.get("MOCK_LLM") == "1":
            self.llm_provider = "mock"
            logger.info("Mock LLM mode enabled")
        else:
            self.llm_provider = llm_provider or os.environ.get("LLM_PROVIDER", "anthropic")

        self.event_bus = event_bus or get_event_bus()
        self._extensions: list = []

        # 配置路径
        os.environ["ENGINE_WORKSTUDY"] = str(self.workstudy)
        os.environ["ENGINE_GOVERNANCE"] = str(self.governance)

        # 设置 LLM Provider 环境变量
        os.environ["LLM_PROVIDER"] = self.llm_provider

        # 配置 alice_engine.workflow.state 的路径
        from alice_engine.workflow.state import configure_paths
        tlo_modules = self.workstudy / ".tlo" / "knowledge" / "modules"
        context_modules = tlo_modules if tlo_modules.exists() else self.workstudy / "context"
        configure_paths(
            workstudy=self.workstudy,
            context_modules=context_modules,
            test_project_root=self.workstudy,
        )

        logger.info("Engine initialized: workstudy=%s, governance=%s, llm=%s",
                     self.workstudy, self.governance, self.llm_provider)

    def add_extension(self, ext) -> None:
        """注册一个 Extension。

        Args:
            ext: Extension 实例，需实现 EngineExtension 协议
        """
        self._extensions.append(ext)
        ext.on_init(self)
        logger.info("Extension registered: %s", type(ext).__name__)

    @property
    def extensions(self) -> list:
        """返回已注册的 Extensions 列表。"""
        return list(self._extensions)

    def run(
        self,
        module: str,
        pages: list[str] = None,
        mode: str = "full",
        run_id: str = None,
    ) -> dict:
        """执行一次完整的 SOP 流水线。

        Args:
            module: 模块名 (如 "equipment", "tank")
            pages: 页面列表 (可选，None=自动发现)
            mode: 执行模式 (full/resume/from-automation/status)
            run_id: 运行 ID (可选，None=自动生成)

        Returns:
            {
                "status": "completed" | "completed_with_issues" | "failed",
                "run_id": str,
                "completed_phases": list[str],
                "failed_phases": list[str],
                "pages": list[str],
                "agent_outputs": dict[str, AgentResult],
            }
        """
        if run_id is None:
            run_id = f"engine-{uuid.uuid4().hex[:8]}"

        logger.info("Engine.run: module=%s, pages=%s, mode=%s, run_id=%s",
                     module, pages, mode, run_id)

        # 发布开始事件
        self.event_bus.emit("run_start", {
            "module": module,
            "pages": pages,
            "mode": mode,
            "run_id": run_id,
        })

        start_time = time.time()

        # 构建初始状态
        from aitest.graphs.state import create_initial_state
        initial_state = create_initial_state(module, pages or [], mode=mode)
        initial_state["run_id"] = run_id

        # 构建并编译图
        from alice_engine.workflow.sop_graph import build_sop_graph
        from aitest.graphs.checkpoint import get_checkpointer

        graph = build_sop_graph()
        compiled = graph.compile(checkpointer=get_checkpointer())

        # 执行
        try:
            final_state = compiled.invoke(
                initial_state,
                {"configurable": {"thread_id": run_id}},
            )
        except Exception as e:
            logger.error("Engine.run failed: %s", e, exc_info=True)
            error_result = {
                "status": "failed",
                "run_id": run_id,
                "error": str(e),
                "elapsed_seconds": round(time.time() - start_time, 2),
                "completed_phases": [],
                "failed_phases": [],
                "pages": pages or [],
                "agent_outputs": {},
            }
            self.event_bus.emit("error", {
                "error_type": "execution_failed",
                "message": str(e),
            })
            return error_result

        elapsed = time.time() - start_time

        result = {
            "status": final_state.get("status", "unknown"),
            "run_id": run_id,
            "elapsed_seconds": round(elapsed, 2),
            "completed_phases": final_state.get("completed_phases", []),
            "failed_phases": final_state.get("failed_phases", []),
            "pages": final_state.get("pages", []),
            "agent_outputs": final_state.get("agent_outputs", {}),
            "module": module,
            "mode": mode,
        }

        # Extensions: on_cycle_end
        for ext in self._extensions:
            try:
                ext.on_cycle_end(module, result)
            except Exception as e:
                logger.warning("Extension %s.on_cycle_end failed: %s",
                               type(ext).__name__, e)

        logger.info("Engine.run completed: status=%s, elapsed=%.1fs, phases=%d",
                     result["status"], elapsed, len(result["completed_phases"]))

        # 发布完成事件
        self.event_bus.emit("complete", result)

        return result

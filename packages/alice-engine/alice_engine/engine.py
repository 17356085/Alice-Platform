"""Engine — Alice 测试自动化引擎。

职责 (ADR-002):
  1. 接收任务 (Task Intake)
  2. 调度执行 (Workflow)
  3. 管理运行时 (Runtime)
  4. 返回结果 (RunResult)

三层架构:
  - Runtime Capability: Knowledge, Memory, Checkpoint, Retry, Tracing
  - Extension: Audit, Complexity, 自定义

不属于 Engine:
  - 配置解析 → Project
  - 用户交互 → CLI / Web
  - 结果存储 → Platform
  - LLM 细节 → Provider
"""

from __future__ import annotations

import asyncio
import logging
import os
import time
import uuid
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Literal

from alice_engine.events import EventBus
from alice_engine.exceptions import ProjectNotFoundError
from alice_engine.extension import EngineExtension
from alice_engine.project import Project, ValidationResult
from alice_engine.runtime import KnowledgeStore, MemoryStore
from alice_engine.workflow import configure_behavior_pack, configure_paths

logger = logging.getLogger(__name__)


@dataclass
class RunResult:
    """SOP 执行结果。"""

    status: Literal["completed", "completed_with_issues", "failed"] = "failed"
    run_id: str = ""
    module: str = ""
    pages: list[str] = field(default_factory=list)
    mode: str = "full"
    elapsed_seconds: float = 0.0
    completed_phases: list[str] = field(default_factory=list)
    failed_phases: list[str] = field(default_factory=list)
    agent_outputs: dict[str, Any] = field(default_factory=dict)
    error: str | None = None

    @property
    def success(self) -> bool:
        """是否成功完成。"""
        return self.status == "completed"


class Engine:
    """Alice 测试自动化引擎。

    三层架构:
      - Runtime: Knowledge, Memory, Checkpoint, Retry, Tracing
      - Extension: Audit, Complexity, 自定义

    用法:
        from alice_engine import Engine, Project
        from alice_engine.runtime import InMemoryKnowledgeStore, InMemoryMemoryStore

        project = Project("./my-project")
        engine = Engine(
            project=project,
            llm_provider="mock",
            knowledge=InMemoryKnowledgeStore(),
            memory=InMemoryMemoryStore(),
        )
        result = engine.run("equipment", pages=["alarm-config"])
    """

    def __init__(
        self,
        project: Project | None = None,
        project_path: str | Path | None = None,
        llm_provider: str = "anthropic",
        event_bus: EventBus | None = None,
        knowledge: KnowledgeStore | None = None,
        memory: MemoryStore | None = None,
        extensions: list[EngineExtension] | None = None,
    ):
        """初始化 Engine。

        Args:
            project: Project 实例 (推荐)
            project_path: 项目路径 (兼容旧 API)
            llm_provider: LLM Provider 名称
            event_bus: 事件总线 (Runtime)
            knowledge: 知识存储 (Runtime)
            memory: 执行记忆 (Runtime)
            extensions: 扩展列表 (被动监听)
        """
        # Project 解析
        if project is not None:
            self._project = project
        elif project_path is not None:
            self._project = Project(project_path)
        else:
            self._project = Project(".")

        self.llm_provider = llm_provider
        self.event_bus = event_bus or EventBus()
        self.knowledge = knowledge
        self.memory = memory
        self._extensions: list[EngineExtension] = []

        # 注册扩展
        if extensions:
            for ext in extensions:
                self.add_extension(ext)

        # 配置环境变量 (供内部模块使用)
        os.environ["ENGINE_WORKSTUDY"] = str(self._project.path)
        os.environ["LLM_PROVIDER"] = self.llm_provider

        # 配置行为包 + 路径（替代硬编码 governance 路径）
        self._behavior_pack = self._project.behavior_pack
        configure_behavior_pack(self._behavior_pack)
        configure_paths(
            workstudy=self._project.path,
            test_project_root=self._project.path,
        )

        # 初始化 Governance Router（统一调度入口）
        from alice_engine.router import GovernanceRouter
        self._router = GovernanceRouter(
            external_pack=self._project.governance_path if self._project.has_governance else None,
        )
        if os.environ.get("MOCK_LLM") == "1" or llm_provider == "mock":
            os.environ["MOCK_LLM"] = "1"
            self.llm_provider = "mock"

        logger.info(
            "Engine initialized: project=%s, llm=%s, knowledge=%s, memory=%s",
            self._project.name, self.llm_provider,
            type(knowledge).__name__ if knowledge else "None",
            type(memory).__name__ if memory else "None",
        )

    @property
    def project(self) -> Project:
        """当前项目。"""
        return self._project

    @property
    def router(self):
        """Governance Router — 统一调度入口。"""
        return self._router

    def add_extension(self, ext: EngineExtension) -> None:
        """注册扩展。"""
        self._extensions.append(ext)
        ext.on_init(self)
        logger.info("Extension registered: %s", type(ext).__name__)

    @property
    def extensions(self) -> list[EngineExtension]:
        """已注册的扩展列表。"""
        return list(self._extensions)

    def validate(self) -> ValidationResult:
        """验证项目配置。"""
        return self._project.validate()

    def list_modules(self) -> list[str]:
        """列出可用模块。"""
        return self._project.modules

    def run(
        self,
        module: str,
        pages: list[str] | None = None,
        mode: Literal["full", "resume", "from-automation"] = "full",
        run_id: str | None = None,
    ) -> RunResult:
        """执行一次完整的 SOP 流水线。

        Args:
            module: 模块名
            pages: 页面列表
            mode: 执行模式
            run_id: 运行 ID

        Returns:
            RunResult
        """
        if run_id is None:
            run_id = f"engine-{uuid.uuid4().hex[:8]}"

        logger.info(
            "Engine.run: module=%s, pages=%s, mode=%s, run_id=%s",
            module, pages, mode, run_id,
        )

        # Runtime: 知识检索 (执行前)
        knowledge_context = {}
        if self.knowledge:
            for page in (pages or []):
                try:
                    items = self.knowledge.search(module, page, limit=5)
                    if items:
                        knowledge_context[page] = items
                        logger.info("Knowledge: found %d items for %s/%s",
                                    len(items), module, page)
                except Exception as e:
                    logger.warning("Knowledge search failed: %s", e)

        # Runtime: 记忆检索 (执行前)
        memory_context = None
        if self.memory:
            try:
                memory_context = self.memory.get_last(module)
                if memory_context:
                    logger.info("Memory: found last run %s", memory_context.run_id)
            except Exception as e:
                logger.warning("Memory search failed: %s", e)

        # 发布开始事件
        self.event_bus.emit("run_start", {
            "module": module,
            "pages": pages,
            "mode": mode,
            "run_id": run_id,
        })

        start_time = time.time()

        try:
            from alice_engine._internal.graph import build_sop_graph

            initial_state = {
                "module": module,
                "pages": pages or [],
                "mode": mode,
                "run_id": run_id,
                "current_phase": "",
                "completed_phases": [],
                "failed_phases": [],
                "status": "running",
                "agent_outputs": {},
                "governance": {},
                "project_path": str(self._project.path),
                "knowledge_context": knowledge_context,
                "memory_context": memory_context,
            }

            graph = build_sop_graph()
            final_state = graph.run(initial_state, event_bus=self.event_bus)

        except Exception as e:
            logger.error("Engine.run failed: %s", e, exc_info=True)
            elapsed = time.time() - start_time

            error_result = RunResult(
                status="failed",
                run_id=run_id,
                module=module,
                pages=pages or [],
                mode=mode,
                elapsed_seconds=round(elapsed, 2),
                error=str(e),
            )

            self.event_bus.emit("error", {
                "error_type": "execution_failed",
                "message": str(e),
            })

            return error_result

        elapsed = time.time() - start_time

        result = RunResult(
            status=final_state.get("status", "completed"),
            run_id=run_id,
            module=module,
            pages=final_state.get("pages", pages or []),
            mode=mode,
            elapsed_seconds=round(elapsed, 2),
            completed_phases=final_state.get("completed_phases", []),
            failed_phases=final_state.get("failed_phases", []),
            agent_outputs=final_state.get("agent_outputs", {}),
        )

        # Runtime: 知识沉淀 (执行后)
        if self.knowledge:
            try:
                self.knowledge.ingest(module, result)
                logger.info("Knowledge: ingested results for %s", module)
            except Exception as e:
                logger.warning("Knowledge ingest failed: %s", e)

        # Runtime: 记忆存储 (执行后)
        if self.memory:
            try:
                self.memory.remember(module, result)
                logger.info("Memory: recorded %s", module)
            except Exception as e:
                logger.warning("Memory remember failed: %s", e)

        # Extensions: on_cycle_end (被动监听)
        for ext in self._extensions:
            try:
                ext.on_cycle_end(module, result)
            except Exception as e:
                logger.warning("Extension %s.on_cycle_end failed: %s", type(ext).__name__, e)

        logger.info(
            "Engine.run completed: status=%s, elapsed=%.1fs, phases=%d",
            result.status, elapsed, len(result.completed_phases),
        )

        self.event_bus.emit("complete", {
            "status": result.status,
            "run_id": run_id,
            "elapsed_seconds": result.elapsed_seconds,
        })

        return result

    async def run_async(
        self,
        module: str,
        pages: list[str] | None = None,
        mode: Literal["full", "resume", "from-automation"] = "full",
        run_id: str | None = None,
    ) -> RunResult:
        """异步执行 SOP 流水线。"""
        return await asyncio.to_thread(self.run, module, pages, mode, run_id)

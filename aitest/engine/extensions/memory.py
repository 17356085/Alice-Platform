"""
Testing Memory Extension — ChromaDB 向量记忆。

在 Preflight 后注入历史记忆 (已知 Bug、已覆盖场景)，
在 CycleEnd 后沉淀新记忆。

用法:
    from aitest.engine import Engine
    from aitest.engine.extensions import MemoryExtension

    engine = Engine()
    engine.add_extension(MemoryExtension())
    result = engine.run("equipment", ["alarm-config"])
"""

import logging

logger = logging.getLogger(__name__)


class MemoryExtension:
    """Testing Memory Extension — ChromaDB 向量记忆。"""

    def __init__(self, memory_types: list[str] = None):
        """
        Args:
            memory_types: 要查询的记忆类型 (默认: ["bug_pattern", "test_coverage"])
        """
        self.memory_types = memory_types or ["bug_pattern", "test_coverage"]
        self._store = None

    def _get_store(self):
        """延迟初始化 Memory Store。"""
        if self._store is None:
            try:
                from aitest.platform.testing_memory import TestingMemoryStore
                self._store = TestingMemoryStore()
            except Exception as e:
                logger.warning("TestingMemoryStore not available: %s", e)
                self._store = False
        return self._store if self._store is not False else None

    def on_init(self, engine) -> None:
        """Engine 初始化后调用。"""
        self.engine = engine

    def on_preflight(self, module: str, preflight_result: dict) -> None:
        """Preflight 后注入历史记忆。"""
        store = self._get_store()
        if not store:
            return

        try:
            pages = preflight_result.get("pages", [])
            memory_context = {}

            for mem_type in self.memory_types:
                for page_slug in pages:
                    items = store.query(
                        memory_type=mem_type,
                        module=module,
                        page=page_slug,
                        limit=3,
                    )
                    if items:
                        key = f"{mem_type}:{page_slug}"
                        memory_context[key] = items

            if memory_context:
                preflight_result["memory_context"] = memory_context
                logger.info("Memory: injected %d memory entries for %s",
                            len(memory_context), module)
        except Exception as e:
            logger.warning("Memory query failed: %s", e)

    def on_phase_end(self, module: str, phase: str, result: dict) -> None:
        """每个 Phase 完成后调用。"""
        pass

    def on_cycle_end(self, module: str, result: dict) -> None:
        """完成后沉淀新记忆。"""
        store = self._get_store()
        if not store:
            return

        try:
            # 沉淀 Agent 输出为记忆
            agent_outputs = result.get("agent_outputs", {})
            for agent_name, output in agent_outputs.items():
                if isinstance(output, dict) and output.get("success"):
                    store.add(
                        memory_type="agent_output",
                        module=module,
                        content=f"{agent_name}: {output.get('termination_reason', 'completed')}",
                        metadata={"run_id": result.get("run_id", "")},
                    )
            logger.info("Memory: stored agent outputs for module %s", module)
        except Exception as e:
            logger.warning("Memory store failed: %s", e)

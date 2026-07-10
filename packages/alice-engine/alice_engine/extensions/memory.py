"""MemoryExtension — 执行记忆检索与沉淀（使用 MemoryStore 接口）。

在 Engine 执行前检索上次执行结果，执行后记录本次结果。
帮助 Engine 了解历史执行情况，优化重试策略。

用法:
    from alice_engine import Engine, Project
    from alice_engine.extensions import MemoryExtension
    from alice_engine.runtime import InMemoryMemoryStore

    store = InMemoryMemoryStore()
    ext = MemoryExtension(store=store)
    engine = Engine(project=Project("./my-project"), extensions=[ext])
    result = engine.run("equipment", ["alarm-config"])
"""

import logging
from typing import Optional

logger = logging.getLogger(__name__)


class MemoryExtension:
    """Memory Extension — 执行历史记忆。

    使用 MemoryStore 接口，支持任意存储后端:
      - InMemoryMemoryStore (内存)
      - FileMemoryStore (JSON 文件)
      - 用户自定义实现 (SQLite, PostgreSQL, etc.)

    注意：此 Extension 与平台的 TestingMemoryStore（向量记忆）不同，
    它记录的是 RunResult 执行结果，而非语义记忆。
    """

    def __init__(self, store=None):
        """
        Args:
            store: MemoryStore 实现（如未提供则延迟初始化）
        """
        self.store = store
        self.last_memory = None  # 上次执行记录

    def _get_store(self):
        """获取或延迟初始化 Store。"""
        if self.store is None:
            # 默认使用内存存储
            from alice_engine.runtime import InMemoryMemoryStore
            self.store = InMemoryMemoryStore()
            logger.info("MemoryExtension: using InMemoryMemoryStore")
        return self.store

    def on_init(self, engine) -> None:
        """Engine 初始化后调用。"""
        self.engine = engine

    def on_phase_end(self, module: str, phase: str, result: dict) -> None:
        """每个 Phase 完成后调用。"""
        # Memory 不需要 phase-level 钩子
        pass

    def on_cycle_end(self, module: str, result) -> None:
        """完成后记录本次执行。"""
        store = self._get_store()
        if not store:
            return

        try:
            store.remember(module, result)
            logger.info("MemoryExtension: remembered result for module %s (status: %s)",
                        module, result.status)
        except Exception as e:
            logger.warning("MemoryExtension: remember failed: %s", e)

    def get_last_run(self, module: str):
        """获取某模块上次执行记录（Engine 可主动调用）。

        Args:
            module: 模块名

        Returns:
            MemoryRecord 或 None
        """
        store = self._get_store()
        if not store:
            return None

        try:
            record = store.get_last(module)
            if record:
                logger.info("MemoryExtension: found last run for %s (status: %s)",
                            module, record.status)
            return record
        except Exception as e:
            logger.warning("MemoryExtension: get_last failed: %s", e)
            return None

    def get_history(self, module: str = None, limit: int = 10):
        """获取执行历史（Engine 可主动调用）。

        Args:
            module: 模块名过滤（None=全部）
            limit: 返回数量

        Returns:
            MemoryRecord 列表
        """
        store = self._get_store()
        if not store:
            return []

        try:
            records = store.get_history(module, limit)
            logger.info("MemoryExtension: found %d history records", len(records))
            return records
        except Exception as e:
            logger.warning("MemoryExtension: get_history failed: %s", e)
            return []


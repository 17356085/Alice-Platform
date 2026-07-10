"""KnowledgeExtension — 知识检索与沉淀（使用 KnowledgeStore 接口）。

在 Engine 执行前检索历史知识，执行后沉淀新知识。
减少重复 LLM 调用，提高测试覆盖率。

用法:
    from alice_engine import Engine, Project
    from alice_engine.extensions import KnowledgeExtension
    from alice_engine.runtime import InMemoryKnowledgeStore

    store = InMemoryKnowledgeStore()
    ext = KnowledgeExtension(store=store)
    engine = Engine(project=Project("./my-project"), extensions=[ext])
    result = engine.run("equipment", ["alarm-config"])
"""

import logging
from typing import Optional

logger = logging.getLogger(__name__)


class KnowledgeExtension:
    """Knowledge Extension — 跨 Run 知识复用。

    使用 KnowledgeStore 接口，支持任意存储后端:
      - InMemoryKnowledgeStore (内存)
      - 用户自定义实现 (ChromaDB, Elasticsearch, etc.)
    """

    def __init__(self, store=None, search_limit: int = 5):
        """
        Args:
            store: KnowledgeStore 实现（如未提供则延迟初始化）
            search_limit: 检索结果数量限制 (默认: 5)
        """
        self.store = store
        self.search_limit = search_limit

    def _get_store(self):
        """获取或延迟初始化 Store。"""
        if self.store is None:
            # 默认使用内存存储
            from alice_engine.runtime import InMemoryKnowledgeStore
            self.store = InMemoryKnowledgeStore()
            logger.info("KnowledgeExtension: using InMemoryKnowledgeStore")
        return self.store

    def on_init(self, engine) -> None:
        """Engine 初始化后调用。"""
        self.engine = engine

    def on_phase_end(self, module: str, phase: str, result: dict) -> None:
        """每个 Phase 完成后调用。"""
        # Knowledge 不需要 phase-level 钩子
        pass

    def on_cycle_end(self, module: str, result) -> None:
        """完成后沉淀新知识。"""
        store = self._get_store()
        if not store:
            return

        try:
            # 沉淀执行结果为知识
            store.ingest(module, result)
            logger.info("KnowledgeExtension: ingested results for module %s", module)
        except Exception as e:
            logger.warning("KnowledgeExtension: ingest failed: %s", e)

    def search_before_run(self, module: str, pages: list[str]) -> dict:
        """执行前检索历史知识（Engine 主动调用）。

        Args:
            module: 模块名
            pages: 页面列表

        Returns:
            知识上下文 {"page_slug": [KnowledgeItem, ...]}
        """
        store = self._get_store()
        if not store:
            return {}

        knowledge_context = {}
        try:
            for page_slug in pages:
                items = store.search(module, page_slug, limit=self.search_limit)
                if items:
                    knowledge_context[page_slug] = items
                    logger.info("KnowledgeExtension: found %d items for %s/%s",
                                len(items), module, page_slug)
        except Exception as e:
            logger.warning("KnowledgeExtension: search failed: %s", e)

        return knowledge_context

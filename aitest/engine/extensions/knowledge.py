"""
Knowledge + RAG Extension — 跨 Run 知识复用。

在 Preflight 后注入历史知识，在 CycleEnd 后沉淀新知识。
减少重复 LLM 调用，提高测试覆盖率。

用法:
    from aitest.engine import Engine
    from aitest.engine.extensions import KnowledgeExtension

    engine = Engine()
    engine.add_extension(KnowledgeExtension())
    result = engine.run("equipment", ["alarm-config"])
"""

import logging

logger = logging.getLogger(__name__)


class KnowledgeExtension:
    """Knowledge + RAG Extension — 跨 Run 知识复用。"""

    def __init__(self, search_limit: int = 5):
        """
        Args:
            search_limit: 检索结果数量限制 (默认: 5)
        """
        self.search_limit = search_limit
        self._store = None

    def _get_store(self):
        """延迟初始化 RAG Store。"""
        if self._store is None:
            try:
                from aitest.knowledge.rag_engine import RAGEngine
                self._store = RAGEngine()
            except Exception as e:
                logger.warning("RAGEngine not available: %s", e)
                self._store = False  # 标记不可用
        return self._store if self._store is not False else None

    def on_init(self, engine) -> None:
        """Engine 初始化后调用。"""
        self.engine = engine

    def on_preflight(self, module: str, preflight_result: dict) -> None:
        """Preflight 后注入历史知识。"""
        store = self._get_store()
        if not store:
            return

        try:
            pages = preflight_result.get("pages", [])
            for page_slug in pages:
                relevant = store.search(module, page_slug, limit=self.search_limit)
                if relevant:
                    preflight_result.setdefault("knowledge_context", {})[page_slug] = relevant
                    logger.info("Knowledge: injected %d items for %s/%s",
                                len(relevant), module, page_slug)
        except Exception as e:
            logger.warning("Knowledge search failed: %s", e)

    def on_phase_end(self, module: str, phase: str, result: dict) -> None:
        """每个 Phase 完成后调用。"""
        pass

    def on_cycle_end(self, module: str, result: dict) -> None:
        """完成后沉淀知识。"""
        store = self._get_store()
        if not store:
            return

        try:
            store.ingest(module, result)
            logger.info("Knowledge: ingested results for module %s", module)
        except Exception as e:
            logger.warning("Knowledge ingest failed: %s", e)

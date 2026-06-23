"""Testing Memory Store — 类型化 ChromaDB CRUD。

Week 3 Day 3-4: 8个 collection，类型安全的增删查改。
"""
import json
import time
import logging
import hashlib
from pathlib import Path
from typing import Optional

from aitest.platform.testing_memory import (
    TestingMemory, MemoryType, Confidence, MemoryLifecycle,
)

logger = logging.getLogger(__name__)

# Collection metadata
COLLECTIONS = {
    "ui_patterns":         MemoryType.UI_PATTERN,
    "locator_history":     MemoryType.LOCATOR_HISTORY,
    "business_rules":      MemoryType.BUSINESS_RULE,
    "known_bugs":          MemoryType.KNOWN_BUG,
    "historical_failures": MemoryType.HISTORICAL_FAILURE,
    "page_dependencies":   MemoryType.PAGE_DEPENDENCY,
    "risk_patterns":       MemoryType.RISK_PATTERN,
    "workflow_recipes":    MemoryType.WORKFLOW_RECIPE,
}

MEMORY_TYPE_TO_COLLECTION = {v: k for k, v in COLLECTIONS.items()}


class TestingMemoryStore:
    """测试记忆存储 — ChromaDB 封装。

    用法:
        store = TestingMemoryStore()
        store.add(UIPatternMemory(component="el-table", content="..."))
        results = store.search("ui_patterns", "表格翻页测试")
    """

    def __init__(self, persist_dir: str = None):
        self._client = None
        self._persist_dir = persist_dir
        self._init_client()

    def _init_client(self):
        try:
            import chromadb
            persist = self._persist_dir or ".chroma_testing"
            self._client = chromadb.PersistentClient(path=persist)
            self._ensure_collections()
        except ImportError:
            logger.warning("chromadb not installed. TestingMemoryStore disabled.")
            self._client = None

    def _ensure_collections(self):
        if not self._client:
            return
        for name in COLLECTIONS:
            try:
                self._client.get_collection(name)
            except Exception:
                self._client.create_collection(name=name, metadata={"description": f"Testing memory: {name}"})

    def available(self) -> bool:
        return self._client is not None

    # ── CRUD ──────────────────────────────────────────────────────

    def add(self, memory: TestingMemory) -> str:
        """添加一条记忆。自动生成唯一 ID。"""
        if not self._client:
            return ""
        collection_name = MEMORY_TYPE_TO_COLLECTION.get(memory.type)
        if not collection_name:
            return ""

        memory.id = memory.id or _make_id(memory.content)
        memory.updated_at = _now()
        collection = self._client.get_collection(collection_name)

        collection.add(
            ids=[memory.id],
            documents=[memory.content],
            metadatas=[memory.to_metadata()],
        )
        logger.debug(f"Memory added: {memory.type.value} → {memory.id[:12]}...")
        return memory.id

    def get(self, memory_type: MemoryType, memory_id: str) -> Optional[TestingMemory]:
        """获取单条记忆。"""
        if not self._client:
            return None
        collection_name = MEMORY_TYPE_TO_COLLECTION.get(memory_type)
        if not collection_name:
            return None
        collection = self._client.get_collection(collection_name)
        result = collection.get(ids=[memory_id])
        if result and result["documents"]:
            return TestingMemory.from_metadata(result["documents"][0], result["metadatas"][0])
        return None

    def update(self, memory: TestingMemory) -> bool:
        """更新记忆。"""
        if not self._client or not memory.id:
            return False
        collection_name = MEMORY_TYPE_TO_COLLECTION.get(memory.type)
        if not collection_name:
            return False
        memory.updated_at = _now()
        collection = self._client.get_collection(collection_name)
        collection.update(ids=[memory.id], documents=[memory.content], metadatas=[memory.to_metadata()])
        return True

    def delete(self, memory_type: MemoryType, memory_id: str) -> bool:
        """删除单条记忆。"""
        if not self._client:
            return False
        collection_name = MEMORY_TYPE_TO_COLLECTION.get(memory_type)
        if not collection_name:
            return False
        collection = self._client.get_collection(collection_name)
        collection.delete(ids=[memory_id])
        return True

    # ── Search ────────────────────────────────────────────────────

    def search(
        self,
        collection_name: str,
        query: str,
        top_k: int = 5,
        min_confidence: Confidence = None,
    ) -> list[dict]:
        """搜索记忆。按相关性 * decay_factor 排序。"""
        if not self._client:
            return []
        try:
            collection = self._client.get_collection(collection_name)
            n = min(top_k, 20)
            results = collection.query(query_texts=[query], n_results=n)
        except Exception as e:
            logger.warning(f"Memory search failed on '{collection_name}': {e}")
            return []

        memories = []
        if not results or not results.get("documents") or not results["documents"][0]:
            return []

        for i, doc in enumerate(results["documents"][0]):
            meta = results["metadatas"][0][i] if results.get("metadatas") else {}
            dist = results["distances"][0][i] if results.get("distances") else 0

            if min_confidence:
                conf = Confidence(meta.get("confidence", "once"))
                # VERIFIED > OBSERVED_ONCE/MANUAL > INFERRED
                conf_order = {Confidence.VERIFIED: 4, Confidence.MANUAL: 3, Confidence.OBSERVED_ONCE: 2, Confidence.INFERRED: 1}
                if conf_order.get(conf, 0) < conf_order.get(min_confidence, 0):
                    continue

            decay = float(meta.get("decay_factor", 1.0))
            score = (1.0 - (dist / 2.0)) if dist else 0.5  # ChromaDB distance → 0-1 score

            memories.append({
                "content": doc,
                "metadata": meta,
                "score": round(score * decay, 3),
                "raw_distance": dist,
            })

        memories.sort(key=lambda m: m["score"], reverse=True)
        return memories[:top_k]

    def search_multi(
        self,
        queries: list[dict],
        top_k: int = 3,
    ) -> dict[str, list[dict]]:
        """跨多个 Collection 搜索。"""
        results = {}
        for q in queries:
            name = q.get("collection", "")
            query = q.get("query", "")
            if name and query:
                results[name] = self.search(name, query, top_k=top_k)
        return results

    # ── Maintenance ───────────────────────────────────────────────

    def decay_all(self):
        """全量衰减。定期调用（每次 SOP 完成后）。"""
        if not self._client:
            return
        for name in COLLECTIONS:
            try:
                collection = self._client.get_collection(name)
                all_data = collection.get()
                if not all_data or not all_data["ids"]:
                    continue
                for i, mid in enumerate(all_data["ids"]):
                    meta = all_data["metadatas"][i] if all_data.get("metadatas") else {}
                    mem = TestingMemory.from_metadata(
                        all_data["documents"][i] if all_data.get("documents") else "",
                        meta,
                    )
                    mem = MemoryLifecycle.decay(mem)
                    if MemoryLifecycle.should_delete(mem):
                        collection.delete(ids=[mid])
                    else:
                        collection.update(ids=[mid], metadatas=[mem.to_metadata()])
            except Exception as e:
                logger.debug(f"Decay failed for '{name}': {e}")

    def stats(self) -> dict:
        """返回各 collection 的统计信息。"""
        if not self._client:
            return {"status": "unavailable"}
        stats = {}
        for name in COLLECTIONS:
            try:
                collection = self._client.get_collection(name)
                count = collection.count()
                stats[name] = count
            except Exception:
                stats[name] = -1
        stats["total"] = sum(v for v in stats.values() if v > 0)
        return stats


# ══════════════════════════════════════════════════════════════════════════
#  Helpers
# ══════════════════════════════════════════════════════════════════════════

def _make_id(content: str) -> str:
    return hashlib.md5(f"{content}{time.time()}".encode()).hexdigest()[:16]

def _now() -> str:
    from datetime import datetime
    return datetime.now().isoformat()

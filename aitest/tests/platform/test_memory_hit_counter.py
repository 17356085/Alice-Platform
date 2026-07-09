"""Tests for memory hit counter (P1 — 热度驱动)。

Tests: hit_count 递增、decay_factor 提升、MemoryLifecycle.hit_boost。
No ChromaDB dependency — mocks collection operations.
"""
import pytest
from unittest.mock import MagicMock, patch, PropertyMock
from aitest.platform.testing_memory import (
    TestingMemory as MemoryItem, MemoryType, Confidence, MemoryLifecycle,
)


# ══════════════════════════════════════════════════════════════════════════
#  MemoryLifecycle.hit_boost
# ══════════════════════════════════════════════════════════════════════════


class TestHitBoost:
    def test_no_boost_below_threshold(self):
        """hit_count 未达阈值时不提升。"""
        mem = MemoryItem(
            type=MemoryType.UI_PATTERN,
            content="test",
            hit_count=3,
            decay_factor=0.5,
        )
        result = MemoryLifecycle.hit_boost(mem)
        assert result.decay_factor == 0.5  # unchanged

    def test_boost_at_threshold(self):
        """hit_count == 5 时触发提升。"""
        mem = MemoryItem(
            type=MemoryType.UI_PATTERN,
            content="test",
            hit_count=5,
            decay_factor=0.5,
        )
        result = MemoryLifecycle.hit_boost(mem)
        assert result.decay_factor == pytest.approx(0.65, abs=0.01)

    def test_boost_at_10(self):
        """hit_count == 10 时再次触发。"""
        mem = MemoryItem(
            type=MemoryType.UI_PATTERN,
            content="test",
            hit_count=10,
            decay_factor=0.7,
        )
        result = MemoryLifecycle.hit_boost(mem)
        assert result.decay_factor == pytest.approx(0.85, abs=0.01)

    def test_boost_capped_at_1(self):
        """decay_factor 上限为 1.0。"""
        mem = MemoryItem(
            type=MemoryType.UI_PATTERN,
            content="test",
            hit_count=5,
            decay_factor=0.95,
        )
        result = MemoryLifecycle.hit_boost(mem)
        assert result.decay_factor == 1.0

    def test_no_boost_at_hit_count_0(self):
        """hit_count == 0 不触发。"""
        mem = MemoryItem(
            type=MemoryType.UI_PATTERN,
            content="test",
            hit_count=0,
            decay_factor=0.5,
        )
        result = MemoryLifecycle.hit_boost(mem)
        assert result.decay_factor == 0.5

    def test_no_boost_at_7(self):
        """hit_count == 7（非 5 的倍数）不触发。"""
        mem = MemoryItem(
            type=MemoryType.UI_PATTERN,
            content="test",
            hit_count=7,
            decay_factor=0.5,
        )
        result = MemoryLifecycle.hit_boost(mem)
        assert result.decay_factor == 0.5


# ══════════════════════════════════════════════════════════════════════════
#  TestingMemory.hit_count field
# ══════════════════════════════════════════════════════════════════════════


class TestMemoryHitCountField:
    def test_default_hit_count(self):
        mem = MemoryItem(content="test")
        assert mem.hit_count == 0

    def test_hit_count_in_metadata(self):
        mem = MemoryItem(content="test", hit_count=42)
        meta = mem.to_metadata()
        assert meta["hit_count"] == 42

    def test_hit_count_from_metadata(self):
        meta = {
            "type": "ui_pattern",
            "module": "",
            "page": "",
            "confidence": "once",
            "source": "",
            "decay_factor": 1.0,
            "verify_count": 0,
            "hit_count": 17,
            "tags": "",
        }
        mem = MemoryItem.from_metadata("test", meta)
        assert mem.hit_count == 17

    def test_hit_count_missing_in_metadata_defaults_0(self):
        """旧数据没有 hit_count 字段时默认为 0。"""
        meta = {
            "type": "ui_pattern",
            "module": "",
            "page": "",
            "confidence": "once",
            "source": "",
            "decay_factor": 1.0,
            "verify_count": 0,
            "tags": "",
        }
        mem = MemoryItem.from_metadata("test", meta)
        assert mem.hit_count == 0


# ══════════════════════════════════════════════════════════════════════════
#  TestingMemoryStore.search — hit tracking (mocked ChromaDB)
# ══════════════════════════════════════════════════════════════════════════


class TestSearchHitTracking:
    """验证 search() 中的命中计数逻辑。"""

    def _make_store_with_mock(self, query_results: dict):
        """创建带 mock ChromaDB 的 TestingMemoryStore。"""
        from aitest.platform.testing_memory_store import TestingMemoryStore

        store = TestingMemoryStore.__new__(TestingMemoryStore)
        mock_client = MagicMock()
        mock_collection = MagicMock()
        mock_collection.query.return_value = query_results
        mock_client.get_collection.return_value = mock_collection
        store._client = mock_client
        return store, mock_collection

    def test_hit_count_incremented(self):
        """search() 后 hit_count 应递增。"""
        query_results = {
            "documents": [["test content"]],
            "metadatas": [[{
                "type": "ui_pattern", "module": "", "page": "",
                "confidence": "once", "source": "", "decay_factor": 1.0,
                "verify_count": 0, "hit_count": 0, "tags": "",
            }]],
            "distances": [[0.5]],
            "ids": [["mem-001"]],
        }
        store, mock_coll = self._make_store_with_mock(query_results)

        results = store.search("ui_patterns", "test query")

        assert len(results) == 1
        assert results[0]["metadata"]["hit_count"] == 1

    def test_hit_count_accumulates(self):
        """多次 search() 后 hit_count 累积。"""
        query_results = {
            "documents": [["test"]],
            "metadatas": [[{
                "type": "ui_pattern", "module": "", "page": "",
                "confidence": "once", "source": "", "decay_factor": 1.0,
                "verify_count": 0, "hit_count": 4, "tags": "",
            }]],
            "distances": [[0.5]],
            "ids": [["mem-002"]],
        }
        store, mock_coll = self._make_store_with_mock(query_results)

        results = store.search("ui_patterns", "test")
        assert results[0]["metadata"]["hit_count"] == 5  # 4 + 1

    def test_boost_triggered_at_threshold(self):
        """hit_count 达到阈值时 decay_factor 应提升。"""
        query_results = {
            "documents": [["test"]],
            "metadatas": [[{
                "type": "ui_pattern", "module": "", "page": "",
                "confidence": "once", "source": "", "decay_factor": 0.5,
                "verify_count": 0, "hit_count": 4, "tags": "",
            }]],
            "distances": [[0.5]],
            "ids": [["mem-003"]],
        }
        store, mock_coll = self._make_store_with_mock(query_results)

        results = store.search("ui_patterns", "test")
        # hit_count 4 → 5, triggers boost: 0.5 + 0.15 = 0.65
        assert results[0]["metadata"]["hit_count"] == 5
        assert results[0]["metadata"]["decay_factor"] == pytest.approx(0.65, abs=0.01)

    def test_batch_update_called(self):
        """search() 后应调用 _batch_update_hits。"""
        query_results = {
            "documents": [["test"]],
            "metadatas": [[{
                "type": "ui_pattern", "module": "", "page": "",
                "confidence": "once", "source": "", "decay_factor": 1.0,
                "verify_count": 0, "hit_count": 0, "tags": "",
            }]],
            "distances": [[0.5]],
            "ids": [["mem-004"]],
        }
        store, mock_coll = self._make_store_with_mock(query_results)

        store.search("ui_patterns", "test")
        # Verify batch update was called
        mock_coll.update.assert_called_once()

    def test_empty_results_no_update(self):
        """空结果不触发更新。"""
        query_results = {
            "documents": [[]],
            "metadatas": [[]],
            "distances": [[]],
            "ids": [[]],
        }
        store, mock_coll = self._make_store_with_mock(query_results)

        results = store.search("ui_patterns", "test")
        assert results == []
        mock_coll.update.assert_not_called()

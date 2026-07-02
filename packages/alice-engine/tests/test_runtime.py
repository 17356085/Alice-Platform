"""Runtime 单元测试。"""

import pytest
from alice_engine.runtime import (
    InMemoryKnowledgeStore,
    InMemoryMemoryStore,
    KnowledgeItem,
    MemoryRecord,
)
from alice_engine.runtime.core.retry import ReliableProvider, UsageTracker
from alice_engine.runtime.core.checkpoint import CheckpointManager
from alice_engine.runtime.core.circuit_breaker import CircuitBreaker
from alice_engine.providers import MockProvider
from alice_engine.providers.base import LLMResponse


class TestKnowledgeStore:
    """KnowledgeStore 测试。"""

    def test_search_empty(self):
        """测试空搜索。"""
        store = InMemoryKnowledgeStore()
        results = store.search("module", "page")
        assert results == []

    def test_ingest_and_search(self):
        """测试存储和搜索。"""
        store = InMemoryKnowledgeStore()

        # 创建 mock result
        class MockResult:
            run_id = "test-1"
            status = "completed"
            pages = ["page1"]
            elapsed_seconds = 1.0
            completed_phases = ["observe"]

        store.ingest("module", MockResult())
        results = store.search("module", "page1")
        assert len(results) == 1
        assert results[0].module == "module"


class TestMemoryStore:
    """MemoryStore 测试。"""

    def test_remember_and_get_last(self):
        """测试记录和获取。"""
        store = InMemoryMemoryStore()

        class MockResult:
            run_id = "test-1"
            status = "completed"
            pages = ["page1"]
            elapsed_seconds = 1.0
            completed_phases = ["observe"]
            failed_phases = []

        store.remember("module", MockResult())
        last = store.get_last("module")
        assert last is not None
        assert last.run_id == "test-1"

    def test_get_history(self):
        """测试获取历史。"""
        store = InMemoryMemoryStore()

        class MockResult:
            run_id = "test-1"
            status = "completed"
            pages = ["page1"]
            elapsed_seconds = 1.0
            completed_phases = ["observe"]
            failed_phases = []

        store.remember("module", MockResult())
        history = store.get_history("module")
        assert len(history) == 1


class TestReliableProvider:
    """ReliableProvider 测试。"""

    def test_reliable_provider_init(self):
        """测试 ReliableProvider 初始化。"""
        mock = MockProvider()
        reliable = ReliableProvider(primary=mock, max_retries=3)
        assert reliable.supports_tools() is True

    def test_reliable_provider_complete(self):
        """测试 ReliableProvider.complete()。"""
        mock = MockProvider()
        reliable = ReliableProvider(primary=mock, max_retries=3)
        response = reliable.complete("system", "user")

        assert isinstance(response, LLMResponse)
        assert response.content != ""


class TestCheckpointManager:
    """CheckpointManager 测试。"""

    def test_checkpoint_manager_init(self, tmp_path):
        """测试 CheckpointManager 初始化。"""
        manager = CheckpointManager(governance_path=tmp_path)
        assert manager.governance == tmp_path

    def test_list_runs_empty(self, tmp_path):
        """测试列出空运行。"""
        manager = CheckpointManager(governance_path=tmp_path)
        runs = manager.list_runs()
        assert runs == []

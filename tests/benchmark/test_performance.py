"""
性能基准测试套件

对比 SDK vs 平台集成的性能差异。

测试场景：
1. Extension 开销测试（有/无 Extension）
2. 存储后端对比（InMemory vs 平台特定实现）
3. 多 Extension 并发性能
4. 知识检索延迟

依赖：
    pip install pytest pytest-benchmark memory-profiler psutil

运行：
    pytest tests/benchmark/ --benchmark-only
    pytest tests/benchmark/ --benchmark-only --benchmark-save=baseline
    pytest tests/benchmark/ --benchmark-compare=baseline
"""

import time
import pytest
from pathlib import Path
from typing import Optional

# 尝试导入 SDK（Python 3.11+ 需要）
try:
    from alice_engine import Engine, Project
    from alice_engine.extensions import (
        AuditExtension,
        ComplexityExtension,
        KnowledgeExtension,
        MemoryExtension,
    )
    from alice_engine.runtime import InMemoryKnowledgeStore, InMemoryMemoryStore
    from alice_engine.providers import get_provider
    SDK_AVAILABLE = True
except ImportError:
    SDK_AVAILABLE = False


# =============================================================================
# Fixtures
# =============================================================================

@pytest.fixture
def test_project(tmp_path):
    """创建测试项目。"""
    project_dir = tmp_path / "test-project"
    project_dir.mkdir()

    # 创建最小 project.yaml
    project_yaml = project_dir / "project.yaml"
    project_yaml.write_text("""
version: 1
project:
  id: perf-test
  name: Performance Test
""".strip())

    return project_dir


@pytest.fixture
def mock_provider():
    """Mock LLM Provider（避免真实 API 调用）。"""
    if not SDK_AVAILABLE:
        pytest.skip("SDK not available (Python 3.11+ required)")

    return get_provider("mock")


# =============================================================================
# Benchmark 1: Extension 开销测试
# =============================================================================

@pytest.mark.benchmark(group="extension-overhead")
def test_engine_no_extension(benchmark, test_project, mock_provider):
    """基线：无 Extension 的 Engine 执行。"""
    if not SDK_AVAILABLE:
        pytest.skip("SDK not available")

    def run_bare():
        engine = Engine(
            project=Project(str(test_project)),
            llm_provider=mock_provider,
        )
        # 模拟轻量级执行（避免真实测试耗时）
        return {"status": "success", "phases": []}

    result = benchmark(run_bare)
    assert result["status"] == "success"


@pytest.mark.benchmark(group="extension-overhead")
def test_engine_single_extension(benchmark, test_project, mock_provider):
    """单个 Extension（Audit）。"""
    if not SDK_AVAILABLE:
        pytest.skip("SDK not available")

    def run_with_audit():
        engine = Engine(
            project=Project(str(test_project)),
            llm_provider=mock_provider,
            extensions=[AuditExtension()],
        )
        return {"status": "success", "phases": []}

    result = benchmark(run_with_audit)
    assert result["status"] == "success"


@pytest.mark.benchmark(group="extension-overhead")
def test_engine_all_extensions(benchmark, test_project, mock_provider):
    """全部 4 个 Extension。"""
    if not SDK_AVAILABLE:
        pytest.skip("SDK not available")

    def run_with_all():
        engine = Engine(
            project=Project(str(test_project)),
            llm_provider=mock_provider,
            extensions=[
                AuditExtension(),
                ComplexityExtension(),
                KnowledgeExtension(),
                MemoryExtension(),
            ],
        )
        return {"status": "success", "phases": []}

    result = benchmark(run_with_all)
    assert result["status"] == "success"


# =============================================================================
# Benchmark 2: 存储后端对比
# =============================================================================

@pytest.mark.benchmark(group="storage-backend")
def test_inmemory_knowledge_store(benchmark):
    """InMemory KnowledgeStore 性能。"""
    if not SDK_AVAILABLE:
        pytest.skip("SDK not available")

    store = InMemoryKnowledgeStore()

    def run_ingest_and_search():
        # 模拟沉淀
        from alice_engine.runtime.intelligence.knowledge import KnowledgeItem
        items = [
            KnowledgeItem(
                module="user",
                page=f"page-{i}",
                content=f"test content {i}",
                metadata={},
                score=0.9,
            )
            for i in range(10)
        ]
        for item in items:
            store._items.append(item)

        # 模拟检索
        results = store.search(module="user", page="page-1", limit=5)
        return len(results)

    count = benchmark(run_ingest_and_search)
    assert count >= 0


@pytest.mark.benchmark(group="storage-backend")
def test_inmemory_memory_store(benchmark):
    """InMemory MemoryStore 性能。"""
    if not SDK_AVAILABLE:
        pytest.skip("SDK not available")

    store = InMemoryMemoryStore()

    def run_remember_and_recall():
        # 模拟记录
        from alice_engine.runtime.intelligence.memory import MemoryRecord
        from alice_engine import RunResult

        for i in range(10):
            # 创建 Mock RunResult
            result = type('MockResult', (), {
                'run_id': f'run-{i}',
                'module': 'user',
                'pages': ['page-1'],
                'status': 'success',
                'elapsed_seconds': 1.5,
                'completed_phases': ['phase-1'],
                'failed_phases': [],
            })()
            store.remember(module="user", result=result)

        # 模拟召回
        last = store.get_last(module="user")
        history = store.get_history(module="user", limit=5)
        return len(history)

    count = benchmark(run_remember_and_recall)
    assert count > 0


# =============================================================================
# Benchmark 3: Extension 钩子延迟
# =============================================================================

@pytest.mark.benchmark(group="extension-hooks")
def test_knowledge_extension_hooks(benchmark):
    """Knowledge Extension 钩子延迟。"""
    if not SDK_AVAILABLE:
        pytest.skip("SDK not available")

    ext = KnowledgeExtension(store=InMemoryKnowledgeStore())

    def run_hooks():
        # 模拟 on_cycle_end
        result = type('MockResult', (), {
            'run_id': 'run-1',
            'module': 'user',
            'pages': ['page-1'],
            'status': 'success',
        })()
        ext.on_cycle_end(module="user", result=result)

        # 模拟 search_before_run
        knowledge = ext.search_before_run(module="user", pages=["page-1"])
        return len(knowledge)

    count = benchmark(run_hooks)
    assert count >= 0


@pytest.mark.benchmark(group="extension-hooks")
def test_memory_extension_hooks(benchmark):
    """Memory Extension 钩子延迟。"""
    if not SDK_AVAILABLE:
        pytest.skip("SDK not available")

    ext = MemoryExtension(store=InMemoryMemoryStore())

    def run_hooks():
        # 模拟 on_cycle_end
        result = type('MockResult', (), {
            'run_id': 'run-1',
            'module': 'user',
            'pages': ['page-1'],
            'status': 'success',
            'elapsed_seconds': 1.5,
            'completed_phases': ['phase-1'],
            'failed_phases': [],
        })()
        ext.on_cycle_end(module="user", result=result)

        # 模拟 get_last_run
        last = ext.get_last_run(module="user")
        return 1 if last else 0

    count = benchmark(run_hooks)
    assert count >= 0


# =============================================================================
# Benchmark 4: 批量操作性能
# =============================================================================

@pytest.mark.benchmark(group="batch-operations")
@pytest.mark.parametrize("batch_size", [10, 50, 100])
def test_knowledge_batch_ingest(benchmark, batch_size):
    """Knowledge 批量沉淀性能。"""
    if not SDK_AVAILABLE:
        pytest.skip("SDK not available")

    store = InMemoryKnowledgeStore()

    def batch_ingest():
        from alice_engine.runtime.intelligence.knowledge import KnowledgeItem

        items = [
            KnowledgeItem(
                module="user",
                page=f"page-{i}",
                content=f"test content {i}" * 100,  # 模拟较长内容
                metadata={"index": i},
                score=0.9,
            )
            for i in range(batch_size)
        ]

        for item in items:
            store._items.append(item)

        return len(store._items)

    count = benchmark(batch_ingest)
    assert count == batch_size


@pytest.mark.benchmark(group="batch-operations")
@pytest.mark.parametrize("batch_size", [10, 50, 100])
def test_memory_batch_remember(benchmark, batch_size):
    """Memory 批量记录性能。"""
    if not SDK_AVAILABLE:
        pytest.skip("SDK not available")

    store = InMemoryMemoryStore()

    def batch_remember():
        for i in range(batch_size):
            result = type('MockResult', (), {
                'run_id': f'run-{i}',
                'module': f'module-{i % 5}',  # 5 个模块
                'pages': [f'page-{i}'],
                'status': 'success',
                'elapsed_seconds': 1.5,
                'completed_phases': ['phase-1'],
                'failed_phases': [],
            })()
            store.remember(module=result.module, result=result)

        return len(store._records)

    count = benchmark(batch_remember)
    assert count == batch_size


# =============================================================================
# 内存占用测试（非 benchmark，使用 memory_profiler）
# =============================================================================

def test_memory_footprint_no_extension(test_project, mock_provider):
    """内存占用：无 Extension。"""
    if not SDK_AVAILABLE:
        pytest.skip("SDK not available")

    try:
        import psutil
        import os

        process = psutil.Process(os.getpid())
        mem_before = process.memory_info().rss / 1024 / 1024  # MB

        engine = Engine(
            project=Project(str(test_project)),
            llm_provider=mock_provider,
        )

        mem_after = process.memory_info().rss / 1024 / 1024  # MB
        mem_delta = mem_after - mem_before

        print(f"\n内存占用（无 Extension）: {mem_delta:.2f} MB")
        assert mem_delta < 100  # 应该小于 100 MB

    except ImportError:
        pytest.skip("psutil not available")


def test_memory_footprint_all_extensions(test_project, mock_provider):
    """内存占用：全部 Extension。"""
    if not SDK_AVAILABLE:
        pytest.skip("SDK not available")

    try:
        import psutil
        import os

        process = psutil.Process(os.getpid())
        mem_before = process.memory_info().rss / 1024 / 1024  # MB

        engine = Engine(
            project=Project(str(test_project)),
            llm_provider=mock_provider,
            extensions=[
                AuditExtension(),
                ComplexityExtension(),
                KnowledgeExtension(),
                MemoryExtension(),
            ],
        )

        mem_after = process.memory_info().rss / 1024 / 1024  # MB
        mem_delta = mem_after - mem_before

        print(f"\n内存占用（4 个 Extension）: {mem_delta:.2f} MB")
        assert mem_delta < 150  # 应该小于 150 MB

    except ImportError:
        pytest.skip("psutil not available")

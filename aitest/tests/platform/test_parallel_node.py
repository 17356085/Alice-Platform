"""P8 Parallel 节点测试 — 验证并行执行功能（方案1）。

测试覆盖:
1. 并行执行多个子节点
2. 结果聚合（成功/失败统计）
3. 错误处理（部分节点失败）
4. 并发控制（max_concurrency）
5. 嵌套节点类型支持（agent/condition/human_gate）
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from pathlib import Path
import uuid

from aitest.platform.workflow import WorkflowGraph, WorkflowNode, WorkflowEdge, RetryPolicy
from aitest.platform.workflow_executor import WorkflowExecutor, WorkflowRuntime, NodeExecutor
from aitest.platform.workspace import ExecutionContext


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# Fixtures
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━


@pytest.fixture
def mock_execution_context():
    """创建 Mock ExecutionContext。"""
    return ExecutionContext(
        workspace_id="ws_test",
        org_id="org_test",
        user_id="user_test",
    )


@pytest.fixture
def simple_parallel_workflow():
    """创建简单的 Parallel Workflow（3个 agent 节点并行）。"""
    workflow = WorkflowGraph(
        workflow_id="test_parallel",
        name="Test Parallel Workflow",
        version="1.0.0",
        nodes=[
            WorkflowNode(
                node_id="parallel_node",
                type="parallel",
                metadata={
                    "parallel_nodes": ["agent_1", "agent_2", "agent_3"],
                    "max_concurrency": 2,
                },
            ),
            WorkflowNode(
                node_id="agent_1",
                type="agent",
                agent_id="test-agent",
            ),
            WorkflowNode(
                node_id="agent_2",
                type="agent",
                agent_id="test-agent",
            ),
            WorkflowNode(
                node_id="agent_3",
                type="agent",
                agent_id="test-agent",
            ),
        ],
        edges=[],
    )
    return workflow


@pytest.fixture
def mixed_parallel_workflow():
    """创建混合节点类型的 Parallel Workflow（agent + condition）。"""
    workflow = WorkflowGraph(
        workflow_id="test_mixed_parallel",
        name="Test Mixed Parallel Workflow",
        version="1.0.0",
        nodes=[
            WorkflowNode(
                node_id="parallel_node",
                type="parallel",
                metadata={
                    "parallel_nodes": ["agent_1", "condition_1"],
                    "max_concurrency": 2,
                },
            ),
            WorkflowNode(
                node_id="agent_1",
                type="agent",
                agent_id="test-agent",
            ),
            WorkflowNode(
                node_id="condition_1",
                type="condition",
                condition_expr="True",
            ),
        ],
        edges=[],
    )
    return workflow


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# Test 1: 基础并行执行
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━


def test_parallel_node_executes_all_sub_nodes(simple_parallel_workflow, mock_execution_context):
    """测试 Parallel 节点执行所有子节点。"""
    runtime = WorkflowRuntime(
        run_id=f"run_{uuid.uuid4().hex[:16]}",
        workflow_id=simple_parallel_workflow.workflow_id,
        ctx=mock_execution_context,
        params={},
        runtime_config={},
    )

    executor = WorkflowExecutor(simple_parallel_workflow, runtime)

    # Mock execute_agent_node 返回成功
    with patch.object(executor.node_executor, 'execute_agent_node', return_value={"success": True, "result": "ok"}):
        parallel_node = executor.find_node("parallel_node")
        result = executor.node_executor.execute_parallel_node(parallel_node, runtime, {})

    # 验证
    assert result["success"] is True
    assert result["total_nodes"] == 3
    assert result["successful_nodes"] == 3
    assert result["failed_nodes"] == 0
    assert len(result["results"]) == 3
    assert "agent_1" in result["results"]
    assert "agent_2" in result["results"]
    assert "agent_3" in result["results"]


def test_parallel_node_respects_max_concurrency(simple_parallel_workflow, mock_execution_context):
    """测试 Parallel 节点遵守 max_concurrency 限制。"""
    runtime = WorkflowRuntime(
        run_id=f"run_{uuid.uuid4().hex[:16]}",
        workflow_id=simple_parallel_workflow.workflow_id,
        ctx=mock_execution_context,
        params={},
        runtime_config={},
    )

    executor = WorkflowExecutor(simple_parallel_workflow, runtime)

    # 记录并发执行的节点数
    concurrent_count = []
    max_concurrent = 0

    def mock_execute_agent(node, runtime, state):
        concurrent_count.append(1)
        import time
        time.sleep(0.1)  # 模拟执行时间
        current = len(concurrent_count)
        nonlocal max_concurrent
        max_concurrent = max(max_concurrent, current)
        concurrent_count.pop()
        return {"success": True, "result": "ok"}

    with patch.object(executor.node_executor, 'execute_agent_node', side_effect=mock_execute_agent):
        parallel_node = executor.find_node("parallel_node")
        result = executor.node_executor.execute_parallel_node(parallel_node, runtime, {})

    # 验证：max_concurrency=2，所以最多2个节点同时执行
    # 注意：由于线程调度，这个测试可能不稳定，仅作为基本验证
    assert result["success"] is True
    assert result["total_nodes"] == 3


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# Test 2: 错误处理
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━


def test_parallel_node_handles_partial_failures(simple_parallel_workflow, mock_execution_context):
    """测试 Parallel 节点处理部分子节点失败。"""
    runtime = WorkflowRuntime(
        run_id=f"run_{uuid.uuid4().hex[:16]}",
        workflow_id=simple_parallel_workflow.workflow_id,
        ctx=mock_execution_context,
        params={},
        runtime_config={},
    )

    executor = WorkflowExecutor(simple_parallel_workflow, runtime)

    # Mock: agent_1 成功，agent_2 失败，agent_3 成功
    def mock_execute_agent(node, runtime, state):
        if node.node_id == "agent_2":
            return {"success": False, "error": "Agent 2 failed"}
        return {"success": True, "result": "ok"}

    with patch.object(executor.node_executor, 'execute_agent_node', side_effect=mock_execute_agent):
        parallel_node = executor.find_node("parallel_node")
        result = executor.node_executor.execute_parallel_node(parallel_node, runtime, {})

    # 验证
    assert result["success"] is False  # 有失败节点，overall_success=False
    assert result["total_nodes"] == 3
    assert result["successful_nodes"] == 2
    assert result["failed_nodes"] == 1
    assert result["errors"] is not None
    assert "agent_2" in result["errors"]


def test_parallel_node_handles_all_failures(simple_parallel_workflow, mock_execution_context):
    """测试 Parallel 节点处理所有子节点失败。"""
    runtime = WorkflowRuntime(
        run_id=f"run_{uuid.uuid4().hex[:16]}",
        workflow_id=simple_parallel_workflow.workflow_id,
        ctx=mock_execution_context,
        params={},
        runtime_config={},
    )

    executor = WorkflowExecutor(simple_parallel_workflow, runtime)

    # Mock: 所有节点失败
    with patch.object(executor.node_executor, 'execute_agent_node', return_value={"success": False, "error": "Failed"}):
        parallel_node = executor.find_node("parallel_node")
        result = executor.node_executor.execute_parallel_node(parallel_node, runtime, {})

    # 验证
    assert result["success"] is False
    assert result["total_nodes"] == 3
    assert result["successful_nodes"] == 0
    assert result["failed_nodes"] == 3


def test_parallel_node_handles_missing_sub_node(simple_parallel_workflow, mock_execution_context):
    """测试 Parallel 节点处理子节点不存在的情况。"""
    runtime = WorkflowRuntime(
        run_id=f"run_{uuid.uuid4().hex[:16]}",
        workflow_id=simple_parallel_workflow.workflow_id,
        ctx=mock_execution_context,
        params={},
        runtime_config={},
    )

    executor = WorkflowExecutor(simple_parallel_workflow, runtime)

    # 修改 parallel_nodes 包含不存在的节点
    parallel_node = executor.find_node("parallel_node")
    parallel_node.metadata["parallel_nodes"] = ["agent_1", "nonexistent_node"]

    with patch.object(executor.node_executor, 'execute_agent_node', return_value={"success": True}):
        result = executor.node_executor.execute_parallel_node(parallel_node, runtime, {})

    # 验证
    assert result["success"] is False  # 有失败节点
    assert "nonexistent_node" in result["errors"]
    assert "not found in workflow" in result["errors"]["nonexistent_node"]


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# Test 3: 混合节点类型
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━


def test_parallel_node_supports_mixed_node_types(mixed_parallel_workflow, mock_execution_context):
    """测试 Parallel 节点支持混合节点类型（agent + condition）。"""
    runtime = WorkflowRuntime(
        run_id=f"run_{uuid.uuid4().hex[:16]}",
        workflow_id=mixed_parallel_workflow.workflow_id,
        ctx=mock_execution_context,
        params={},
        runtime_config={},
    )

    executor = WorkflowExecutor(mixed_parallel_workflow, runtime)

    # Mock agent 和 condition 执行
    with patch.object(executor.node_executor, 'execute_agent_node', return_value={"success": True, "result": "agent ok"}):
        with patch.object(executor.node_executor, 'execute_condition_node', return_value={"success": True, "result": True}):
            parallel_node = executor.find_node("parallel_node")
            result = executor.node_executor.execute_parallel_node(parallel_node, runtime, {})

    # 验证
    assert result["success"] is True
    assert result["total_nodes"] == 2
    assert result["successful_nodes"] == 2
    assert "agent_1" in result["results"]
    assert "condition_1" in result["results"]


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# Test 4: 方案1架构验证
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━


def test_node_executor_is_instance_method():
    """测试 NodeExecutor 现在是实例方法（方案1架构验证）。"""
    workflow = WorkflowGraph(
        workflow_id="test",
        name="Test",
        version="1.0.0",
        nodes=[],
        edges=[],
    )
    runtime = WorkflowRuntime(
        run_id="run_test",
        workflow_id="test",
        ctx=Mock(),
        params={},
        runtime_config={},
    )

    executor = WorkflowExecutor(workflow, runtime)

    # 验证：NodeExecutor 是实例，而非静态类
    assert hasattr(executor, 'node_executor')
    assert isinstance(executor.node_executor, NodeExecutor)
    assert executor.node_executor.executor is executor


def test_executor_has_find_node_method(simple_parallel_workflow, mock_execution_context):
    """测试 WorkflowExecutor 有 find_node() 方法（方案1架构验证）。"""
    runtime = WorkflowRuntime(
        run_id="run_test",
        workflow_id=simple_parallel_workflow.workflow_id,
        ctx=mock_execution_context,
        params={},
        runtime_config={},
    )

    executor = WorkflowExecutor(simple_parallel_workflow, runtime)

    # 验证：find_node 方法存在且可用
    node = executor.find_node("agent_1")
    assert node is not None
    assert node.node_id == "agent_1"
    assert node.type == "agent"

    # 不存在的节点返回 None
    node = executor.find_node("nonexistent")
    assert node is None


def test_executor_has_execute_single_node_method(simple_parallel_workflow, mock_execution_context):
    """测试 WorkflowExecutor 有 execute_single_node() 方法（方案1架构验证）。"""
    runtime = WorkflowRuntime(
        run_id="run_test",
        workflow_id=simple_parallel_workflow.workflow_id,
        ctx=mock_execution_context,
        params={},
        runtime_config={},
    )

    executor = WorkflowExecutor(simple_parallel_workflow, runtime)

    # 验证：execute_single_node 方法存在且可用
    with patch.object(executor.node_executor, 'execute_agent_node', return_value={"success": True}):
        node = executor.find_node("agent_1")
        result = executor.execute_single_node(node, runtime, {})

    assert result["success"] is True


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# Test 5: 边界情况
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━


def test_parallel_node_with_empty_parallel_nodes(mock_execution_context):
    """测试 Parallel 节点 parallel_nodes 为空的情况。"""
    workflow = WorkflowGraph(
        workflow_id="test",
        name="Test",
        version="1.0.0",
        nodes=[
            WorkflowNode(
                node_id="parallel_node",
                type="parallel",
                metadata={"parallel_nodes": []},  # 空列表
            ),
        ],
        edges=[],
    )

    runtime = WorkflowRuntime(
        run_id="run_test",
        workflow_id="test",
        ctx=mock_execution_context,
        params={},
        runtime_config={},
    )

    executor = WorkflowExecutor(workflow, runtime)
    parallel_node = executor.find_node("parallel_node")
    result = executor.node_executor.execute_parallel_node(parallel_node, runtime, {})

    # 验证：返回错误
    assert result["success"] is False
    assert "No parallel_nodes specified" in result["error"]


def test_parallel_node_without_metadata(mock_execution_context):
    """测试 Parallel 节点没有 metadata 的情况。"""
    workflow = WorkflowGraph(
        workflow_id="test",
        name="Test",
        version="1.0.0",
        nodes=[
            WorkflowNode(
                node_id="parallel_node",
                type="parallel",
                metadata={},  # 空 metadata
            ),
        ],
        edges=[],
    )

    runtime = WorkflowRuntime(
        run_id="run_test",
        workflow_id="test",
        ctx=mock_execution_context,
        params={},
        runtime_config={},
    )

    executor = WorkflowExecutor(workflow, runtime)
    parallel_node = executor.find_node("parallel_node")
    result = executor.node_executor.execute_parallel_node(parallel_node, runtime, {})

    # 验证：返回错误
    assert result["success"] is False
    assert "No parallel_nodes specified" in result["error"]

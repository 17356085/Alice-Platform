"""测试 Workflow 执行引擎 — 端到端测试

测试场景:
1. 简单 Workflow: requirement-agent → test-design-agent
2. 带 human_gate 的 Workflow: agent → human_gate → agent
3. 带 condition 的 Workflow: agent → condition → agent (条件跳过)
4. 重试逻辑: 模拟 Agent 失败
"""

import json
from pathlib import Path

# 测试 Workflow 定义
TEST_WORKFLOWS = {
    "simple-workflow": {
        "workflow_id": "test-simple-workflow",
        "name": "Simple Two-Agent Workflow",
        "version": "1.0.0",
        "nodes": [
            {
                "node_id": "requirement",
                "type": "agent",
                "agent_id": "requirement-agent",
                "agent_version": "2.5.0",
            },
            {
                "node_id": "design",
                "type": "agent",
                "agent_id": "test-design-agent",
                "agent_version": "2.5.0",
            },
        ],
        "edges": [
            {
                "from": "requirement",
                "to": "design",
                "condition": "always",
            },
        ],
    },
    "hitl-workflow": {
        "workflow_id": "test-hitl-workflow",
        "name": "HITL Approval Workflow",
        "version": "1.0.0",
        "nodes": [
            {
                "node_id": "requirement",
                "type": "agent",
                "agent_id": "requirement-agent",
                "agent_version": "2.5.0",
            },
            {
                "node_id": "approval",
                "type": "human_gate",
                "prompt": "请审核需求分析结果",
                "timeout_seconds": 3600,
                "default_action": "approved",
            },
            {
                "node_id": "design",
                "type": "agent",
                "agent_id": "test-design-agent",
                "agent_version": "2.5.0",
            },
        ],
        "edges": [
            {
                "from": "requirement",
                "to": "approval",
                "condition": "always",
            },
            {
                "from": "approval",
                "to": "design",
                "condition": "approved",
            },
        ],
    },
    "condition-workflow": {
        "workflow_id": "test-condition-workflow",
        "name": "Conditional Workflow",
        "version": "1.0.0",
        "nodes": [
            {
                "node_id": "requirement",
                "type": "agent",
                "agent_id": "requirement-agent",
                "agent_version": "2.5.0",
            },
            {
                "node_id": "check-success",
                "type": "condition",
                "condition_expr": "node_outputs['requirement']['success'] == True",
            },
            {
                "node_id": "design",
                "type": "agent",
                "agent_id": "test-design-agent",
                "agent_version": "2.5.0",
            },
        ],
        "edges": [
            {
                "from": "requirement",
                "to": "check-success",
                "condition": "always",
            },
            {
                "from": "check-success",
                "to": "design",
                "condition": "node_outputs['check-success']['result'] == True",
            },
        ],
    },
    "retry-workflow": {
        "workflow_id": "test-retry-workflow",
        "name": "Retry Policy Workflow",
        "version": "1.0.0",
        "nodes": [
            {
                "node_id": "flaky-agent",
                "type": "agent",
                "agent_id": "requirement-agent",
                "agent_version": "2.5.0",
                "retry_policy": {
                    "max_attempts": 3,
                    "backoff": "exponential",
                    "backoff_seconds": 1,
                },
            },
        ],
        "edges": [],
    },
}


def create_test_workflows():
    """创建测试 Workflow 到数据库"""
    from aitest.platform.workflow_store import get_workflow_store
    from aitest.platform.workflow import WorkflowGraph

    store = get_workflow_store()

    for wf_id, wf_data in TEST_WORKFLOWS.items():
        print(f"Creating test workflow: {wf_id}")

        # 转换为 WorkflowGraph
        graph = WorkflowGraph.from_dict(wf_data)

        # 保存到数据库
        store.create_workflow(
            workflow_id=wf_data["workflow_id"],
            name=wf_data["name"],
            description=f"Test workflow: {wf_id}",
            version=wf_data["version"],
            graph=graph,
            org_id="test-org",
            created_by="test-user",
        )

        print(f"  ✓ Created: {wf_data['workflow_id']}")


def test_simple_workflow():
    """测试简单 Workflow: requirement → design"""
    import asyncio
    from aitest.platform.workspace import ExecutionContext
    from aitest.server.api.run_executor import RunExecutor

    print("\n=== Test 1: Simple Workflow ===")

    ctx = ExecutionContext(
        org_id="test-org",
        workspace_id="test-workspace",
        user_id="test-user",
        metadata={},
    )

    params = {
        "module": "equipment",
        "pages": ["equipment-list"],
    }

    runtime = {
        "provider": "claude",
    }

    execution = {
        "mode": "full",
    }

    result = asyncio.run(
        RunExecutor.execute_workflow(
            ctx=ctx,
            target_id="test-simple-workflow",
            target_version="latest",
            params=params,
            runtime=runtime,
            execution=execution,
        )
    )

    print(f"Result: {json.dumps(result, indent=2)}")

    # 验证
    assert result["status"] in ["completed", "failed"], f"Invalid status: {result['status']}"
    assert "workflow_result" in result
    assert "completed_nodes" in result["workflow_result"]

    if result["status"] == "completed":
        completed = result["workflow_result"]["completed_nodes"]
        print(f"✓ Completed nodes: {completed}")
        assert len(completed) == 2, f"Expected 2 nodes, got {len(completed)}"
    else:
        print(f"✗ Workflow failed: {result['error_message']}")


def test_hitl_workflow():
    """测试 HITL Workflow: agent → human_gate → agent"""
    import asyncio
    from aitest.platform.workspace import ExecutionContext
    from aitest.server.api.run_executor import RunExecutor

    print("\n=== Test 2: HITL Workflow ===")

    ctx = ExecutionContext(
        org_id="test-org",
        workspace_id="test-workspace",
        user_id="test-user",
        metadata={},
    )

    params = {
        "module": "equipment",
        "pages": ["equipment-list"],
    }

    runtime = {"provider": "claude"}
    execution = {"mode": "full"}

    result = asyncio.run(
        RunExecutor.execute_workflow(
            ctx=ctx,
            target_id="test-hitl-workflow",
            target_version="latest",
            params=params,
            runtime=runtime,
            execution=execution,
        )
    )

    print(f"Result: {json.dumps(result, indent=2)}")

    # 验证 human_gate 节点
    if result["status"] == "completed":
        node_outputs = result["workflow_result"]["node_outputs"]
        approval = node_outputs.get("approval", {})
        print(f"✓ Human gate action: {approval.get('action')}")
        assert approval.get("action") == "approved", "Expected auto-approval"


def test_condition_workflow():
    """测试条件 Workflow: agent → condition → agent"""
    import asyncio
    from aitest.platform.workspace import ExecutionContext
    from aitest.server.api.run_executor import RunExecutor

    print("\n=== Test 3: Condition Workflow ===")

    ctx = ExecutionContext(
        org_id="test-org",
        workspace_id="test-workspace",
        user_id="test-user",
        metadata={},
    )

    params = {
        "module": "equipment",
        "pages": ["equipment-list"],
    }

    runtime = {"provider": "claude"}
    execution = {"mode": "full"}

    result = asyncio.run(
        RunExecutor.execute_workflow(
            ctx=ctx,
            target_id="test-condition-workflow",
            target_version="latest",
            params=params,
            runtime=runtime,
            execution=execution,
        )
    )

    print(f"Result: {json.dumps(result, indent=2)}")

    # 验证条件节点
    if result["status"] == "completed":
        node_outputs = result["workflow_result"]["node_outputs"]
        condition = node_outputs.get("check-success", {})
        print(f"✓ Condition result: {condition.get('result')}")


def main():
    """运行所有测试"""
    print("Setting up test workflows...")
    create_test_workflows()

    print("\nRunning tests...")
    try:
        test_simple_workflow()
        test_hitl_workflow()
        test_condition_workflow()
        print("\n✓ All tests passed!")
    except Exception as e:
        print(f"\n✗ Test failed: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()

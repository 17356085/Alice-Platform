"""Tests for RunExecutor — execute_skill() and execute_evaluation()

测试 POST /api/v1/runs 的 target_type=skill 和 target_type=evaluation
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from aitest.server.api.run_executor import RunExecutor
from aitest.platform.workspace import ExecutionContext


@pytest.fixture
def mock_ctx():
    """模拟 ExecutionContext"""
    return ExecutionContext(
        workspace_id="ws_test",
        org_id="org_test",
        user_id="user_alice",
        metadata={},
    )


@pytest.fixture
def mock_run_store():
    """模拟 RunStore"""
    with patch("aitest.server.api.run_executor.get_run_store") as mock:
        store = Mock()
        store.create_run = Mock()
        store.update_run_status = Mock()
        mock.return_value = store
        yield store


@pytest.fixture
def mock_quality_store():
    """模拟 QualityStore"""
    with patch("aitest.server.api.run_executor.get_quality_store") as mock:
        store = Mock()
        store.create_evaluation = Mock()
        store.get_dataset = Mock()
        store.update_evaluation_status = Mock()
        mock.return_value = store
        yield store


# ══════════════════════════════════════════════════════════════════════════
#  execute_skill() 测试
# ══════════════════════════════════════════════════════════════════════════


@pytest.mark.asyncio
async def test_execute_skill_success(mock_ctx, mock_run_store):
    """测试 execute_skill() 成功执行"""

    # Mock run_skill() 返回成功响应
    mock_response = Mock()
    mock_response.content = "这是页面分析结果：\n\n## 元素清单\n- 按钮: #submit\n- 输入框: #username"
    mock_response.token_usage = {
        "input": 1500,
        "output": 800,
        "total": 2300,
    }

    with patch("aitest.server.api.run_executor.run_skill", return_value=mock_response):
        result = await RunExecutor.execute_skill(
            ctx=mock_ctx,
            target_id="automation/page-observe",
            target_version="1.2.0",
            params={
                "prompt": "分析 alarm-config 页面",
                "context": {"module": "equipment", "page": "alarm-config"},
            },
            runtime={"provider": "claude"},
            execution={"mode": "full"},
        )

    # 验证结果
    assert result["status"] == "completed"
    assert result["error_message"] == ""
    assert result["metrics"]["tokens_used"] == 2300
    assert result["metrics"]["input_tokens"] == 1500
    assert result["metrics"]["output_tokens"] == 800
    assert result["metrics"]["duration_ms"] > 0
    assert "output_preview" in result
    assert "元素清单" in result["output_preview"]

    # 验证 Run 状态更新
    mock_run_store.create_run.assert_called_once()
    mock_run_store.update_run_status.assert_called_once()
    assert mock_run_store.update_run_status.call_args[0][1] == "completed"


@pytest.mark.asyncio
async def test_execute_skill_with_provider_id(mock_ctx, mock_run_store):
    """测试 execute_skill() 支持 provider_id（从 ModelProviderStore 加载）"""

    mock_response = Mock()
    mock_response.content = "Test output"
    mock_response.token_usage = {"input": 100, "output": 50, "total": 150}

    with patch("aitest.server.api.run_executor.run_skill", return_value=mock_response):
        result = await RunExecutor.execute_skill(
            ctx=mock_ctx,
            target_id="test-skill",
            target_version="latest",
            params={"prompt": "Test"},
            runtime={"provider": "claude", "provider_id": "anthropic-prod"},
            execution={},
        )

    assert result["status"] == "completed"


@pytest.mark.asyncio
async def test_execute_skill_failure(mock_ctx, mock_run_store):
    """测试 execute_skill() 执行失败"""

    # Mock run_skill() 抛出异常
    with patch("aitest.server.api.run_executor.run_skill", side_effect=Exception("LLM API timeout")):
        result = await RunExecutor.execute_skill(
            ctx=mock_ctx,
            target_id="automation/page-observe",
            target_version="latest",
            params={"prompt": "Test"},
            runtime={"provider": "claude"},
            execution={},
        )

    # 验证结果
    assert result["status"] == "failed"
    assert "LLM API timeout" in result["error_message"]
    assert result["metrics"]["tokens_used"] == 0

    # 验证 Run 状态更新为 failed
    assert mock_run_store.update_run_status.call_args[0][1] == "failed"


@pytest.mark.asyncio
async def test_execute_skill_with_variant(mock_ctx, mock_run_store):
    """测试 execute_skill() 支持 Prompt 变体"""

    mock_response = Mock()
    mock_response.content = "Variant output"
    mock_response.token_usage = {"total": 100}

    with patch("aitest.server.api.run_executor.run_skill", return_value=mock_response) as mock_run_skill:
        result = await RunExecutor.execute_skill(
            ctx=mock_ctx,
            target_id="test-skill",
            target_version="latest",
            params={
                "prompt": "Test",
                "variant": "v2_experimental",
            },
            runtime={"provider": "claude"},
            execution={},
        )

    # 验证 run_skill 被调用时传入了 variant
    mock_run_skill.assert_called_once()
    call_kwargs = mock_run_skill.call_args[1]
    assert call_kwargs.get("variant") == "v2_experimental"
    assert result["status"] == "completed"


# ══════════════════════════════════════════════════════════════════════════
#  execute_evaluation() 测试
# ══════════════════════════════════════════════════════════════════════════


@pytest.mark.asyncio
async def test_execute_evaluation_success(mock_ctx, mock_run_store, mock_quality_store):
    """测试 execute_evaluation() 成功执行"""

    # 1. Mock Dataset
    from aitest.platform.quality import Dataset, Example, Evaluation, EvaluatorConfig

    mock_dataset = Dataset(
        dataset_id="ds_test123",
        name="Test Suite",
        type="test_cases",
        examples=[
            Example(
                input={"prompt": "分析页面 A"},
                expected_output={"min_length": 100},
            ),
            Example(
                input={"prompt": "分析页面 B"},
                expected_output={"contains": ["元素清单"]},
            ),
        ],
    )
    mock_quality_store.get_dataset.return_value = mock_dataset

    # 2. Mock Evaluation 创建
    mock_evaluation = Evaluation(
        evaluation_id="eval_test456",
        name="Eval test",
        dataset_id="ds_test123",
        agent_id="automation/page-observe",
        agent_version="latest",
        status="pending",
    )
    mock_quality_store.create_evaluation.return_value = mock_evaluation

    # 3. Mock EvalRunner
    from aitest.testing.evaluator import EvalRun

    mock_eval_run_1 = EvalRun(
        run_id="eval-0",
        skill_id="automation/page-observe",
        input_text="分析页面 A",
        criteria={"min_length": 100},
        actual_output="这是一个长度超过 100 字符的分析结果..." * 5,
        passed=True,
        score=0.85,
        token_usage={"input": 200, "output": 150},
        latency_ms=1200,
    )

    mock_eval_run_2 = EvalRun(
        run_id="eval-1",
        skill_id="automation/page-observe",
        input_text="分析页面 B",
        criteria={"contains": ["元素清单"]},
        actual_output="## 元素清单\n- 按钮1\n- 输入框2",
        passed=True,
        score=0.92,
        token_usage={"input": 180, "output": 120},
        latency_ms=1000,
    )

    with patch("aitest.server.api.run_executor.EvalRunner") as MockEvalRunner:
        mock_runner = Mock()
        mock_runner.run.side_effect = [mock_eval_run_1, mock_eval_run_2]
        MockEvalRunner.return_value = mock_runner

        result = await RunExecutor.execute_evaluation(
            ctx=mock_ctx,
            target_id="automation/page-observe",
            target_version="latest",
            params={
                "dataset_id": "ds_test123",
                "eval_config": {
                    "judge_model": "claude-3-5-sonnet-20241022",
                    "metrics": ["correctness", "completeness"],
                },
            },
            runtime={"provider": "claude"},
            execution={"mode": "full"},
        )

    # 验证结果
    assert result["status"] == "completed"
    assert result["error_message"] == ""
    assert result["evaluation_id"] == "eval_test456"

    eval_result = result["evaluation_result"]
    assert eval_result["total_examples"] == 2
    assert eval_result["passed_examples"] == 2
    assert eval_result["failed_examples"] == 0
    assert eval_result["pass_rate"] == 1.0
    assert 0.85 <= eval_result["avg_score"] <= 0.92

    # 验证 token 统计
    assert result["metrics"]["input_tokens"] == 380  # 200 + 180
    assert result["metrics"]["output_tokens"] == 270  # 150 + 120
    assert result["metrics"]["tokens_used"] == 650

    # 验证 Evaluation 状态更新
    assert mock_quality_store.update_evaluation_status.call_count == 2  # running + completed
    final_call = mock_quality_store.update_evaluation_status.call_args_list[-1]
    assert final_call[1]["status"] == "completed"
    assert final_call[1]["results"] is not None


@pytest.mark.asyncio
async def test_execute_evaluation_dataset_not_found(mock_ctx, mock_run_store, mock_quality_store):
    """测试 execute_evaluation() Dataset 不存在"""

    from aitest.platform.quality import Evaluation

    mock_evaluation = Evaluation(
        evaluation_id="eval_test",
        name="Test",
        dataset_id="ds_not_found",
        agent_id="test-agent",
        agent_version="latest",
    )
    mock_quality_store.create_evaluation.return_value = mock_evaluation
    mock_quality_store.get_dataset.return_value = None

    result = await RunExecutor.execute_evaluation(
        ctx=mock_ctx,
        target_id="test-agent",
        target_version="latest",
        params={"dataset_id": "ds_not_found"},
        runtime={"provider": "claude"},
        execution={},
    )

    # 验证结果
    assert result["status"] == "failed"
    assert "Dataset not found" in result["error_message"]

    # 验证 Evaluation 状态更新为 failed
    assert mock_quality_store.update_evaluation_status.call_args[1]["status"] == "failed"


@pytest.mark.asyncio
async def test_execute_evaluation_empty_dataset(mock_ctx, mock_run_store, mock_quality_store):
    """测试 execute_evaluation() Dataset 为空"""

    from aitest.platform.quality import Dataset, Evaluation

    mock_dataset = Dataset(
        dataset_id="ds_empty",
        name="Empty Dataset",
        type="test_cases",
        examples=[],  # 空样本集
    )
    mock_quality_store.get_dataset.return_value = mock_dataset

    mock_evaluation = Evaluation(
        evaluation_id="eval_test",
        name="Test",
        dataset_id="ds_empty",
        agent_id="test-agent",
        agent_version="latest",
    )
    mock_quality_store.create_evaluation.return_value = mock_evaluation

    result = await RunExecutor.execute_evaluation(
        ctx=mock_ctx,
        target_id="test-agent",
        target_version="latest",
        params={"dataset_id": "ds_empty"},
        runtime={"provider": "claude"},
        execution={},
    )

    # 验证结果
    assert result["status"] == "failed"
    assert "has no examples" in result["error_message"]


@pytest.mark.asyncio
async def test_execute_evaluation_partial_failure(mock_ctx, mock_run_store, mock_quality_store):
    """测试 execute_evaluation() 部分样本失败"""

    from aitest.platform.quality import Dataset, Example, Evaluation
    from aitest.testing.evaluator import EvalRun

    mock_dataset = Dataset(
        dataset_id="ds_test",
        name="Test",
        type="test_cases",
        examples=[
            Example(input={"prompt": "Test 1"}),
            Example(input={"prompt": "Test 2"}),
            Example(input={"prompt": "Test 3"}),
        ],
    )
    mock_quality_store.get_dataset.return_value = mock_dataset

    mock_evaluation = Evaluation(
        evaluation_id="eval_test",
        name="Test",
        dataset_id="ds_test",
        agent_id="test-agent",
        agent_version="latest",
    )
    mock_quality_store.create_evaluation.return_value = mock_evaluation

    # Mock EvalRunner: 第 2 个样本失败
    def mock_run_side_effect(skill_id, input_text, criteria, context_vars):
        if "Test 2" in input_text:
            raise Exception("API timeout")
        return EvalRun(
            run_id="test",
            skill_id=skill_id,
            input_text=input_text,
            criteria=criteria,
            actual_output="Success",
            passed=True,
            score=0.9,
            token_usage={"input": 100, "output": 50},
        )

    with patch("aitest.server.api.run_executor.EvalRunner") as MockEvalRunner:
        mock_runner = Mock()
        mock_runner.run.side_effect = mock_run_side_effect
        MockEvalRunner.return_value = mock_runner

        result = await RunExecutor.execute_evaluation(
            ctx=mock_ctx,
            target_id="test-agent",
            target_version="latest",
            params={"dataset_id": "ds_test"},
            runtime={"provider": "claude"},
            execution={},
        )

    # 验证结果：虽然有样本失败，但整体 Evaluation 仍然完成
    assert result["status"] == "completed"
    eval_result = result["evaluation_result"]
    assert eval_result["total_examples"] == 3
    assert eval_result["passed_examples"] == 2  # 只有 2 个通过
    assert eval_result["failed_examples"] == 1
    assert eval_result["pass_rate"] == 2/3


@pytest.mark.asyncio
async def test_execute_evaluation_missing_dataset_id(mock_ctx, mock_run_store, mock_quality_store):
    """测试 execute_evaluation() 缺少 dataset_id 参数"""

    with pytest.raises(ValueError, match="dataset_id is required"):
        await RunExecutor.execute_evaluation(
            ctx=mock_ctx,
            target_id="test-agent",
            target_version="latest",
            params={},  # 缺少 dataset_id
            runtime={"provider": "claude"},
            execution={},
        )


# ══════════════════════════════════════════════════════════════════════════
#  Integration tests (需要真实依赖)
# ══════════════════════════════════════════════════════════════════════════


@pytest.mark.integration
@pytest.mark.asyncio
async def test_execute_skill_real_integration(mock_ctx):
    """集成测试：真实执行 Skill（需要 LLM Provider）"""
    # 注意：此测试需要真实的 LLM Provider（可能产生费用）
    # 可以通过环境变量 SKIP_INTEGRATION_TESTS=1 跳过

    import os
    if os.getenv("SKIP_INTEGRATION_TESTS") == "1":
        pytest.skip("Skipping integration test")

    result = await RunExecutor.execute_skill(
        ctx=mock_ctx,
        target_id="automation/page-observe",
        target_version="latest",
        params={
            "prompt": "这是一个简单的测试输入",
        },
        runtime={"provider": "mock"},  # 使用 mock provider 避免费用
        execution={},
    )

    assert result["status"] in ("completed", "failed")
    assert "run_id" in result


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])

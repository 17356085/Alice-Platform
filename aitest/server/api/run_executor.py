"""Run execution handlers for different target types (P7-2 Phase 4)"""

from typing import Any, Dict, Optional
import uuid
from datetime import datetime, timezone

from aitest.platform.workspace import ExecutionContext
from aitest.platform.plugin import get_plugin_manager
from aitest.platform.quality_store import get_quality_store
from aitest.platform.run_store import get_run_store
from aitest.testing.evaluator import EvalRunner
from alice_engine.core.skill_executor import run_skill


class RunExecutor:
    """统一执行器 — 根据 target.type 分发到不同执行逻辑"""

    @staticmethod
    async def execute_agent(
        ctx: ExecutionContext,
        target_id: str,
        target_version: str,
        params: Dict[str, Any],
        runtime: Dict[str, Any],
        execution: Dict[str, Any],
    ) -> Dict[str, Any]:
        """执行 Agent（Phase 1 已实现，保持不变）"""
        from aitest.server.api.execution import get_execution_service_static

        svc = get_execution_service_static()
        result = svc.execute(
            ctx=ctx,
            module=params.get("module", ""),
            pages=params.get("pages", []),
            agent=target_id,
            mode=execution.get("mode", "full"),
            provider=runtime.get("provider", "claude"),
            priority=execution.get("priority", 5),
            idempotency_key=ctx.metadata.get("idempotency_key", ""),
            max_retries=execution.get("max_retries", 3),
        )

        return {
            "run_id": result.run_id,
            "status": result.status,
            "error_message": result.error_message,
            "artifacts": [],
            "metrics": {
                "duration_ms": 0,
                "tokens_used": 0,
                "cost_usd": 0.0,
            },
        }

    @staticmethod
    async def execute_workflow(
        ctx: ExecutionContext,
        target_id: str,
        target_version: str,
        params: Dict[str, Any],
        runtime: Dict[str, Any],
        execution: Dict[str, Any],
    ) -> Dict[str, Any]:
        """执行 Workflow（P8-1 完整实现）"""
        import time
        from aitest.platform.workflow_store import get_workflow_store
        from aitest.platform.workflow_executor import WorkflowExecutor, WorkflowRuntime

        start_time = time.time()

        # 1. 加载 Workflow 定义
        store = get_workflow_store()
        if target_version == "latest":
            workflow_obj = store.get_workflow(target_id)
        else:
            # TODO: 支持版本查询
            workflow_obj = store.get_workflow(target_id)

        if not workflow_obj:
            raise ValueError(f"Workflow not found: {target_id}")

        if not workflow_obj.graph:
            raise ValueError(f"Workflow {target_id} has no graph")

        # 2. 创建 Run 记录
        run_id = f"run_{uuid.uuid4().hex[:16]}"
        run_store = get_run_store()

        run_store.create_run(
            run_id=run_id,
            workspace_id=ctx.workspace_id,
            org_id=ctx.org_id,
            triggered_by=ctx.user_id,
            agent=target_id,  # workflow_id
            module="workflow",
            pages=[],
            mode=execution.get("mode", "full"),
            provider=runtime.get("provider", "claude"),
            metadata={
                "target_type": "workflow",
                "target_id": target_id,
                "target_version": target_version,
                "input": params.get("input", {}),
            },
        )

        # 3. 执行 Workflow（使用 WorkflowExecutor）
        try:
            # 创建运行时
            wf_runtime = WorkflowRuntime(
                run_id=run_id,
                workflow_id=target_id,
                ctx=ctx,
                params=params,
                runtime_config=runtime,
            )

            # 执行
            executor = WorkflowExecutor(workflow_obj.graph, wf_runtime)
            result = executor.execute()

            # 更新 Run 状态
            if result["success"]:
                run_store.update_run_status(run_id, "completed")
            else:
                run_store.update_run_status(
                    run_id,
                    "failed",
                    error_message=result.get("error", "Unknown error"),
                )

            duration_ms = max(1, int((time.time() - start_time) * 1000))

            return {
                "run_id": run_id,
                "status": "completed" if result["success"] else "failed",
                "error_message": result.get("error"),
                "artifacts": [],
                "metrics": {
                    "duration_ms": duration_ms,
                    "tokens_used": 0,  # TODO: 聚合所有 Agent 节点的 token 使用
                    "cost_usd": 0.0,
                },
                "workflow_result": {
                    "completed_nodes": result.get("completed_nodes", []),
                    "node_outputs": result.get("node_outputs", {}),
                },
            }

        except Exception as e:
            # 执行失败
            run_store.update_run_status(run_id, "failed", error_message=str(e))

            return {
                "run_id": run_id,
                "status": "failed",
                "error_message": str(e),
                "artifacts": [],
                "metrics": {
                    "duration_ms": int((time.time() - start_time) * 1000),
                    "tokens_used": 0,
                    "cost_usd": 0.0,
                },
            }

    @staticmethod
    async def execute_skill(
        ctx: ExecutionContext,
        target_id: str,
        target_version: str,
        params: Dict[str, Any],
        runtime: Dict[str, Any],
        execution: Dict[str, Any],
    ) -> Dict[str, Any]:
        """执行单个 Skill（完整实现）"""
        import time

        start_time = time.time()

        # 1. 创建 Run 记录
        run_id = f"run_{uuid.uuid4().hex[:16]}"
        run_store = get_run_store()

        run_store.create_run(
            run_id=run_id,
            workspace_id=ctx.workspace_id,
            org_id=ctx.org_id,
            triggered_by=ctx.user_id,
            agent=target_id,  # skill_id
            module="skill",
            pages=[],
            mode=execution.get("mode", "full"),
            provider=runtime.get("provider", "claude"),
            metadata={
                "target_type": "skill",
                "target_id": target_id,
                "target_version": target_version,
                "prompt": params.get("prompt", ""),
                "context": params.get("context", {}),
            },
        )

        # 2. 执行 Skill（复用 SDK 层）
        try:

            # 获取 Provider
            provider_name = runtime.get("provider", "claude")
            provider_id = runtime.get("provider_id")  # 可选：从 ModelProviderStore 加载

            # P6-3: 准备 Plugin Skill 查找函数
            pm = get_plugin_manager()
            pm.load_all()

            def plugin_skill_lookup(skill_id: str):
                """从 PluginManager 查找 Plugin Skill 路径."""
                return pm.get_skill(skill_id)

            # 执行 Skill
            response = run_skill(
                skill_id=target_id,
                user_input=params.get("prompt", ""),
                provider=provider_name,
                context_vars=params.get("context", {}),
                variant=params.get("variant"),  # 可选：Prompt 变体
                plugin_lookup_fn=plugin_skill_lookup,  # P6-3: 注入 Plugin Skill 查找
            )

            # 3. 提取结果
            actual_output = response.content or ""
            token_usage = response.token_usage or {}

            # 提取 token 数据
            input_tokens = token_usage.get("input", 0)
            output_tokens = token_usage.get("output", 0)
            total_tokens = token_usage.get("total", input_tokens + output_tokens)

            # 4. 提取 artifacts（如果 Skill 输出包含代码块/YAML）
            artifacts = []
            # TODO: 如果需要保存 Skill 输出到文件系统，在此提取
            # from alice_engine.core.output_persistence import extract_code_block, extract_yaml_block
            # code_blocks = extract_code_block(actual_output)
            # yaml_blocks = extract_yaml_block(actual_output)

            # 5. 更新 Run 状态
            duration_ms = max(1, int((time.time() - start_time) * 1000))

            run_store.update_run_status(run_id, "completed")

            # 如果 RunStore 支持 update_run_summary，更新汇总信息
            # run_store.update_run_summary(
            #     run_id=run_id,
            #     total_tokens=total_tokens,
            #     artifacts=artifacts,
            # )

            return {
                "run_id": run_id,
                "status": "completed",
                "error_message": "",
                "artifacts": artifacts,
                "metrics": {
                    "duration_ms": duration_ms,
                    "tokens_used": total_tokens,
                    "input_tokens": input_tokens,
                    "output_tokens": output_tokens,
                    "cost_usd": 0.0,  # TODO: 计算实际成本
                },
                "output_preview": actual_output[:500] if actual_output else "",
            }

        except Exception as e:
            # 执行失败
            duration_ms = int((time.time() - start_time) * 1000)
            error_message = f"Skill execution failed: {str(e)}"

            run_store.update_run_status(run_id, "failed", error_message=error_message)

            return {
                "run_id": run_id,
                "status": "failed",
                "error_message": error_message,
                "artifacts": [],
                "metrics": {
                    "duration_ms": duration_ms,
                    "tokens_used": 0,
                    "cost_usd": 0.0,
                },
            }

    @staticmethod
    async def execute_evaluation(
        ctx: ExecutionContext,
        target_id: str,
        target_version: str,
        params: Dict[str, Any],
        runtime: Dict[str, Any],
        execution: Dict[str, Any],
    ) -> Dict[str, Any]:
        """执行 Evaluation（P5-1）"""

        dataset_id = params.get("dataset_id")
        if not dataset_id:
            raise ValueError("params.dataset_id is required for type='evaluation'")

        # 1. 创建 Evaluation 记录
        quality_store = get_quality_store()
        eval_config = params.get("eval_config", {})

        from aitest.platform.quality import EvaluatorConfig

        evaluator_config = EvaluatorConfig(
            judge_model=eval_config.get("judge_model", "claude-3-5-sonnet-20241022"),
            metrics=eval_config.get("metrics", ["correctness"]),
            custom_rubric=eval_config.get("custom_rubric"),
        )

        evaluation = quality_store.create_evaluation(
            name=f"Eval {target_id} on {dataset_id}",
            dataset_id=dataset_id,
            agent_id=target_id,
            agent_version=target_version,
            org_id=ctx.org_id,
            created_by=ctx.user_id,
            evaluator_config=evaluator_config,
        )

        # 2. 创建 Run 记录
        run_id = f"run_{uuid.uuid4().hex[:16]}"
        run_store = get_run_store()

        run_store.create_run(
            run_id=run_id,
            workspace_id=ctx.workspace_id,
            org_id=ctx.org_id,
            triggered_by=ctx.user_id,
            agent=target_id,
            module="evaluation",
            pages=[],
            mode=execution.get("mode", "full"),
            provider=runtime.get("provider", "claude"),
            metadata={
                "target_type": "evaluation",
                "target_id": target_id,
                "target_version": target_version,
                "evaluation_id": evaluation.evaluation_id,
                "dataset_id": dataset_id,
            },
        )

        # 3. 执行 Evaluation（遍历 Dataset + 聚合结果）
        try:
            import time

            start_time = time.time()

            # 3.1 加载 Dataset
            dataset = quality_store.get_dataset(dataset_id)
            if not dataset:
                raise ValueError(f"Dataset not found: {dataset_id}")

            if not dataset.examples:
                raise ValueError(f"Dataset '{dataset_id}' has no examples")

            # 3.2 更新 Evaluation 状态为 running
            quality_store.update_evaluation_status(
                evaluation.evaluation_id,
                status="running",
            )
            run_store.update_run_status(run_id, "running")

            # 3.3 遍历样本执行 Skill/Agent
            runner = EvalRunner(provider=runtime.get("provider", "claude"))
            eval_results = []

            for idx, example in enumerate(dataset.examples):
                # 提取输入
                user_input = example.input.get("prompt", "") or str(example.input)

                # 提取评分标准（如果有 expected_output）
                criteria = {}
                if example.expected_output:
                    criteria = example.expected_output

                # 执行 Skill（注意：target_id 可能是 skill_id 或 agent_id）
                # 假设 target_id 是 skill_id，如果是 agent_id，需要改用 run_agent()
                try:
                    eval_run = runner.run(
                        skill_id=target_id,
                        input_text=user_input,
                        criteria=criteria,
                        context_vars=example.input,
                    )
                    eval_results.append(eval_run)
                except Exception as e:
                    # 单个样本失败不中断整个评估
                    from aitest.testing.evaluator import EvalRun
                    eval_run = EvalRun(
                        run_id=f"eval-{idx}",
                        skill_id=target_id,
                        input_text=user_input,
                        criteria=criteria,
                        actual_output="",
                        passed=False,
                        score=0.0,
                        errors=[f"Execution error: {str(e)}"],
                    )
                    eval_results.append(eval_run)

            # 3.4 聚合结果
            from aitest.platform.quality import EvaluationResult

            total_examples = len(eval_results)
            passed_examples = sum(1 for r in eval_results if r.passed)
            failed_examples = total_examples - passed_examples

            avg_score = sum(r.score for r in eval_results) / total_examples if total_examples > 0 else 0.0

            # 聚合 metrics
            total_tokens_input = sum(r.token_usage.get("input", 0) for r in eval_results)
            total_tokens_output = sum(r.token_usage.get("output", 0) for r in eval_results)
            total_tokens = total_tokens_input + total_tokens_output

            eval_result = EvaluationResult(
                pass_rate=passed_examples / total_examples if total_examples > 0 else 0.0,
                total_examples=total_examples,
                passed_examples=passed_examples,
                failed_examples=failed_examples,
                metrics={
                    "avg_score": round(avg_score, 3),
                    "total_tokens": total_tokens,
                },
                details=[
                    {
                        "example_index": idx,
                        "input_preview": r.input_text[:100],
                        "passed": r.passed,
                        "score": r.score,
                        "errors": r.errors,
                    }
                    for idx, r in enumerate(eval_results)
                ],
            )

            # 3.5 更新 Evaluation 状态
            quality_store.update_evaluation_status(
                evaluation.evaluation_id,
                status="completed",
                results=eval_result,
            )

            # 3.6 更新 Run 状态
            duration_ms = int((time.time() - start_time) * 1000)
            run_store.update_run_status(run_id, "completed")

            return {
                "run_id": run_id,
                "status": "completed",
                "error_message": "",
                "artifacts": [],
                "metrics": {
                    "duration_ms": duration_ms,
                    "tokens_used": total_tokens,
                    "input_tokens": total_tokens_input,
                    "output_tokens": total_tokens_output,
                    "cost_usd": 0.0,  # TODO: 计算实际成本
                },
                "evaluation_id": evaluation.evaluation_id,
                "evaluation_result": {
                    "pass_rate": eval_result.pass_rate,
                    "total_examples": eval_result.total_examples,
                    "passed_examples": eval_result.passed_examples,
                    "failed_examples": eval_result.failed_examples,
                    "avg_score": eval_result.metrics.get("avg_score", 0.0),
                },
            }

        except Exception as e:
            # 执行失败
            duration_ms = int((time.time() - start_time) * 1000)
            error_message = f"Evaluation execution failed: {str(e)}"

            quality_store.update_evaluation_status(
                evaluation.evaluation_id,
                status="failed",
                error_message=error_message,
            )
            run_store.update_run_status(run_id, "failed", error_message=error_message)

            return {
                "run_id": run_id,
                "status": "failed",
                "error_message": error_message,
                "artifacts": [],
                "metrics": {
                    "duration_ms": duration_ms,
                    "tokens_used": 0,
                    "cost_usd": 0.0,
                },
                "evaluation_id": evaluation.evaluation_id,
            }

"""Run execution handlers for different target types (P7-2 Phase 4)"""

from typing import Any, Dict, Optional
import uuid
from datetime import datetime, timezone

from aitest.platform.workspace import ExecutionContext


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
        from aitest.platform.run_store import get_run_store
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

            duration_ms = int((time.time() - start_time) * 1000)

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
        """执行单个 Skill（占位实现）"""
        from aitest.platform.run_store import get_run_store

        # 创建 Run 记录
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

        # TODO: 实现 Skill 独立执行逻辑
        run_store.update_run_status(run_id, "pending", error_message="Skill execution not implemented yet")

        return {
            "run_id": run_id,
            "status": "pending",
            "error_message": "Skill execution not implemented yet",
            "artifacts": [],
            "metrics": {
                "duration_ms": 0,
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
        from aitest.platform.quality_store import get_quality_store
        from aitest.platform.run_store import get_run_store

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

        # 3. 启动 Evaluation 执行（TODO: 异步执行）
        run_store.update_run_status(
            run_id,
            "pending",
            error_message="Evaluation execution engine not implemented yet (P5-1 follow-up)",
        )

        return {
            "run_id": run_id,
            "status": "pending",
            "error_message": "Evaluation execution engine not implemented yet",
            "artifacts": [],
            "metrics": {
                "duration_ms": 0,
                "tokens_used": 0,
                "cost_usd": 0.0,
            },
            "evaluation_id": evaluation.evaluation_id,
        }

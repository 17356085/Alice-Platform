"""Workflow Execution Engine — 从 JSON 构建 LangGraph 并执行 (P8-1)

架构设计:
1. WorkflowExecutor: 主执行器，从 WorkflowGraph JSON 构建 LangGraph
2. NodeExecutor: 节点执行器工厂，根据 node.type 分发到不同执行逻辑
3. WorkflowRuntime: 运行时状态管理，节点间数据传递
4. RetryHandler: 处理节点重试逻辑（exponential backoff）

节点类型:
- agent: 复用现有 AgentLoop（通过 ExecutionService）
- human_gate: WebSocket 推送到 Studio，等待人工审核（基础版）
- condition: 条件分支（简单表达式求值）
- parallel: 并行执行（Send() API）

状态传递:
- WorkflowState: 包含 node_outputs (Dict[node_id, Any]), current_node, error
- 每个节点输出保存在 node_outputs[node_id]
- 下游节点可通过 state["node_outputs"][upstream_node_id] 访问上游结果
"""

import logging
import operator
import time
import uuid
from dataclasses import dataclass, field
from typing import Annotated, Any, Dict, List, Optional, TypedDict
from datetime import datetime, timezone

from langgraph.graph import StateGraph, END
from langgraph.types import Send

from aitest.platform.workflow import WorkflowGraph, WorkflowNode, WorkflowEdge, RetryPolicy
from aitest.platform.workspace import ExecutionContext

logger = logging.getLogger(__name__)


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# Workflow State
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━


class WorkflowState(TypedDict, total=False):
    """Workflow 运行时状态"""
    run_id: str
    workflow_id: str
    node_outputs: Dict[str, Any]  # {node_id: output}
    current_node: str
    completed_nodes: List[str]
    error: Optional[str]
    metadata: Dict[str, Any]
    parallel_results: Annotated[List[Dict], operator.add]  # P8-方案2: 并行结果累积器
    current_sub_node: str  # P8-方案2: 当前处理的子节点 ID


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# Runtime State Manager
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━


@dataclass
class WorkflowRuntime:
    """Workflow 运行时状态管理"""
    run_id: str
    workflow_id: str
    ctx: ExecutionContext
    params: Dict[str, Any]
    runtime_config: Dict[str, Any]
    node_outputs: Dict[str, Any] = field(default_factory=dict)
    completed_nodes: List[str] = field(default_factory=list)

    def get_node_output(self, node_id: str) -> Optional[Any]:
        """获取节点输出"""
        return self.node_outputs.get(node_id)

    def set_node_output(self, node_id: str, output: Any):
        """设置节点输出"""
        self.node_outputs[node_id] = output
        if node_id not in self.completed_nodes:
            self.completed_nodes.append(node_id)

    def to_state(self) -> WorkflowState:
        """转换为 WorkflowState"""
        return {
            "run_id": self.run_id,
            "workflow_id": self.workflow_id,
            "node_outputs": self.node_outputs.copy(),
            "current_node": "",
            "completed_nodes": self.completed_nodes.copy(),
            "error": None,
            "metadata": {},
        }


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# Retry Handler
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━


class RetryHandler:
    """节点重试处理器"""

    @staticmethod
    def calculate_backoff(attempt: int, policy: RetryPolicy) -> float:
        """计算退避时间（秒）"""
        if policy.backoff == "exponential":
            return policy.backoff_seconds * (2 ** (attempt - 1))
        elif policy.backoff == "linear":
            return policy.backoff_seconds * attempt
        else:
            return 0.0

    @staticmethod
    def should_retry(attempt: int, policy: RetryPolicy, error: Exception) -> bool:
        """判断是否应该重试"""
        if attempt >= policy.max_attempts:
            return False

        # TODO: 根据 error 类型判断是否可重试
        # 例如: API rate limit → 可重试，validation error → 不可重试
        return True


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# Node Executors
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━


class NodeExecutor:
    """节点执行器（P8-方案1: 重构为实例方法）"""

    def __init__(self, executor: 'WorkflowExecutor'):
        """初始化节点执行器。

        Args:
            executor: WorkflowExecutor 实例，用于访问 workflow.nodes 和递归执行节点
        """
        self.executor = executor

    def execute_agent_node(
        self,
        node: WorkflowNode,
        runtime: WorkflowRuntime,
        state: WorkflowState,
    ) -> Dict[str, Any]:
        """执行 agent 节点（复用现有 ExecutionService）"""
        from aitest.server.api.execution import get_execution_service_static

        logger.info(f"[WorkflowExecutor] Executing agent node: {node.node_id} (agent={node.agent_id})")

        # 从 params 提取 module/pages
        module = runtime.params.get("module", "")
        pages = runtime.params.get("pages", [])

        # 重试逻辑
        policy = node.retry_policy or RetryPolicy()
        attempt = 0
        last_error = None

        while attempt < policy.max_attempts:
            attempt += 1
            try:
                svc = get_execution_service_static()
                result = svc.execute(
                    ctx=runtime.ctx,
                    module=module,
                    pages=pages,
                    agent=node.agent_id,
                    mode=runtime.runtime_config.get("mode", "full"),
                    provider=runtime.runtime_config.get("provider", "claude"),
                    priority=5,
                    idempotency_key=f"{runtime.run_id}_{node.node_id}_{attempt}",
                    max_retries=1,  # 内层不重试，外层统一处理
                )

                return {
                    "success": result.status == "completed",
                    "run_id": result.run_id,
                    "status": result.status,
                    "error_message": result.error_message,
                }

            except Exception as e:
                last_error = e
                logger.warning(f"[WorkflowExecutor] Agent node {node.node_id} attempt {attempt} failed: {e}")

                if attempt < policy.max_attempts:
                    backoff = RetryHandler.calculate_backoff(attempt, policy)
                    logger.info(f"[WorkflowExecutor] Retrying in {backoff}s...")
                    time.sleep(backoff)

        # 所有重试失败
        logger.error(f"[WorkflowExecutor] Agent node {node.node_id} failed after {policy.max_attempts} attempts")
        return {
            "success": False,
            "error_message": f"Failed after {policy.max_attempts} attempts: {last_error}",
        }

    def execute_human_gate_node(
        self,
        node: WorkflowNode,
        runtime: WorkflowRuntime,
        state: WorkflowState,
    ) -> Dict[str, Any]:
        """Persist a gate and block this workflow thread until it is resolved."""
        logger.info(f"[WorkflowExecutor] Human gate node: {node.node_id} (prompt={node.prompt})")
        from aitest.platform.human_gates import create_gate, wait_for_gate
        gate = create_gate(runtime.run_id, node.node_id, node.prompt or "Approval required", state.get("node_outputs", {}), ["approve", "reject", "request_changes"])
        return wait_for_gate(gate["id"], node.timeout_seconds, node.default_action)

    def execute_condition_node(
        self,
        node: WorkflowNode,
        runtime: WorkflowRuntime,
        state: WorkflowState,
    ) -> Dict[str, Any]:
        """执行 condition 节点（简单表达式求值）"""
        logger.info(f"[WorkflowExecutor] Condition node: {node.node_id} (expr={node.condition_expr})")

        if not node.condition_expr:
            logger.warning(f"[WorkflowExecutor] Condition node {node.node_id} has no expression, defaulting to True")
            return {"success": True, "result": True}

        # 简单实现：支持访问 node_outputs
        # 例如: "node_outputs['requirement_agent']['success'] == True"
        try:
            # 安全的表达式求值（限制 globals/locals）
            allowed_globals = {
                "__builtins__": {},
                "node_outputs": state.get("node_outputs", {}),
            }
            result = eval(node.condition_expr, allowed_globals, {})

            logger.info(f"[WorkflowExecutor] Condition evaluated to: {result}")
            return {"success": True, "result": bool(result)}

        except Exception as e:
            logger.error(f"[WorkflowExecutor] Condition evaluation failed: {e}")
            return {"success": False, "error": str(e), "result": False}

    def execute_parallel_node(
        self,
        node: WorkflowNode,
        runtime: WorkflowRuntime,
        state: WorkflowState,
    ) -> Dict[str, Any]:
        """执行 parallel 节点（方案1完整实现 — 使用线程池并行执行）

        P8-方案1: NodeExecutor 现在是实例方法，可以访问 self.executor.workflow.nodes
        来查找和执行子节点。
        """
        import concurrent.futures
        from concurrent.futures import ThreadPoolExecutor, as_completed

        logger.info(f"[WorkflowExecutor] Parallel node: {node.node_id}")

        # 1. 从 metadata 获取并行节点列表
        parallel_nodes = node.metadata.get("parallel_nodes", [])
        max_concurrency = node.metadata.get("max_concurrency", 3)

        if not parallel_nodes:
            logger.warning(f"[WorkflowExecutor] Parallel node {node.node_id} has no parallel_nodes specified")
            return {"success": False, "error": "No parallel_nodes specified in node.metadata"}

        logger.info(f"[WorkflowExecutor] Executing {len(parallel_nodes)} nodes in parallel (max_concurrency={max_concurrency})")

        # 2. 并行执行所有子节点
        results = {}
        errors = {}

        def execute_sub_node(sub_node_id: str) -> tuple[str, Dict[str, Any]]:
            """执行单个子节点（在线程池中）"""
            try:
                # ✅ P8-方案1: 现在可以访问 workflow.nodes 查找子节点
                sub_node = self.executor.find_node(sub_node_id)
                if not sub_node:
                    return sub_node_id, {
                        "success": False,
                        "error": f"Sub-node '{sub_node_id}' not found in workflow"
                    }

                logger.info(f"[WorkflowExecutor] Executing parallel sub-node: {sub_node_id} (type={sub_node.type})")

                # ✅ P8-方案1: 递归执行子节点（支持任意节点类型）
                result = self.executor.execute_single_node(sub_node, runtime, state)

                return sub_node_id, result

            except Exception as e:
                logger.error(f"[WorkflowExecutor] Parallel sub-node {sub_node_id} failed: {e}")
                return sub_node_id, {"success": False, "error": str(e)}

        # 3. 使用线程池并行执行
        with ThreadPoolExecutor(max_workers=max_concurrency) as executor:
            # 提交所有任务
            future_to_node = {
                executor.submit(execute_sub_node, sub_node_id): sub_node_id
                for sub_node_id in parallel_nodes
            }

            # 收集结果
            for future in as_completed(future_to_node):
                sub_node_id = future_to_node[future]
                try:
                    node_id, result = future.result()
                    results[node_id] = result
                    if not result.get("success", False):
                        errors[node_id] = result.get("error", "Unknown error")
                except Exception as e:
                    logger.error(f"[WorkflowExecutor] Failed to get result for {sub_node_id}: {e}")
                    errors[sub_node_id] = str(e)

        # 4. 聚合结果
        total_nodes = len(parallel_nodes)
        successful_nodes = sum(1 for r in results.values() if r.get("success", False))
        failed_nodes = len(errors)

        overall_success = failed_nodes == 0

        logger.info(
            f"[WorkflowExecutor] Parallel execution completed: "
            f"{successful_nodes}/{total_nodes} succeeded, {failed_nodes} failed"
        )

        return {
            "success": overall_success,
            "total_nodes": total_nodes,
            "successful_nodes": successful_nodes,
            "failed_nodes": failed_nodes,
            "results": results,
            "errors": errors if errors else None,
        }


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# Workflow Executor
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━


class WorkflowExecutor:
    """Workflow 执行引擎 — 从 JSON 构建 LangGraph"""

    def __init__(
        self,
        workflow: WorkflowGraph,
        runtime: WorkflowRuntime,
    ):
        self.workflow = workflow
        self.runtime = runtime
        self.graph: Optional[StateGraph] = None
        self.node_executor = NodeExecutor(self)  # P8-方案1: 创建 NodeExecutor 实例

    def find_node(self, node_id: str) -> Optional[WorkflowNode]:
        """根据 node_id 查找节点（P8-方案1 新增）。

        Args:
            node_id: 节点 ID

        Returns:
            WorkflowNode 或 None
        """
        for node in self.workflow.nodes:
            if node.node_id == node_id:
                return node
        return None

    def execute_single_node(
        self,
        node: WorkflowNode,
        runtime: WorkflowRuntime,
        state: WorkflowState,
    ) -> Dict[str, Any]:
        """执行单个节点（P8-方案1 新增）。

        Args:
            node: 要执行的节点
            runtime: 运行时状态
            state: Workflow 状态

        Returns:
            节点执行结果
        """
        # 根据节点类型分发到对应的执行器
        if node.type == "agent":
            return self.node_executor.execute_agent_node(node, runtime, state)
        elif node.type == "human_gate":
            return self.node_executor.execute_human_gate_node(node, runtime, state)
        elif node.type == "condition":
            return self.node_executor.execute_condition_node(node, runtime, state)
        elif node.type == "parallel":
            return self.node_executor.execute_parallel_node(node, runtime, state)
        else:
            logger.error(f"[WorkflowExecutor] Unknown node type: {node.type}")
            return {"success": False, "error": f"Unknown node type: {node.type}"}

    def build_graph(self) -> StateGraph:
        """从 WorkflowGraph JSON 构建 LangGraph（P8-方案2: 支持 Parallel 节点的 Send() API）"""
        logger.info(f"[WorkflowExecutor] Building graph for workflow: {self.workflow.workflow_id}")

        builder = StateGraph(WorkflowState)

        # P8-方案2: 检测 parallel 节点，构建 fan-out/fan-in 子图
        parallel_nodes = [n for n in self.workflow.nodes if n.type == "parallel"]

        # 添加节点
        for node in self.workflow.nodes:
            if node.type == "parallel":
                # P8-方案2: Parallel 节点需要特殊处理（fan-out + fan-in）
                self._add_parallel_subgraph(builder, node)
            else:
                # 普通节点直接添加
                node_func = self._make_node_func(node)
                builder.add_node(node.node_id, node_func)

        # 添加边
        entry_nodes = self._find_entry_nodes()
        if not entry_nodes:
            raise ValueError("No entry nodes found (nodes with no incoming edges)")

        # 设置入口点（如果有多个入口，选第一个）
        builder.set_entry_point(entry_nodes[0])

        # 添加边（跳过 parallel 节点的出边，由 _add_parallel_subgraph 处理）
        for edge in self.workflow.edges:
            # P8-方案2: 如果 from_node 是 parallel 节点，由子图处理
            from_node_obj = self.find_node(edge.from_node)
            if from_node_obj and from_node_obj.type == "parallel":
                continue  # 跳过，由 _add_parallel_subgraph 处理

            if edge.condition == "always":
                builder.add_edge(edge.from_node, edge.to_node)
            else:
                # 条件边：需要路由函数
                route_func = self._make_route_func(edge)
                builder.add_conditional_edges(
                    edge.from_node,
                    route_func,
                    {edge.to_node: edge.to_node, END: END},
                )

        # 找出没有出边的节点，连接到 END
        # 注意: parallel 节点由 _add_parallel_subgraph 单独处理，不在此连接到 END
        parallel_node_ids = {n.node_id for n in self.workflow.nodes if n.type == "parallel"}
        exit_nodes = self._find_exit_nodes()
        for node_id in exit_nodes:
            if node_id not in parallel_node_ids:
                builder.add_edge(node_id, END)

        self.graph = builder
        return builder

    def _make_node_func(self, node: WorkflowNode):
        """为节点创建执行函数"""
        def node_func(state: WorkflowState) -> Dict[str, Any]:
            logger.info(f"[WorkflowExecutor] Executing node: {node.node_id} (type={node.type})")

            # P8-方案1: 使用 NodeExecutor 实例方法（而非静态方法）
            result = self.execute_single_node(node, self.runtime, state)

            # 保存节点输出
            self.runtime.set_node_output(node.node_id, result)

            # 更新状态
            return {
                "current_node": node.node_id,
                "node_outputs": {node.node_id: result},
                "completed_nodes": [node.node_id],
            }

        return node_func

    def _make_route_func(self, edge: WorkflowEdge):
        """为条件边创建路由函数"""
        def route_func(state: WorkflowState) -> str:
            # 简单实现：检查上游节点输出
            upstream_output = state.get("node_outputs", {}).get(edge.from_node, {})

            if edge.condition == "approved":
                # human_gate 节点的 approved 条件
                if upstream_output.get("action") == "approved":
                    return edge.to_node
                else:
                    return END

            elif edge.condition == "rejected":
                if upstream_output.get("action") == "rejected":
                    return edge.to_node
                else:
                    return END

            else:
                # 自定义表达式
                try:
                    allowed_globals = {
                        "__builtins__": {},
                        "node_outputs": state.get("node_outputs", {}),
                        "upstream": upstream_output,
                    }
                    result = eval(edge.condition, allowed_globals, {})
                    return edge.to_node if result else END
                except Exception as e:
                    logger.error(f"[WorkflowExecutor] Route condition evaluation failed: {e}")
                    return END

        return route_func

    def _find_entry_nodes(self) -> List[str]:
        """找出入口节点（没有入边的节点）"""
        all_nodes = {node.node_id for node in self.workflow.nodes}
        nodes_with_incoming = {edge.to_node for edge in self.workflow.edges}
        return list(all_nodes - nodes_with_incoming)

    def _find_exit_nodes(self) -> List[str]:
        """找出出口节点（没有出边的节点）"""
        all_nodes = {node.node_id for node in self.workflow.nodes}
        nodes_with_outgoing = {edge.from_node for edge in self.workflow.edges}
        return list(all_nodes - nodes_with_outgoing)

    def _add_parallel_subgraph(self, builder: StateGraph, parallel_node: WorkflowNode):
        """为 parallel 节点添加 fan-out/fan-in 子图（P8-方案2）。

        结构:
            parallel_node → fanout (返回 list[Send])
                              ↓
                          sub_node_1
                          sub_node_2  ← 并行执行
                          sub_node_3
                              ↓
                           merge_node → 下游节点
        """
        sub_node_ids = parallel_node.metadata.get("parallel_nodes", [])
        if not sub_node_ids:
            logger.warning(f"[WorkflowExecutor] Parallel node {parallel_node.node_id} has no sub-nodes")
            return

        process_name = f"{parallel_node.node_id}_process"
        merge_name = f"{parallel_node.node_id}_merge"

        # 1. Fan-out 函数：为每个子节点创建一个 Send
        def fanout(state: WorkflowState) -> list[Send]:
            logger.info(f"[WorkflowExecutor] Fanout from {parallel_node.node_id} to {len(sub_node_ids)} sub-nodes")
            sends = []
            for sub_node_id in sub_node_ids:
                # 每个子节点独立状态副本
                sub_state = {**state, "current_sub_node": sub_node_id}
                sends.append(Send(process_name, sub_state))
            return sends

        # 2. 处理单个子节点
        def process_sub_node(state: WorkflowState) -> Dict[str, Any]:
            sub_node_id = state.get("current_sub_node")
            logger.info(f"[WorkflowExecutor] Processing sub-node: {sub_node_id}")

            sub_node = self.find_node(sub_node_id)
            if not sub_node:
                logger.error(f"[WorkflowExecutor] Sub-node {sub_node_id} not found")
                return {
                    "parallel_results": [{
                        "node_id": sub_node_id,
                        "success": False,
                        "error": f"Sub-node '{sub_node_id}' not found in workflow"
                    }]
                }

            # 执行子节点
            try:
                result = self.execute_single_node(sub_node, self.runtime, state)
                self.runtime.set_node_output(sub_node_id, result)

                return {
                    "parallel_results": [{
                        "node_id": sub_node_id,
                        "success": result.get("success", False),
                        "result": result
                    }]
                }
            except Exception as e:
                logger.error(f"[WorkflowExecutor] Sub-node {sub_node_id} execution failed: {e}")
                return {
                    "parallel_results": [{
                        "node_id": sub_node_id,
                        "success": False,
                        "error": str(e)
                    }]
                }

        # 3. Merge 函数：聚合所有子节点结果
        def merge_results(state: WorkflowState) -> Dict[str, Any]:
            results = state.get("parallel_results", [])
            logger.info(f"[WorkflowExecutor] Merging {len(results)} parallel results")

            # 统计成功/失败
            total = len(results)
            successful = sum(1 for r in results if r.get("success", False))
            failed = total - successful

            # 聚合结果
            aggregated = {
                "success": failed == 0,
                "total_nodes": total,
                "successful_nodes": successful,
                "failed_nodes": failed,
                "results": {r["node_id"]: r.get("result", {}) for r in results},
                "errors": {r["node_id"]: r.get("error", "Unknown error") for r in results if not r.get("success", False)} or None,
            }

            # 保存到 node_outputs
            self.runtime.set_node_output(parallel_node.node_id, aggregated)

            return {
                "current_node": parallel_node.node_id,
                "node_outputs": {parallel_node.node_id: aggregated},
                "completed_nodes": [parallel_node.node_id],
            }

        # 4. 构建子图
        builder.add_node(process_name, process_sub_node)
        builder.add_node(merge_name, merge_results)

        # 5. 连接边
        # parallel_node → fanout → process (多个 Send)
        builder.add_conditional_edges(
            parallel_node.node_id,
            fanout,
            [process_name]
        )

        # process → merge (自动聚合)
        builder.add_edge(process_name, merge_name)

        # 6. 处理 merge 节点的出边
        # 找到从 parallel_node 出发的边，重定向到 merge_name
        for edge in self.workflow.edges:
            if edge.from_node == parallel_node.node_id:
                if edge.condition == "always":
                    builder.add_edge(merge_name, edge.to_node)
                else:
                    # 条件边（如果需要）
                    route_func = self._make_route_func(edge)
                    builder.add_conditional_edges(
                        merge_name,
                        route_func,
                        {edge.to_node: edge.to_node, END: END},
                    )

        logger.info(f"[WorkflowExecutor] Added parallel subgraph for {parallel_node.node_id} with {len(sub_node_ids)} sub-nodes")

    def execute(self) -> Dict[str, Any]:
        """执行 Workflow"""
        logger.info(f"[WorkflowExecutor] Starting workflow execution: {self.workflow.workflow_id}")

        # 构建图
        builder = self.build_graph()
        compiled = builder.compile()

        # 初始状态
        initial_state = self.runtime.to_state()

        # 执行
        try:
            final_state = compiled.invoke(initial_state)

            logger.info(f"[WorkflowExecutor] Workflow completed: {len(final_state.get('completed_nodes', []))} nodes")

            return {
                "success": True,
                "state": final_state,
                "completed_nodes": final_state.get("completed_nodes", []),
                "node_outputs": final_state.get("node_outputs", {}),
            }

        except Exception as e:
            logger.error(f"[WorkflowExecutor] Workflow execution failed: {e}")
            import traceback
            traceback.print_exc()

            return {
                "success": False,
                "error": str(e),
                "state": initial_state,
            }

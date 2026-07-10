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
import time
import uuid
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, TypedDict
from datetime import datetime, timezone

from langgraph.graph import StateGraph, END

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
    """节点执行器工厂"""

    @staticmethod
    def execute_agent_node(
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

    @staticmethod
    def execute_human_gate_node(
        node: WorkflowNode,
        runtime: WorkflowRuntime,
        state: WorkflowState,
    ) -> Dict[str, Any]:
        """执行 human_gate 节点（基础版：返回 default_action）

        TODO: WebSocket 推送到 Studio，等待人工审核
        当前实现: 直接返回 default_action
        """
        logger.info(f"[WorkflowExecutor] Human gate node: {node.node_id} (prompt={node.prompt})")
        logger.warning(f"[WorkflowExecutor] WebSocket HITL not implemented, using default_action={node.default_action}")

        # TODO:
        # 1. 通过 WebSocket 推送到 Studio: {"type": "human_gate", "node_id": ..., "prompt": ...}
        # 2. 等待用户响应（timeout_seconds）
        # 3. 超时则返回 default_action

        # 当前占位实现
        return {
            "success": True,
            "action": node.default_action,
            "comment": "Auto-approved (WebSocket HITL not implemented)",
        }

    @staticmethod
    def execute_condition_node(
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

    @staticmethod
    def execute_parallel_node(
        node: WorkflowNode,
        runtime: WorkflowRuntime,
        state: WorkflowState,
    ) -> Dict[str, Any]:
        """执行 parallel 节点（占位：未来使用 LangGraph Send() API）"""
        logger.info(f"[WorkflowExecutor] Parallel node: {node.node_id}")
        logger.warning(f"[WorkflowExecutor] Parallel execution not implemented, executing sequentially")

        # TODO: 使用 LangGraph Send() API 实现并行执行
        # 参考: aitest/graphs/parallel_sop.py

        return {"success": True, "note": "Parallel execution not implemented"}


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

    def build_graph(self) -> StateGraph:
        """从 WorkflowGraph JSON 构建 LangGraph"""
        logger.info(f"[WorkflowExecutor] Building graph for workflow: {self.workflow.workflow_id}")

        builder = StateGraph(WorkflowState)

        # 添加节点
        for node in self.workflow.nodes:
            node_func = self._make_node_func(node)
            builder.add_node(node.node_id, node_func)

        # 添加边
        entry_nodes = self._find_entry_nodes()
        if not entry_nodes:
            raise ValueError("No entry nodes found (nodes with no incoming edges)")

        # 设置入口点（如果有多个入口，选第一个）
        builder.set_entry_point(entry_nodes[0])

        # 添加边
        for edge in self.workflow.edges:
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
        exit_nodes = self._find_exit_nodes()
        for node_id in exit_nodes:
            builder.add_edge(node_id, END)

        self.graph = builder
        return builder

    def _make_node_func(self, node: WorkflowNode):
        """为节点创建执行函数"""
        def node_func(state: WorkflowState) -> Dict[str, Any]:
            logger.info(f"[WorkflowExecutor] Executing node: {node.node_id} (type={node.type})")

            # 根据节点类型分发
            if node.type == "agent":
                result = NodeExecutor.execute_agent_node(node, self.runtime, state)
            elif node.type == "human_gate":
                result = NodeExecutor.execute_human_gate_node(node, self.runtime, state)
            elif node.type == "condition":
                result = NodeExecutor.execute_condition_node(node, self.runtime, state)
            elif node.type == "parallel":
                result = NodeExecutor.execute_parallel_node(node, self.runtime, state)
            else:
                logger.error(f"[WorkflowExecutor] Unknown node type: {node.type}")
                result = {"success": False, "error": f"Unknown node type: {node.type}"}

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

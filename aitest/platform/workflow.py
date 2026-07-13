"""Workflow domain models — JSON schema-based workflow definitions (P8-1)."""

from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any
from datetime import datetime


@dataclass
class RetryPolicy:
    """节点重试策略"""
    max_attempts: int = 1
    backoff: str = "none"  # "none" | "linear" | "exponential"
    backoff_seconds: int = 1


@dataclass
class WorkflowNode:
    """工作流节点

    type 支持:
    - "agent": 执行 Agent
    - "human_gate": 人工审核
    - "condition": 条件分支
    - "parallel": 并行执行
    """
    node_id: str
    type: str  # "agent" | "human_gate" | "condition" | "parallel"

    # agent 节点专用
    agent_id: Optional[str] = None
    agent_version: str = "latest"

    # human_gate 节点专用
    prompt: Optional[str] = None
    timeout_seconds: int = 3600
    default_action: str = "reject"

    # condition 节点专用
    condition_expr: Optional[str] = None  # Python expression

    # 通用配置
    retry_policy: Optional[RetryPolicy] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    position: Optional[Dict[str, float]] = None

    def to_dict(self) -> dict:
        result = {
            "node_id": self.node_id,
            "type": self.type,
            "metadata": self.metadata,
        }
        if self.position is not None:
            result["position"] = self.position
        if self.agent_id:
            result["agent_id"] = self.agent_id
            result["agent_version"] = self.agent_version
        if self.prompt:
            result["prompt"] = self.prompt
            result["timeout_seconds"] = self.timeout_seconds
            result["default_action"] = self.default_action
        if self.condition_expr:
            result["condition_expr"] = self.condition_expr
        if self.retry_policy:
            result["retry_policy"] = {
                "max_attempts": self.retry_policy.max_attempts,
                "backoff": self.retry_policy.backoff,
                "backoff_seconds": self.retry_policy.backoff_seconds,
            }
        return result


@dataclass
class WorkflowEdge:
    """工作流边"""
    from_node: str
    to_node: str
    condition: str = "always"  # "always" | "approved" | "rejected" | custom expression

    def to_dict(self) -> dict:
        return {
            "from": self.from_node,
            "to": self.to_node,
            "condition": self.condition,
        }


@dataclass
class ParallelPolicy:
    """并行执行策略"""
    parallel_nodes: List[str] = field(default_factory=list)
    max_concurrency: int = 3

    def to_dict(self) -> dict:
        return {
            "parallel_nodes": self.parallel_nodes,
            "max_concurrency": self.max_concurrency,
        }


@dataclass
class WorkflowGraph:
    """工作流图定义（JSON schema）"""
    workflow_id: str
    name: str
    version: str
    nodes: List[WorkflowNode] = field(default_factory=list)
    edges: List[WorkflowEdge] = field(default_factory=list)
    parallel_policy: Optional[ParallelPolicy] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict:
        result = {
            "workflow_id": self.workflow_id,
            "name": self.name,
            "version": self.version,
            "nodes": [n.to_dict() for n in self.nodes],
            "edges": [e.to_dict() for e in self.edges],
            "metadata": self.metadata,
        }
        if self.parallel_policy:
            result["parallel_policy"] = self.parallel_policy.to_dict()
        return result

    @classmethod
    def from_dict(cls, data: dict) -> "WorkflowGraph":
        """从字典创建 WorkflowGraph"""
        nodes = []
        for node_data in data.get("nodes", []):
            retry_policy = None
            if "retry_policy" in node_data:
                rp = node_data["retry_policy"]
                retry_policy = RetryPolicy(
                    max_attempts=rp.get("max_attempts", 1),
                    backoff=rp.get("backoff", "none"),
                    backoff_seconds=rp.get("backoff_seconds", 1),
                )

            nodes.append(WorkflowNode(
                node_id=node_data["node_id"],
                type=node_data["type"],
                agent_id=node_data.get("agent_id"),
                agent_version=node_data.get("agent_version", "latest"),
                prompt=node_data.get("prompt"),
                timeout_seconds=node_data.get("timeout_seconds", 3600),
                default_action=node_data.get("default_action", "reject"),
                condition_expr=node_data.get("condition_expr"),
                retry_policy=retry_policy,
                metadata=node_data.get("metadata", {}),
                position=node_data.get("position"),
            ))

        edges = []
        for edge_data in data.get("edges", []):
            edges.append(WorkflowEdge(
                from_node=edge_data.get("from", edge_data.get("from_node")),
                to_node=edge_data.get("to", edge_data.get("to_node")),
                condition=edge_data.get("condition", "always"),
            ))

        parallel_policy = None
        if "parallel_policy" in data:
            pp = data["parallel_policy"]
            parallel_policy = ParallelPolicy(
                parallel_nodes=pp.get("parallel_nodes", []),
                max_concurrency=pp.get("max_concurrency", 3),
            )

        return cls(
            workflow_id=data["workflow_id"],
            name=data["name"],
            version=data["version"],
            nodes=nodes,
            edges=edges,
            parallel_policy=parallel_policy,
            metadata=data.get("metadata", {}),
        )


@dataclass
class Workflow:
    """工作流资源（包含元数据 + 图定义）"""
    workflow_id: str
    name: str
    description: str
    version: str
    status: str  # "draft" | "published" | "archived"
    org_id: str = ""
    created_by: str = ""
    created_at: str = ""
    updated_at: str = ""
    graph: Optional[WorkflowGraph] = None

    def to_dict(self) -> dict:
        result = {
            "workflow_id": self.workflow_id,
            "name": self.name,
            "description": self.description,
            "version": self.version,
            "status": self.status,
            "org_id": self.org_id,
            "created_by": self.created_by,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }
        if self.graph:
            result["graph"] = self.graph.to_dict()
        return result

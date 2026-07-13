"""Workflow graph, branch and debug-runtime tests."""

from unittest.mock import patch

from aitest.platform.workflow import WorkflowEdge, WorkflowGraph, WorkflowNode
from aitest.platform.workflow_executor import WorkflowExecutor, WorkflowRuntime
from aitest.platform.workspace import ExecutionContext
from aitest.server.api.workflows_v1_validate import validate_workflow_graph


def _runtime(graph):
    return WorkflowRuntime("debug-run", graph.workflow_id, ExecutionContext(workspace_id="ws", org_id="org", user_id="u"), {}, {})


def test_graph_accepts_arbitrary_edges_and_positions_round_trip():
    graph = WorkflowGraph.from_dict({
        "workflow_id": "wf", "name": "wf", "version": "1",
        "nodes": [{"node_id": "a", "type": "condition", "condition_expr": "True", "position": {"x": 12, "y": 24}}, {"node_id": "b", "type": "condition", "condition_expr": "True"}, {"node_id": "c", "type": "condition", "condition_expr": "True"}],
        "edges": [{"from": "a", "to": "c"}, {"from_node": "a", "to_node": "b", "condition": "always"}],
    })
    assert graph.nodes[0].position == {"x": 12, "y": 24}
    assert {(edge.from_node, edge.to_node) for edge in graph.edges} == {("a", "b"), ("a", "c")}


def test_debug_runtime_pauses_and_resumes_at_breakpoint():
    graph = WorkflowGraph(
        "wf", "wf", "1",
        nodes=[WorkflowNode("a", "condition", condition_expr="True"), WorkflowNode("b", "condition", condition_expr="True")],
        edges=[WorkflowEdge("a", "b", "always")],
    )
    runtime = _runtime(graph)
    executor = WorkflowExecutor(graph, runtime)
    paused = executor.execute_debug(breakpoints={"b"})
    assert paused["status"] == "paused"
    assert paused["completed_nodes"] == ["a"]
    resumed = executor.execute_debug()
    assert resumed["status"] == "completed"
    assert resumed["completed_nodes"] == ["a", "b"]
    assert any(event["event"] == "debug.paused" for event in resumed["events"])


def test_debug_runtime_follows_only_matching_branch():
    graph = WorkflowGraph(
        "wf", "wf", "1",
        nodes=[WorkflowNode("a", "condition", condition_expr="True"), WorkflowNode("yes", "condition", condition_expr="True"), WorkflowNode("no", "condition", condition_expr="True")],
        edges=[WorkflowEdge("a", "yes", "upstream.get('result') is True"), WorkflowEdge("a", "no", "False")],
    )
    result = WorkflowExecutor(graph, _runtime(graph)).execute_debug()
    assert result["status"] == "completed"
    assert "yes" in result["completed_nodes"]
    assert "no" not in result["completed_nodes"]


def test_validation_rejects_incomplete_parallel_node():
    graph = WorkflowGraph("wf", "wf", "1", nodes=[WorkflowNode("p", "parallel", metadata={})])
    errors, _ = validate_workflow_graph(graph, ["p"])
    assert any("parallel_nodes" in error for error in errors)

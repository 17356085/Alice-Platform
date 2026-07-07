"""Workflow graph registry tests."""

from alice_engine.workflow import (
    GraphContract,
    build_graph,
    get_graph_contract,
    list_graph_contracts,
    list_graphs,
    register_graph,
)


def test_builtin_graphs_are_discoverable():
    graphs = list_graphs()
    assert "sop" in graphs
    assert "parallel_sop" in graphs


def test_graph_contract_has_metadata():
    contract = get_graph_contract("sop")
    assert isinstance(contract, GraphContract)
    assert contract.graph_id == "sop"
    assert contract.builder_name == "build_sop_graph"
    assert contract.available is True


def test_list_graph_contracts_includes_builtin_graphs():
    contracts = list_graph_contracts()
    graph_ids = {c.graph_id for c in contracts}
    assert "sop" in graph_ids
    assert "parallel_sop" in graph_ids


def test_build_graph_returns_compilable_graph():
    graph = build_graph("sop")
    assert graph is not None
    compiled = graph.compile()
    assert compiled is not None


def test_register_custom_graph_contract():
    def _custom_graph(**kwargs):
        return {"built": True, "kwargs": kwargs}

    register_graph(
        "custom_demo",
        _custom_graph,
        name="Custom Demo Graph",
        description="test graph",
        module="tests.workflow",
        entrypoint="tests.workflow.custom",
    )

    contract = get_graph_contract("custom_demo")
    assert contract is not None
    assert contract.name == "Custom Demo Graph"
    assert contract.description == "test graph"

    built = build_graph("custom_demo", answer=42)
    assert built["built"] is True
    assert built["kwargs"]["answer"] == 42

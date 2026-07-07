"""Workflow graph registry — discovery and build contracts for graphs.

Phase 4 graph plugin contract:
  - graphs are registered by stable graph_id
  - each graph exposes a contract for discovery
  - callers can list or build graphs without importing implementation details
"""

from __future__ import annotations

from dataclasses import dataclass, field, replace
from typing import Any, Callable


GraphBuilder = Callable[..., Any]


@dataclass
class GraphContract:
    """Discovery metadata for a workflow graph."""

    graph_id: str
    name: str = ""
    description: str = ""
    module: str = ""
    builder_name: str = ""
    category: str = "workflow"
    entrypoint: str = ""
    supports_checkpoint: bool = True
    supports_parallel: bool = False
    available: bool = True
    source: str = "builtin"
    extra: dict[str, Any] = field(default_factory=dict)


@dataclass
class GraphDefinition:
    """Registered graph definition."""

    contract: GraphContract
    builder: GraphBuilder


class GraphRegistry:
    """Registry of workflow graphs and their contracts."""

    def __init__(self):
        self._definitions: dict[str, GraphDefinition] = {}

    def register(
        self,
        graph_id: str,
        builder: GraphBuilder,
        *,
        name: str = "",
        description: str = "",
        module: str = "",
        builder_name: str = "",
        category: str = "workflow",
        entrypoint: str = "",
        supports_checkpoint: bool = True,
        supports_parallel: bool = False,
        available: bool = True,
        source: str = "builtin",
        extra: dict[str, Any] | None = None,
    ) -> None:
        contract = GraphContract(
            graph_id=graph_id,
            name=name or graph_id,
            description=description,
            module=module,
            builder_name=builder_name or getattr(builder, "__name__", ""),
            category=category,
            entrypoint=entrypoint,
            supports_checkpoint=supports_checkpoint,
            supports_parallel=supports_parallel,
            available=available,
            source=source,
            extra=extra or {},
        )
        self._definitions[graph_id] = GraphDefinition(contract=contract, builder=builder)

    def register_contract(self, contract: GraphContract, builder: GraphBuilder) -> None:
        self._definitions[contract.graph_id] = GraphDefinition(contract=contract, builder=builder)

    def list_graphs(self) -> list[str]:
        return list(self._definitions.keys())

    def list_contracts(self) -> list[GraphContract]:
        return [definition.contract for definition in self._definitions.values()]

    def get_contract(self, graph_id: str) -> GraphContract | None:
        definition = self._definitions.get(graph_id)
        return definition.contract if definition else None

    def get_builder(self, graph_id: str) -> GraphBuilder | None:
        definition = self._definitions.get(graph_id)
        return definition.builder if definition else None

    def build(self, graph_id: str, **kwargs) -> Any:
        builder = self.get_builder(graph_id)
        if builder is None:
            raise KeyError(f"Unknown graph: {graph_id}")
        return builder(**kwargs)

    def discover(self) -> list[GraphContract]:
        return self.list_contracts()


_REGISTRY = GraphRegistry()
_BUILTIN_REGISTERED = False


def _register_builtin_graphs() -> None:
    global _BUILTIN_REGISTERED
    if _BUILTIN_REGISTERED:
        return

    from .sop_graph import build_compiled_graph, build_sop_graph
    from .parallel import compile_parallel_sop, build_parallel_sop_graph

    _REGISTRY.register(
        "sop",
        build_sop_graph,
        name="SOP Graph",
        description="Canonical sequential SOP orchestration graph",
        module="alice_engine.workflow.sop_graph",
        builder_name="build_sop_graph",
        entrypoint="workflow.sop_graph",
        supports_checkpoint=True,
        supports_parallel=False,
    )
    _REGISTRY.register(
        "sop_compiled",
        build_compiled_graph,
        name="Compiled SOP Graph",
        description="Canonical SOP graph compiled with checkpoint",
        module="alice_engine.workflow.sop_graph",
        builder_name="build_compiled_graph",
        entrypoint="workflow.sop_graph",
        supports_checkpoint=True,
        supports_parallel=False,
    )
    _REGISTRY.register(
        "parallel_sop",
        compile_parallel_sop,
        name="Parallel SOP Graph",
        description="LangGraph Send-based parallel SOP graph",
        module="alice_engine.workflow.parallel",
        builder_name="compile_parallel_sop",
        entrypoint="workflow.parallel",
        supports_checkpoint=True,
        supports_parallel=True,
    )
    _REGISTRY.register(
        "parallel_sop_builder",
        build_parallel_sop_graph,
        name="Parallel SOP Builder",
        description="Uncompiled parallel SOP builder",
        module="alice_engine.workflow.parallel",
        builder_name="build_parallel_sop_graph",
        entrypoint="workflow.parallel",
        supports_checkpoint=True,
        supports_parallel=True,
    )
    _BUILTIN_REGISTERED = True


def register_graph(graph_id: str, builder: GraphBuilder, **kwargs) -> None:
    _register_builtin_graphs()
    _REGISTRY.register(graph_id, builder, **kwargs)


def register_graph_contract(contract: GraphContract, builder: GraphBuilder) -> None:
    _register_builtin_graphs()
    _REGISTRY.register_contract(contract, builder)


def list_graphs() -> list[str]:
    _register_builtin_graphs()
    return _REGISTRY.list_graphs()


def list_graph_contracts() -> list[GraphContract]:
    _register_builtin_graphs()
    return _REGISTRY.list_contracts()


def get_graph_contract(graph_id: str) -> GraphContract | None:
    _register_builtin_graphs()
    return _REGISTRY.get_contract(graph_id)


def build_graph(graph_id: str, **kwargs) -> Any:
    _register_builtin_graphs()
    return _REGISTRY.build(graph_id, **kwargs)


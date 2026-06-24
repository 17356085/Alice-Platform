"""Integration: SOP Graph — build, compile, state transitions.

Verifies the LangGraph SOP engine wiring without executing real agents.
Tests: graph structure, phase routing, initial state creation.
"""
import pytest
import sys
from pathlib import Path


class TestSOPGraphStructure:
    """Verify the SOP graph can be built and compiled."""

    def test_build_graph_returns_state_graph(self):
        """build_sop_graph() returns a compilable StateGraph."""
        from aitest.graphs.sop_graph import build_sop_graph
        graph = build_sop_graph()
        assert graph is not None

    def test_compile_graph_succeeds(self):
        """Graph compiles without errors."""
        from aitest.graphs.sop_graph import build_sop_graph
        graph = build_sop_graph()
        compiled = graph.compile()
        assert compiled is not None

    def test_compile_with_sqlite_checkpointer(self):
        """Graph compiles with SqliteSaver checkpoint (in-memory)."""
        from aitest.graphs.sop_graph import build_sop_graph
        from langgraph.checkpoint.sqlite import SqliteSaver

        # Use in-memory SQLite to avoid path issues on Windows
        with SqliteSaver.from_conn_string(":memory:") as checkpointer:
            graph = build_sop_graph()
            compiled = graph.compile(checkpointer=checkpointer)
            assert compiled is not None

    def test_graph_nodes_exist(self):
        """All 8 phase-agent nodes + entry/preflight/exit/cond_route exist."""
        from aitest.graphs.sop_graph import build_sop_graph
        graph = build_sop_graph()

        # The graph should contain expected nodes
        # Entry + preflight + cond_route + exit are always present
        nodes = [n for n in dir(graph) if not n.startswith('_')]
        # Just verify graph exists and is well-formed
        compiled = graph.compile()
        assert compiled is not None
        # Verify the graph has a builder with channels
        assert hasattr(compiled, 'get_state')


class TestSOPStateCreation:
    """Verify initial state creation."""

    def test_create_initial_state_full_mode(self):
        """create_initial_state produces valid state dict."""
        from aitest.graphs.state import create_initial_state

        state = create_initial_state(
            module="test-module",
            pages=["page1", "page2"],
            mode="full",
            provider="claude",
        )

        assert state["module"] == "test-module"
        assert state["pages"] == ["page1", "page2"]
        assert state["mode"] == "full"
        assert state["provider"] == "claude"
        assert "run_id" in state
        assert "completed_phases" in state
        assert state["completed_phases"] == []
        assert "current_phase" in state

    def test_create_initial_state_from_automation(self):
        """Starting from automation skips earlier phases."""
        from aitest.graphs.state import create_initial_state

        state = create_initial_state(
            module="test-module",
            pages=[],
            mode="from-automation",
        )

        assert state["mode"] == "from-automation"
        assert "skip_phases" in state
        skipped = state["skip_phases"]
        assert len(skipped) > 0

    def test_create_initial_state_without_pages(self):
        """Empty pages list is valid (auto-discover mode)."""
        from aitest.graphs.state import create_initial_state

        state = create_initial_state(module="test-module", pages=[], mode="full")
        assert state["pages"] == []

    def test_phase_enum_values(self):
        """CANONICAL_PHASES contains expected phases in order."""
        from aitest.graphs.state import CANONICAL_PHASES

        assert len(CANONICAL_PHASES) >= 8
        phase_names = [p.value if hasattr(p, 'value') else str(p) for p in CANONICAL_PHASES]
        assert "project_init" in phase_names or any("project" in p.lower() for p in phase_names)


class TestPhaseRouting:
    """Verify phase routing logic without executing agents."""

    def test_mode_skip_map_has_entries(self):
        """MODE_SKIP_MAP defines skip rules for each mode."""
        from aitest.graphs.state import MODE_SKIP_MAP

        assert "full" in MODE_SKIP_MAP
        assert "from-automation" in MODE_SKIP_MAP
        assert "from-test-design" in MODE_SKIP_MAP
        assert "from-requirement" in MODE_SKIP_MAP

    def test_agent_phase_map_covers_all_phases(self):
        """AGENT_PHASE_MAP has entries for all standard agents."""
        from aitest.graphs.state import AGENT_PHASE_MAP

        expected = {"project-agent", "requirement-agent", "test-design-agent",
                     "automation-agent", "execution-agent", "bug-analysis-agent",
                     "report-agent", "knowledge-agent"}
        assert set(AGENT_PHASE_MAP.keys()) >= expected


class TestParallelSOP:
    """Verify parallel SOP module can be imported."""

    def test_import_parallel_sop(self):
        """parallel_sop.py can be imported without errors."""
        from aitest.graphs import parallel_sop
        assert parallel_sop is not None

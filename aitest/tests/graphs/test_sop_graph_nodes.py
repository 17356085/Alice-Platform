"""Tests for graphs/sop_graph.py — node functions.

Tests: entry_node, preflight_node, page_advance_node, _route_after_page_advance.
Pure node functions — no LangGraph compilation.
"""
import pytest
from unittest.mock import patch, MagicMock

from aitest.graphs.sop_graph import (
    entry_node, page_advance_node, _route_after_page_advance,
    PHASE_TO_NODE, ALL_AGENT_NODES, _CUSTOM_EDGE_NODES,
)
from aitest.graphs.state import CANONICAL_PHASES, create_initial_state


# ══════════════════════════════════════════════════════════════════════════
#  Helpers
# ══════════════════════════════════════════════════════════════════════════


def _make_state(**overrides) -> dict:
    state = create_initial_state("equipment", ["alarm"])
    state.update(overrides)
    return state


# ══════════════════════════════════════════════════════════════════════════
#  entry_node
# ══════════════════════════════════════════════════════════════════════════


class TestEntryNode:
    def test_full_mode_no_skip(self):
        state = _make_state(mode="full")
        result = entry_node(state)
        assert result["skip_phases"] == []
        assert result["status"] == "running"

    def test_from_requirement_skips_project_init(self):
        state = _make_state(mode="from-requirement")
        result = entry_node(state)
        assert "Project Init" in result["skip_phases"]

    def test_from_test_design_skips_two(self):
        state = _make_state(mode="from-test-design")
        result = entry_node(state)
        assert "Project Init" in result["skip_phases"]
        assert "Requirement" in result["skip_phases"]

    def test_from_automation_skips_three(self):
        state = _make_state(mode="from-automation")
        result = entry_node(state)
        assert len(result["skip_phases"]) == 3

    def test_status_mode(self):
        state = _make_state(mode="status")
        result = entry_node(state)
        assert result["current_phase"] == "Preflight"
        assert result["status"] == "running"

    def test_resume_mode_empty_skip(self):
        state = _make_state(mode="resume")
        result = entry_node(state)
        # Resume mode: skip_phases stays empty, preflight decides
        assert result["skip_phases"] == []


# ══════════════════════════════════════════════════════════════════════════
#  page_advance_node
# ══════════════════════════════════════════════════════════════════════════


class TestPageAdvanceNode:
    def test_advances_index(self):
        state = _make_state(pages=["alarm", "camera", "key-param"],
                            current_page_index=0)
        result = page_advance_node(state)
        assert result["current_page_index"] == 1

    def test_advances_from_middle(self):
        state = _make_state(pages=["alarm", "camera", "key-param"],
                            current_page_index=1)
        result = page_advance_node(state)
        assert result["current_page_index"] == 2

    def test_caps_at_length(self):
        state = _make_state(pages=["alarm", "camera"],
                            current_page_index=2)
        result = page_advance_node(state)
        # Already at end, should cap at len(pages)
        assert result["current_page_index"] == 2

    def test_force_retry_no_advance(self):
        state = _make_state(pages=["alarm", "camera"],
                            current_page_index=0,
                            force_retry_phase="Automation")
        result = page_advance_node(state)
        assert result == {}  # No advance during retry


# ══════════════════════════════════════════════════════════════════════════
#  _route_after_page_advance
# ══════════════════════════════════════════════════════════════════════════


class TestRouteAfterPageAdvance:
    def test_more_pages_goes_to_test_design(self):
        state = _make_state(pages=["alarm", "camera"],
                            current_page_index=1)
        result = _route_after_page_advance(state)
        assert result == "test_design_agent"

    def test_no_more_pages_exits(self):
        state = _make_state(pages=["alarm"],
                            current_page_index=1,
                            completed_phases=list(CANONICAL_PHASES))
        result = _route_after_page_advance(state)
        assert result == "exit"

    def test_force_retry_overrides(self):
        state = _make_state(
            pages=["alarm", "camera"],
            current_page_index=1,
            force_retry_phase="Automation",
        )
        result = _route_after_page_advance(state)
        assert result == "automation_agent_pre"


# ══════════════════════════════════════════════════════════════════════════
#  Constants
# ══════════════════════════════════════════════════════════════════════════


class TestConstants:
    def test_phase_to_node_complete(self):
        for phase in CANONICAL_PHASES:
            assert phase in PHASE_TO_NODE

    def test_all_agent_nodes_contains_all(self):
        for node in PHASE_TO_NODE.values():
            assert node in ALL_AGENT_NODES

    def test_custom_edge_nodes_are_subset(self):
        for node in _CUSTOM_EDGE_NODES:
            assert node in ALL_AGENT_NODES or node in (
                "automation_strategy_approval", "testcase_approval",
                "testcase_quality_gate", "page_advance",
            )

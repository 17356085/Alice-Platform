"""Tests for graphs/sop_graph.py — route_next_phase routing logic.

Tests: PHASE_TO_NODE, route_next_phase (fatal error, status mode,
skip phases, Bug Analysis conditional, force_retry).
Pure function — no LangGraph execution.
"""
import pytest

from aitest.graphs.sop_graph import route_next_phase, PHASE_TO_NODE
from aitest.graphs.state import CANONICAL_PHASES, create_initial_state


# ══════════════════════════════════════════════════════════════════════════
#  Helpers
# ══════════════════════════════════════════════════════════════════════════


def _make_state(**overrides) -> dict:
    state = create_initial_state("equipment", ["alarm"])
    state.update(overrides)
    return state


# ══════════════════════════════════════════════════════════════════════════
#  PHASE_TO_NODE
# ══════════════════════════════════════════════════════════════════════════


class TestPhaseToNode:
    def test_all_canonical_phases_mapped(self):
        for phase in CANONICAL_PHASES:
            assert phase in PHASE_TO_NODE, f"'{phase}' not in PHASE_TO_NODE"

    def test_automation_maps_to_pre(self):
        assert PHASE_TO_NODE["Automation"] == "automation_agent_pre"

    def test_values_are_strings(self):
        for node in PHASE_TO_NODE.values():
            assert isinstance(node, str)


# ══════════════════════════════════════════════════════════════════════════
#  route_next_phase
# ══════════════════════════════════════════════════════════════════════════


class TestRouteNextPhase:
    def test_fatal_error_exits(self):
        state = _make_state(fatal_error="Something broke")
        assert route_next_phase(state) == "exit"

    def test_status_mode_exits(self):
        state = _make_state(mode="status")
        assert route_next_phase(state) == "exit"

    def test_force_retry_overrides(self):
        state = _make_state(
            completed_phases=["Project Init", "Requirement"],
            force_retry_phase="Requirement",
        )
        result = route_next_phase(state)
        assert result == "requirement_agent"

    def test_force_retry_invalid_phase_skips(self):
        state = _make_state(force_retry_phase="Nonexistent Phase")
        # force_retry_phase not in PHASE_TO_NODE → falls through to normal routing
        result = route_next_phase(state)
        assert result != "exit"  # Should proceed normally

    def test_first_phase_project_init(self):
        state = _make_state(completed_phases=[])
        result = route_next_phase(state)
        assert result == "project_agent"

    def test_skips_completed_phases(self):
        state = _make_state(completed_phases=["Project Init", "Requirement"])
        result = route_next_phase(state)
        assert result == "test_design_agent"

    def test_skips_skip_phases(self):
        state = _make_state(
            mode="from-requirement",
            skip_phases=["Project Init"],
            completed_phases=[],
        )
        result = route_next_phase(state)
        # Project Init skipped → next is Requirement
        assert result == "requirement_agent"

    def test_all_completed_exits(self):
        state = _make_state(completed_phases=list(CANONICAL_PHASES))
        result = route_next_phase(state)
        assert result == "exit"

    def test_bug_analysis_skipped_when_no_failure(self):
        """Bug Analysis should be skipped if execution didn't fail."""
        state = _make_state(
            completed_phases=["Project Init", "Requirement", "Test Design",
                              "Automation", "Execute & Debug"],
            agent_outputs={"execution-agent": {"success": True, "execution_failed": False}},
        )
        result = route_next_phase(state)
        # Bug Analysis skipped → goes to Data Sanitization
        assert result == "data_sanitization_agent"

    def test_bug_analysis_triggered_on_failure(self):
        """Bug Analysis should run if execution failed."""
        state = _make_state(
            completed_phases=["Project Init", "Requirement", "Test Design",
                              "Automation", "Execute & Debug"],
            agent_outputs={"execution-agent": {"success": False, "execution_failed": True}},
        )
        result = route_next_phase(state)
        assert result == "bug_analysis_agent"

    def test_bug_analysis_via_execution_failed_flag(self):
        """execution_failed flag on agent_outputs triggers Bug Analysis."""
        state = _make_state(
            completed_phases=["Project Init", "Requirement", "Test Design",
                              "Automation", "Execute & Debug"],
            agent_outputs={"execution_failed": True},
        )
        result = route_next_phase(state)
        assert result == "bug_analysis_agent"

    def test_mixed_completed_and_skipped(self):
        state = _make_state(
            completed_phases=["Project Init", "Test Design"],
            skip_phases=["Requirement"],
            test_cases_approved=True,  # Skip HITL approval gate
        )
        result = route_next_phase(state)
        # Requirement skipped, Test Design done → next is Automation
        assert result == "automation_agent_pre"

    def test_exit_when_all_done_including_bug_analysis(self):
        state = _make_state(
            completed_phases=["Project Init", "Requirement", "Test Design",
                              "Automation", "Execute & Debug", "Bug Analysis",
                              "Data Sanitization", "Report", "Knowledge"],
        )
        result = route_next_phase(state)
        assert result == "exit"

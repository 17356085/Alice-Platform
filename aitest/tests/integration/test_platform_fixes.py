"""Integration tests for platform fixes (2026-06-30 Round 5).

Covers:
  - C6: parallel_sop merge_pages + canonical phase names
  - H7: parallel_sop error propagation (phase failure → break)
  - H3/H4: agent_runner cleanup attribute initialization
  - H5: sop_graph qa_loop_decision_node purity
  - C2: execution_graph generator fix
"""
import pytest
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch


# ══════════════════════════════════════════════════════════════════════════
#  C6 + H7: parallel_sop
# ══════════════════════════════════════════════════════════════════════════

class TestParallelSOPFixes:
    """Verify parallel_sop merge + error propagation fixes."""

    def test_phase_slug_to_canonical_mapping(self):
        """C6: process_single_page maps phase slugs to canonical PhaseName."""
        from alice_engine.workflow.parallel import _PHASE_SLUG_TO_CANONICAL

        assert _PHASE_SLUG_TO_CANONICAL["project_init"] == "Project Init"
        assert _PHASE_SLUG_TO_CANONICAL["requirement"] == "Requirement"
        assert _PHASE_SLUG_TO_CANONICAL["test_design"] == "Test Design"
        assert _PHASE_SLUG_TO_CANONICAL["automation"] == "Automation"
        assert _PHASE_SLUG_TO_CANONICAL["execution"] == "Execute & Debug"
        assert _PHASE_SLUG_TO_CANONICAL["report"] == "Report"
        assert len(_PHASE_SLUG_TO_CANONICAL) == 9  # all phases mapped

    def test_process_single_page_no_page(self):
        """Returns failed result when no page specified."""
        from alice_engine.workflow.parallel import process_single_page

        state = {"module": "test", "pages": [], "provider": "claude"}
        result = process_single_page(state)

        assert "per_page_results" in result
        assert result["per_page_results"][0]["status"] == "failed"
        assert result["per_page_results"][0]["page"] == "unknown"

    def test_process_single_page_error_propagation(self):
        """H7: Phase failure → break, page status reflects partial/failed."""
        from alice_engine.workflow.parallel import process_single_page

        # Mock _run_agent to fail on first phase
        with patch("aitest.graphs.parallel_sop._run_agent", side_effect=RuntimeError("Boom")):
            state = {"module": "test", "pages": ["test-page"], "provider": "claude"}
            result = process_single_page(state)

        page_results = result["per_page_results"]
        assert len(page_results) == 1
        pr = page_results[0]
        # First phase failed → no phases completed, status = "failed"
        assert pr["status"] == "failed"
        assert pr["phases_completed"] == []
        assert "first_failure" in pr
        assert "project_init_error" in pr

    def test_process_single_page_partial_completion(self):
        """H7: Some phases succeed, then failure → status='partial'."""
        from alice_engine.workflow.parallel import process_single_page

        call_count = [0]

        def flaky_agent(*args, **kwargs):
            call_count[0] += 1
            if call_count[0] >= 3:  # Fail on 3rd phase (test_design)
                raise RuntimeError("Boom at phase 3")
            return {"success": True}

        with patch("aitest.graphs.parallel_sop._run_agent", side_effect=flaky_agent):
            state = {"module": "test", "pages": ["test-page"], "provider": "claude"}
            result = process_single_page(state)

        pr = result["per_page_results"][0]
        assert pr["status"] == "partial"
        assert len(pr["phases_completed"]) == 2  # first 2 succeeded
        assert pr["phases_completed"][0] == "Project Init"  # canonical name
        assert "test_design_error" in pr

    def test_merge_pages_does_not_overwrite_status(self):
        """C6: merge_pages writes to agent_outputs, not top-level status."""
        from alice_engine.workflow.parallel import merge_pages

        state = {
            "pages": ["a", "b"],
            "per_page_results": [
                {"page": "a", "status": "completed", "phases_completed": ["Project Init"]},
                {"page": "b", "status": "failed", "phases_completed": [], "first_failure": "boom"},
            ],
            "agent_outputs": {},
        }

        result = merge_pages(state)

        # Should NOT have top-level "status" key (that's SOPState.status)
        assert "status" not in result
        # Should write to agent_outputs
        assert "agent_outputs" in result
        merge = result["agent_outputs"]["parallel_merge"]
        assert merge["parallel_status"] == "partial_failure"
        assert merge["completed_pages"] == 1
        assert merge["failed_pages"] == 1
        assert merge["total_pages"] == 2

    def test_merge_pages_all_completed(self):
        """All pages succeed → parallel_status = 'completed'."""
        from alice_engine.workflow.parallel import merge_pages

        state = {
            "pages": ["a"],
            "per_page_results": [
                {"page": "a", "status": "completed", "phases_completed": ["Project Init", "Requirement"]},
            ],
            "agent_outputs": {},
        }

        result = merge_pages(state)
        merge = result["agent_outputs"]["parallel_merge"]
        assert merge["parallel_status"] == "completed"
        assert merge["completed_pages"] == 1
        assert merge["failed_pages"] == 0

    def test_compile_parallel_sop_graph(self):
        """Parallel SOP graph compiles without errors."""
        from alice_engine.workflow.parallel import compile_parallel_sop
        graph = compile_parallel_sop()
        assert graph is not None


# ══════════════════════════════════════════════════════════════════════════
#  H3 + H4: agent_runner cleanup safety
# ══════════════════════════════════════════════════════════════════════════

class TestAgentRunnerCleanup:
    """Verify agent_runner cleanup attribute initialization."""

    def test_cleanup_attrs_initialized_in_init(self):
        """H3: _mcp_clients, _wt_mgr, _worktree_ctx initialized in __init__."""
        from alice_engine.core.executor import AgentLoop

        agent = AgentLoop("project-agent", module="test", page="test")

        assert hasattr(agent, "_mcp_clients")
        assert agent._mcp_clients == []
        assert hasattr(agent, "_wt_mgr")
        assert agent._wt_mgr is None
        assert hasattr(agent, "_worktree_ctx")
        assert agent._worktree_ctx is None

    def test_finalize_session_safe_without_run(self):
        """H3: _finalize_session doesn't crash when called before _run_single_session."""
        from alice_engine.core.executor import AgentLoop

        agent = AgentLoop("project-agent", module="test", page="test")
        # _finalize_session should be safe even if _run_single_session never ran
        agent._finalize_session()
        assert agent._session_finalized is True

    def test_finalize_session_idempotent(self):
        """_finalize_session is idempotent — safe to call multiple times."""
        from alice_engine.core.executor import AgentLoop

        agent = AgentLoop("project-agent", module="test", page="test")
        agent._finalize_session()
        agent._finalize_session()  # second call should not crash
        assert agent._session_finalized is True


# ══════════════════════════════════════════════════════════════════════════
#  H5: sop_graph qa_loop_decision_node
# ══════════════════════════════════════════════════════════════════════════

class TestQALoopDecision:
    """Verify QA loop decision node is a pure state machine (H5 fix)."""

    def test_qa_loop_decision_node_exists(self):
        """qa_loop_decision_node is importable."""
        from alice_engine.workflow.sop_graph import qa_loop_decision_node
        assert callable(qa_loop_decision_node)

    def test_qa_loop_escalate_returns_report(self):
        """Escalate → skip auto-fix, route to report."""
        from alice_engine.workflow.sop_graph import qa_loop_decision_node

        state = {
            "completed_phases": ["Bug Analysis"],
            "agent_outputs": {"execution_failed": True},
            "qa_loop_rounds": 0,
            "qa_loop_max_rounds": 3,
            "qa_should_escalate": True,
            "qa_loop_phases_seen": [],
            "run_id": "test-run",
            "module": "test",
        }

        result = qa_loop_decision_node(state)

        assert result["qa_loop_status"] == "escalated"
        assert result["qa_loop_decision"] == "report"

    def test_qa_loop_retry_routes_to_automation(self):
        """Still have retry budget + failures → route to automation."""
        from alice_engine.workflow.sop_graph import qa_loop_decision_node

        state = {
            "completed_phases": ["Bug Analysis"],
            "agent_outputs": {"execution-agent": {"execution_failed": True, "success": False}},
            "qa_loop_rounds": 0,
            "qa_loop_max_rounds": 3,
            "qa_should_escalate": False,
            "qa_loop_phases_seen": ["Bug Analysis"],
            "run_id": "test-run",
            "module": "test",
        }

        result = qa_loop_decision_node(state)

        assert result["qa_loop_decision"] == "automation"
        assert result["qa_loop_rounds"] == 1  # incremented

    def test_qa_loop_max_rounds_returns_next_phase(self):
        """Retry budget exhausted → continue to next phase."""
        from alice_engine.workflow.sop_graph import qa_loop_decision_node

        state = {
            "completed_phases": ["Bug Analysis"],
            "agent_outputs": {"execution-agent": {"execution_failed": True, "success": False}},
            "qa_loop_rounds": 3,
            "qa_loop_max_rounds": 3,
            "qa_should_escalate": False,
            "qa_loop_phases_seen": ["Bug Analysis"],
            "run_id": "test-run",
            "module": "test",
        }

        result = qa_loop_decision_node(state)

        assert result["qa_loop_decision"] == "next_phase"
        assert result["qa_loop_status"] == "max_rounds"

    def test_route_next_phase_is_pure(self):
        """H5: route_next_phase does not modify state (no side effects)."""
        from alice_engine.workflow.sop_graph import route_next_phase
        import copy

        state = {
            "module": "test",
            "pages": ["a"],
            "mode": "full",
            "completed_phases": ["Project Init", "Requirement", "Test Design",
                                  "Automation", "Execute & Debug"],
            "failed_phases": [],
            "skip_phases": [],
            "agent_outputs": {"execution-agent": {"success": True, "execution_failed": False}},
            "qa_loop_rounds": 0,
            "qa_loop_should_escalate": False,
            "qa_loop_phases_seen": [],
            "run_id": "test",
            "provider": "claude",
            "current_page_index": 0,
            "test_cases_approved": True,
            "auto_strategy_approved": True,
            "per_page_results": [],
            "gate_results": [],
            "artifact_map": {},
            "skill_observations": [],
        }

        before = copy.deepcopy(state)
        result = route_next_phase(state)

        # State must be unchanged (pure function)
        assert state == before, f"route_next_phase mutated state: {state} != {before}"
        # Should route to next canonical phase (Bug Analysis skipped, so Data Sanitization)
        assert result in ("bug_analysis_agent", "data_sanitization_agent", "report_agent")


# ══════════════════════════════════════════════════════════════════════════
#  C2: execution_graph generator fix
# ══════════════════════════════════════════════════════════════════════════

class TestExecutionGraphFixes:
    """Verify execution_graph generator fix (C2)."""

    def test_knowledge_exit_uses_chain_not_pipe(self):
        """C2: generator | operator replaced with itertools.chain."""
        import ast, inspect
        from aitest.graphs import execution_graph

        source = inspect.getsource(execution_graph)
        # Generator | operator should not appear
        assert "glob(" not in source or "| output_dir.glob" not in source, \
            "Generator pipe operator still present in execution_graph"

    def test_no_hardcoded_path(self):
        """H10: execution_graph uses get_test_project_root, not hardcoded path."""
        import inspect
        from aitest.graphs import execution_graph

        source = inspect.getsource(execution_graph)
        assert "D:/Desktop/Alice/allure-results" not in source, \
            "Hardcoded path still present in execution_graph"


# ══════════════════════════════════════════════════════════════════════════
#  bu_adapter M11 fix
# ══════════════════════════════════════════════════════════════════════════

class TestBuAdapterFixes:
    """Verify bu_adapter JSON extraction logging (M11)."""

    def test_try_parse_json_no_input(self):
        """Returns None for empty/None input."""
        from aitest.bu_adapter import BrowserUseSkillAdapter
        result = BrowserUseSkillAdapter._try_parse_json("")
        assert result is None
        result = BrowserUseSkillAdapter._try_parse_json(None)
        assert result is None

    def test_try_parse_json_raw_object(self):
        """Parses raw JSON object."""
        from aitest.bu_adapter import BrowserUseSkillAdapter
        result = BrowserUseSkillAdapter._try_parse_json('{"key": "value"}')
        assert result == {"key": "value"}

    def test_try_parse_json_fenced_block(self):
        """Parses ```json ... ``` block."""
        from aitest.bu_adapter import BrowserUseSkillAdapter
        text = 'some text\n```json\n{"key": "value"}\n```\nmore text'
        result = BrowserUseSkillAdapter._try_parse_json(text)
        assert result == {"key": "value"}

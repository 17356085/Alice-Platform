"""Tests for graphs/parallel_sop.py — merge_pages, fanout, process_single_page.

Tests: merge_pages (all completed, partial, all failed, empty),
process_single_page (mocked _run_agent), fanout_pages,
benchmark_parallel_vs_sequential.
No real AgentLoop execution — _run_agent is mocked.
"""
import pytest
from unittest.mock import patch, MagicMock

from alice_engine.workflow.parallel import (
    merge_pages, process_single_page, fanout_pages,
    benchmark_parallel_vs_sequential, _PHASE_SLUG_TO_CANONICAL,
)


# ══════════════════════════════════════════════════════════════════════════
#  Helpers
# ══════════════════════════════════════════════════════════════════════════


def _make_state(pages, per_page_results=None, agent_outputs=None):
    return {
        "module": "equipment",
        "pages": pages,
        "per_page_results": per_page_results or [],
        "agent_outputs": agent_outputs or {},
        "provider": "claude",
        "mode": "full",
        "run_id": "test-run",
    }


# ══════════════════════════════════════════════════════════════════════════
#  merge_pages
# ══════════════════════════════════════════════════════════════════════════


class TestMergePages:
    def test_all_completed(self):
        state = _make_state(
            pages=["alarm", "camera"],
            per_page_results=[
                {"page": "alarm", "status": "completed", "phases_completed": ["Project Init", "Automation"]},
                {"page": "camera", "status": "completed", "phases_completed": ["Project Init", "Automation"]},
            ],
        )
        result = merge_pages(state)
        merge = result["agent_outputs"]["parallel_merge"]
        assert merge["parallel_status"] == "completed"
        assert merge["total_pages"] == 2
        assert merge["completed_pages"] == 2
        assert merge["failed_pages"] == 0
        assert merge["partial_pages"] == 0

    def test_some_failed(self):
        state = _make_state(
            pages=["alarm", "camera", "key-param"],
            per_page_results=[
                {"page": "alarm", "status": "completed", "phases_completed": ["Project Init"]},
                {"page": "camera", "status": "failed", "phases_completed": []},
                {"page": "key-param", "status": "completed", "phases_completed": ["Project Init"]},
            ],
        )
        result = merge_pages(state)
        merge = result["agent_outputs"]["parallel_merge"]
        assert merge["parallel_status"] == "partial_failure"
        assert merge["completed_pages"] == 2
        assert merge["failed_pages"] == 1

    def test_all_failed(self):
        state = _make_state(
            pages=["alarm", "camera"],
            per_page_results=[
                {"page": "alarm", "status": "failed", "phases_completed": []},
                {"page": "camera", "status": "failed", "phases_completed": []},
            ],
        )
        result = merge_pages(state)
        merge = result["agent_outputs"]["parallel_merge"]
        assert merge["parallel_status"] == "all_failed"
        assert merge["completed_pages"] == 0
        assert merge["failed_pages"] == 2

    def test_mixed_with_partial(self):
        state = _make_state(
            pages=["alarm", "camera"],
            per_page_results=[
                {"page": "alarm", "status": "completed", "phases_completed": ["A", "B"]},
                {"page": "camera", "status": "partial", "phases_completed": ["A"]},
            ],
        )
        result = merge_pages(state)
        merge = result["agent_outputs"]["parallel_merge"]
        # partial + completed → partial_failure (because partial != completed)
        assert merge["parallel_status"] == "partial_failure"
        assert merge["partial_pages"] == 1

    def test_empty_page_results(self):
        state = _make_state(pages=["alarm"], per_page_results=[])
        result = merge_pages(state)
        merge = result["agent_outputs"]["parallel_merge"]
        assert merge["completed_pages"] == 0
        assert merge["total_pages"] == 1

    def test_preserves_existing_agent_outputs(self):
        state = _make_state(
            pages=["alarm"],
            per_page_results=[
                {"page": "alarm", "status": "completed", "phases_completed": []},
            ],
            agent_outputs={"existing_key": "value"},
        )
        result = merge_pages(state)
        assert result["agent_outputs"]["existing_key"] == "value"
        assert "parallel_merge" in result["agent_outputs"]

    def test_does_not_overwrite_status(self):
        """merge_pages returns agent_outputs, not status — different semantics."""
        state = _make_state(
            pages=["alarm"],
            per_page_results=[
                {"page": "alarm", "status": "completed", "phases_completed": []},
            ],
        )
        result = merge_pages(state)
        assert "status" not in result  # Not overwriting SOPState.status


# ══════════════════════════════════════════════════════════════════════════
#  process_single_page (mocked _run_agent)
# ══════════════════════════════════════════════════════════════════════════


class TestProcessSinglePage:
    def test_no_pages_returns_failed(self):
        state = {"module": "equipment", "pages": [], "provider": "claude"}
        result = process_single_page(state)
        assert len(result["per_page_results"]) == 1
        assert result["per_page_results"][0]["status"] == "failed"
        assert "No page specified" in result["per_page_results"][0]["error"]

    def test_all_phases_succeed(self, monkeypatch):
        """When all agents succeed, page status = completed."""
        mock_run = MagicMock()
        mock_run.return_value = {"agent": "x", "success": True,
                                  "completed_skills": [], "failed_skills": [],
                                  "termination": "completed"}
        monkeypatch.setattr("aitest.graphs.parallel_sop._run_agent", mock_run)

        state = {"module": "equipment", "pages": ["alarm"], "provider": "claude"}
        result = process_single_page(state)

        assert len(result["per_page_results"]) == 1
        page = result["per_page_results"][0]
        assert page["status"] == "completed"
        assert len(page["phases_completed"]) == 6  # All 6 phases
        # Phase names should be canonical
        assert "Project Init" in page["phases_completed"]

    def test_phase_failure_stops_execution(self, monkeypatch):
        """H7: first failure → break, subsequent phases skipped."""
        call_count = [0]

        def failing_agent(agent_name, module, page, provider):
            call_count[0] += 1
            if call_count[0] >= 3:  # Fail on 3rd phase
                raise RuntimeError("Agent crashed")

        monkeypatch.setattr("aitest.graphs.parallel_sop._run_agent", failing_agent)

        state = {"module": "equipment", "pages": ["alarm"], "provider": "claude"}
        result = process_single_page(state)

        page = result["per_page_results"][0]
        assert page["status"] == "partial"  # 2 completed, then failure
        assert len(page["phases_completed"]) == 2  # Only first 2
        assert call_count[0] == 3  # 2 success + 1 failure = 3 calls

    def test_first_phase_failure_marks_failed(self, monkeypatch):
        """All-zero → status = failed."""
        def always_fail(*args, **kwargs):
            raise RuntimeError("Agent unavailable")

        monkeypatch.setattr("aitest.graphs.parallel_sop._run_agent", always_fail)

        state = {"module": "equipment", "pages": ["alarm"], "provider": "claude"}
        result = process_single_page(state)

        page = result["per_page_results"][0]
        assert page["status"] == "failed"
        assert page["phases_completed"] == []

    def test_returns_per_page_results_with_reducer_key(self, monkeypatch):
        """Must return per_page_results (operator.add reducer) for accumulation."""
        mock_run = MagicMock(return_value={"agent": "x", "success": True,
                                            "completed_skills": [], "failed_skills": [],
                                            "termination": "completed"})
        monkeypatch.setattr("aitest.graphs.parallel_sop._run_agent", mock_run)

        state = {"module": "equipment", "pages": ["alarm"], "provider": "claude"}
        result = process_single_page(state)

        # Key must be "per_page_results" for operator.add reducer
        assert "per_page_results" in result
        assert isinstance(result["per_page_results"], list)
        assert result["per_page_results"][0]["page"] == "alarm"


# ══════════════════════════════════════════════════════════════════════════
#  fanout_pages
# ══════════════════════════════════════════════════════════════════════════


class TestFanoutPages:
    def test_empty_pages_returns_empty(self):
        state = {"pages": [], "module": "equipment"}
        sends = fanout_pages(state)
        assert sends == []

    def test_creates_one_send_per_page(self):
        state = {
            "pages": ["alarm", "camera", "key-param"],
            "module": "equipment",
            "provider": "deepseek",
            "mode": "full",
            "run_id": "r1",
            "complexity_tier": "standard",
        }
        sends = fanout_pages(state)
        assert len(sends) == 3
        # Each Send targets process_single_page
        for send in sends:
            assert send.node == "process_single_page"
            assert send.arg["pages"] == [send.arg["pages"][0]]  # Single page
        # Verify page isolation
        pages_seen = [s.arg["pages"][0] for s in sends]
        assert pages_seen == ["alarm", "camera", "key-param"]

    def test_default_provider(self):
        state = {"pages": ["x"], "module": "m"}
        sends = fanout_pages(state)
        assert sends[0].arg["provider"] == "claude"


# ══════════════════════════════════════════════════════════════════════════
#  benchmark_parallel_vs_sequential
# ══════════════════════════════════════════════════════════════════════════


class TestBenchmark:
    def test_single_page(self):
        result = benchmark_parallel_vs_sequential("equipment", ["alarm"])
        assert result["pages"] == 1
        assert result["sequential_est_seconds"] == 120
        assert result["speedup"] == 1.0

    def test_multiple_pages_speedup(self):
        result = benchmark_parallel_vs_sequential("equipment", ["a", "b", "c"])
        assert result["pages"] == 3
        assert result["speedup"] > 1.0

    def test_speedup_increases_with_pages(self):
        r2 = benchmark_parallel_vs_sequential("m", ["a", "b"])
        r5 = benchmark_parallel_vs_sequential("m", ["a", "b", "c", "d", "e"])
        assert r5["speedup"] > r2["speedup"]


# ══════════════════════════════════════════════════════════════════════════
#  _PHASE_SLUG_TO_CANONICAL
# ══════════════════════════════════════════════════════════════════════════


class TestPhaseSlugMapping:
    def test_all_slugs_map_to_valid_phases(self):
        from aitest.graphs.state import CANONICAL_PHASES
        for slug, canonical in _PHASE_SLUG_TO_CANONICAL.items():
            assert canonical in CANONICAL_PHASES, \
                f"'{canonical}' from slug '{slug}' not in CANONICAL_PHASES"

    def test_known_slugs(self):
        assert _PHASE_SLUG_TO_CANONICAL["project_init"] == "Project Init"
        assert _PHASE_SLUG_TO_CANONICAL["automation"] == "Automation"
        assert _PHASE_SLUG_TO_CANONICAL["report"] == "Report"

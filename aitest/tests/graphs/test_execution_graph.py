"""Tests for graphs/execution_graph.py — pure node functions.

Tests: _get_page, exec_entry, exec_exit, report_entry, report_exit,
knowledge_entry, knowledge_exit, build_execution_subgraph structure.
No real AgentLoop — only tests pure state transformations.
"""
import pytest
from unittest.mock import MagicMock

from alice_engine.workflow.execution_graph import (
    _get_page, exec_entry, exec_exit, exec_gate,
    report_entry, report_exit, report_act, report_act2,
    knowledge_entry, knowledge_exit, knowledge_act,
    REPORT_SKILLS,
    build_execution_subgraph, build_report_subgraph, build_knowledge_subgraph,
)


# ══════════════════════════════════════════════════════════════════════════
#  _get_page
# ══════════════════════════════════════════════════════════════════════════


class TestGetPage:
    def test_returns_page_at_index(self):
        state = {"pages": ["alarm", "camera"], "current_page_index": 0}
        assert _get_page(state) == "alarm"

    def test_returns_second_page(self):
        state = {"pages": ["alarm", "camera"], "current_page_index": 1}
        assert _get_page(state) == "camera"

    def test_empty_pages(self):
        state = {"pages": [], "current_page_index": 0}
        assert _get_page(state) == ""

    def test_index_out_of_bounds(self):
        state = {"pages": ["alarm"], "current_page_index": 5}
        assert _get_page(state) == ""

    def test_no_pages_key(self):
        state = {"current_page_index": 0}
        assert _get_page(state) == ""

    def test_no_index_key(self):
        state = {"pages": ["alarm"]}
        assert _get_page(state) == "alarm"


# ══════════════════════════════════════════════════════════════════════════
#  exec_entry / exec_exit
# ══════════════════════════════════════════════════════════════════════════


class TestExecNodes:
    def test_exec_entry(self):
        result = exec_entry({})
        assert result["current_phase"] == "Execute & Debug"

    def test_exec_exit(self):
        result = exec_exit({})
        assert "Execute & Debug" in result["completed_phases"]


# ══════════════════════════════════════════════════════════════════════════
#  report_entry / report_exit
# ══════════════════════════════════════════════════════════════════════════


class TestReportNodes:
    def test_report_entry(self):
        result = report_entry({})
        assert result["current_phase"] == "Report"

    def test_report_exit(self):
        result = report_exit({})
        assert "Report" in result["completed_phases"]

    def test_report_skills_defined(self):
        assert "reporting/report-generator" in REPORT_SKILLS
        assert "reporting/excel-exporter" in REPORT_SKILLS


# ══════════════════════════════════════════════════════════════════════════
#  knowledge_entry / knowledge_exit
# ══════════════════════════════════════════════════════════════════════════


class TestKnowledgeNodes:
    def test_knowledge_entry(self):
        result = knowledge_entry({})
        assert result["current_phase"] == "Knowledge"

    def test_knowledge_exit(self):
        result = knowledge_exit({})
        assert "Knowledge" in result["completed_phases"]

    def test_knowledge_act_calls_run_skill(self, monkeypatch):
        mock_run = MagicMock(return_value=MagicMock(
            content="Knowledge extracted",
            token_usage={"input": 100, "output": 50},
            finish_reason="stop",
        ))
        monkeypatch.setattr("alice_engine.workflow.execution_graph.run_skill", mock_run)
        state = {"module": "equipment", "pages": ["alarm"],
                 "current_page_index": 0, "provider": "fake", "agent_outputs": {}}
        result = knowledge_act(state)
        assert result["current_skill"] == "knowledge/knowledge-manager"


# ══════════════════════════════════════════════════════════════════════════
#  exec_gate
# ══════════════════════════════════════════════════════════════════════════


class TestExecGate:
    def test_returns_gate_results(self):
        state = {"module": "equipment"}
        result = exec_gate(state)
        assert "gate_results" in result
        assert len(result["gate_results"]) == 1
        assert result["gate_results"][0]["phase"] == "Execute & Debug"


# ══════════════════════════════════════════════════════════════════════════
#  SubGraph builders
# ══════════════════════════════════════════════════════════════════════════


class TestSubGraphBuilders:
    def test_build_execution_subgraph_returns_graph(self):
        graph = build_execution_subgraph()
        assert graph is not None

    def test_build_report_subgraph_returns_graph(self):
        graph = build_report_subgraph()
        assert graph is not None

    def test_build_knowledge_subgraph_returns_graph(self):
        graph = build_knowledge_subgraph()
        assert graph is not None


# ══════════════════════════════════════════════════════════════════════════
#  _single_skill_act (via report_act)
# ══════════════════════════════════════════════════════════════════════════


class TestSingleSkillAct:
    def test_report_act_calls_run_skill(self, monkeypatch):
        mock_run = MagicMock(return_value=MagicMock(
            content="Report content",
            token_usage={"input": 100, "output": 50},
            finish_reason="stop",
        ))
        monkeypatch.setattr("alice_engine.workflow.execution_graph.run_skill", mock_run)

        state = {"module": "equipment", "pages": ["alarm"],
                 "current_page_index": 0, "provider": "fake", "agent_outputs": {}}
        result = report_act(state)
        assert result["current_skill"] == "reporting/report-generator"

    def test_report_act2_calls_excel_exporter(self, monkeypatch):
        mock_run = MagicMock(return_value=MagicMock(
            content="Excel exported",
            token_usage={"input": 50, "output": 20},
            finish_reason="stop",
        ))
        monkeypatch.setattr("alice_engine.workflow.execution_graph.run_skill", mock_run)

        state = {"module": "equipment", "pages": ["alarm"],
                 "current_page_index": 0, "provider": "fake", "agent_outputs": {}}
        result = report_act2(state)
        assert result["current_skill"] == "reporting/excel-exporter"

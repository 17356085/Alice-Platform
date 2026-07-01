"""Tests for platform/artifact_lineage.py — artifact DAG tracking.

Tests: PHASE_ARTIFACTS, record_artifact, get_lineage.
Pure in-memory — no external dependencies.
"""
import pytest

from aitest.platform.artifact_lineage import (
    PHASE_ARTIFACTS, record_artifact, get_lineage, _lineage,
)


# ══════════════════════════════════════════════════════════════════════════
#  PHASE_ARTIFACTS
# ══════════════════════════════════════════════════════════════════════════


class TestPhaseArtifacts:
    def test_all_agents_defined(self):
        for agent in ["project-agent", "requirement-agent", "test-design-agent",
                       "automation-agent", "execution-agent", "report-agent",
                       "knowledge-agent"]:
            assert agent in PHASE_ARTIFACTS

    def test_each_has_produces(self):
        for agent, info in PHASE_ARTIFACTS.items():
            assert "produces" in info
            assert isinstance(info["produces"], list)
            assert len(info["produces"]) > 0

    def test_each_has_depends_on(self):
        for agent, info in PHASE_ARTIFACTS.items():
            assert "depends_on" in info
            assert isinstance(info["depends_on"], list)


# ══════════════════════════════════════════════════════════════════════════
#  record_artifact
# ══════════════════════════════════════════════════════════════════════════


class TestRecordArtifact:
    def test_records_to_lineage(self):
        _lineage.clear()
        record_artifact("proj", "equip", "alarm", "PAGE_CONTEXT.md",
                        generated_by="test-design-agent",
                        depends_on=["REQUIREMENT_ANALYSIS.md"])
        key = "proj/equip/alarm"
        assert key in _lineage
        assert len(_lineage[key]) == 1
        assert _lineage[key][0]["artifact"] == "PAGE_CONTEXT.md"

    def test_multiple_records_accumulate(self):
        _lineage.clear()
        record_artifact("p", "m", "pg", "A.md", generated_by="agent-a")
        record_artifact("p", "m", "pg", "B.md", generated_by="agent-b")
        assert len(_lineage["p/m/pg"]) == 2

    def test_default_depends_on_empty(self):
        _lineage.clear()
        record_artifact("p", "m", "pg", "X.md", generated_by="agent")
        assert _lineage["p/m/pg"][0]["depends_on"] == []


# ══════════════════════════════════════════════════════════════════════════
#  get_lineage
# ══════════════════════════════════════════════════════════════════════════


class TestGetLineage:
    def test_returns_nodes_and_edges(self):
        _lineage.clear()
        record_artifact("proj", "equip", "alarm", "PAGE_CONTEXT.md",
                        generated_by="test-design-agent",
                        depends_on=["REQUIREMENT_ANALYSIS.md"])
        dag = get_lineage("proj", "equip", "alarm")
        assert "nodes" in dag
        assert "edges" in dag
        assert len(dag["nodes"]) >= 1

    def test_empty_lineage_has_declared_artifacts(self):
        _lineage.clear()
        dag = get_lineage("proj", "equip", "nonexistent-page")
        # Even without recorded artifacts, declared phase artifacts should appear
        assert len(dag["nodes"]) > 0

    def test_recorded_artifacts_marked_generated(self):
        _lineage.clear()
        record_artifact("p", "m", "pg", "TEST.md", generated_by="agent")
        dag = get_lineage("p", "m", "pg")
        generated = [n for n in dag["nodes"] if n["status"] == "generated"]
        assert len(generated) >= 1

    def test_dag_has_project_module_page(self):
        _lineage.clear()
        dag = get_lineage("my-project", "equipment", "alarm")
        assert dag["project"] == "my-project"
        assert dag["module"] == "equipment"
        assert dag["page"] == "alarm"

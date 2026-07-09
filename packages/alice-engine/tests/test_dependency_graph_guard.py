"""Dependency graph guardrails for Phase 8."""

from __future__ import annotations

import json
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[3]
BASELINE_PATH = REPO_ROOT / "docs" / "architecture" / "dependency_graph_baseline.json"
sys.path.insert(0, str(REPO_ROOT))

from tools import check_dependency_graph  # noqa: E402


def test_dependency_graph_matches_reviewed_baseline():
    report = check_dependency_graph.build_dependency_report()
    baseline = check_dependency_graph.load_baseline(BASELINE_PATH)

    errors = check_dependency_graph.compare_with_baseline(report, baseline)

    assert errors == []


def test_dependency_graph_baseline_has_expected_shape():
    baseline = json.loads(BASELINE_PATH.read_text(encoding="utf-8"))

    assert baseline["summary"]["node_count"] >= 1
    assert baseline["summary"]["edge_count"] >= 1
    assert baseline["summary"]["scc_count"] >= 0
    assert isinstance(baseline["sccs"], list)
    assert baseline["boundary_violations"] == []

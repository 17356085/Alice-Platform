"""
Artifact Lineage — tracks how artifacts relate to each other.

Each artifact knows: who generated it, what it depends on, version, timestamp.
Together with Timeline Replay, this answers "why" something happened.

DAG:
  MODULE_CONTEXT → REQUIREMENT → PAGE_CONTEXT → TEST_CASES
    → TECH_ANALYSIS → AUTO_STRATEGY → PageObject/test → evidence → report

Usage:
    from aitest.platform.artifact_lineage import get_lineage, record_artifact

    record_artifact("equipment", "alarm-config", "PAGE_CONTEXT.md",
                    generated_by="test-design-agent",
                    depends_on=["REQUIREMENT_ANALYSIS.md"])

    dag = get_lineage("web-automation", "equipment", "alarm-config")
"""

import json
import threading
from pathlib import Path
from datetime import datetime, timezone
from typing import Optional

# ── SOP Phase → Expected Artifacts (declarative) ─────────────────────

PHASE_ARTIFACTS = {
    "project-agent": {
        "produces": ["MODULE_CONTEXT.md", "PROJECT_CONTEXT.md"],
        "depends_on": [],
    },
    "requirement-agent": {
        "produces": ["REQUIREMENT_ANALYSIS.md"],
        "depends_on": ["MODULE_CONTEXT.md"],
    },
    "test-design-agent": {
        "produces": ["PAGE_CONTEXT.md", "RISK_MODEL.md", "TEST_CASES.md", "BUSINESS_SCENARIOS.md"],
        "depends_on": ["REQUIREMENT_ANALYSIS.md", "MODULE_CONTEXT.md"],
    },
    "automation-agent": {
        "produces": ["TECH_ANALYSIS.md", "AUTO_STRATEGY.md", "PageObject.py", "test_scripts.py"],
        "depends_on": ["PAGE_CONTEXT.md", "TEST_CASES.md", "RISK_MODEL.md"],
    },
    "execution-agent": {
        "produces": ["evidence/"],
        "depends_on": ["PageObject.py", "test_scripts.py", "AUTO_STRATEGY.md"],
    },
    "bug-analysis-agent": {
        "produces": ["BUG_ANALYSIS.md"],
        "depends_on": ["evidence/", "TEST_CASES.md"],
    },
    "report-agent": {
        "produces": ["report/", "TEST_REPORT.xlsx"],
        "depends_on": ["evidence/", "BUG_ANALYSIS.md", "TEST_CASES.md"],
    },
    "knowledge-agent": {
        "produces": ["KNOWLEDGE_UPDATE"],
        "depends_on": ["all"],
    },
}

# ── Lineage record ─────────────────────────────────────────────────────

_lineage: dict[str, list[dict]] = {}  # key = project/module/page
_lock = threading.Lock()


def record_artifact(
    project: str,
    module: str,
    page: str,
    artifact_name: str,
    generated_by: str,
    depends_on: list[str] = None,
    version: str = "1",
):
    """Record an artifact generation event. Called by AgentLoop after each Phase."""
    key = f"{project}/{module}/{page}"
    entry = {
        "artifact": artifact_name,
        "generated_by": generated_by,
        "depends_on": depends_on or [],
        "version": version,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }
    with _lock:
        if key not in _lineage:
            _lineage[key] = []
        _lineage[key].append(entry)


def get_lineage(project: str, module: str, page: str = "") -> dict:
    """Get the artifact lineage DAG for a project/module/page.

    Returns nodes and edges suitable for frontend visualization.
    """
    key = f"{project}/{module}/{page}" if page else f"{project}/{module}"

    # Build from recorded lineage + declarative phase artifacts
    nodes = []
    edges = []
    seen = set()

    def add_node(name: str, agent: str = "", status: str = "defined"):
        if name not in seen:
            nodes.append({"id": name, "label": name.replace(".md", "").replace(".py", ""),
                          "agent": agent, "status": status})
            seen.add(name)

    def add_edge(source: str, target: str):
        edges.append({"source": source, "target": target})

    # First pass: recorded artifacts
    with _lock:
        records = _lineage.get(key, [])

    for r in records:
        add_node(r["artifact"], r["generated_by"], "generated")
        for dep in r.get("depends_on", []):
            add_node(dep, "", "exists")
            add_edge(dep, r["artifact"])

    # Second pass: fill in declared artifacts that haven't been generated yet
    for agent, info in PHASE_ARTIFACTS.items():
        for artifact in info["produces"]:
            if artifact not in seen:
                add_node(artifact, agent, "pending")
            for dep in info.get("depends_on", []):
                if dep not in seen:
                    add_node(dep, "", "defined")
                add_edge(dep, artifact)

    return {
        "project": project,
        "module": module,
        "page": page or "(all)",
        "nodes": nodes,
        "edges": edges,
        "total_artifacts": len(nodes),
        "generated": sum(1 for n in nodes if n["status"] == "generated"),
        "pending": sum(1 for n in nodes if n["status"] == "pending"),
    }

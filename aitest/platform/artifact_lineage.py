"""
Artifact Lineage — tracks how artifacts relate to each other. v3.0
PostgreSQL persistence via docker exec psql.
"""

import json
from datetime import datetime, timezone
from aitest.infra.database import pg_exec, pg_query

PHASE_ARTIFACTS = {
    "project-agent": {"produces": ["MODULE_CONTEXT.md", "PROJECT_CONTEXT.md"], "depends_on": []},
    "requirement-agent": {"produces": ["REQUIREMENT_ANALYSIS.md"], "depends_on": ["MODULE_CONTEXT.md"]},
    "test-design-agent": {"produces": ["PAGE_CONTEXT.md", "RISK_MODEL.md", "TEST_CASES.md", "BUSINESS_SCENARIOS.md"], "depends_on": ["REQUIREMENT_ANALYSIS.md", "MODULE_CONTEXT.md"]},
    "automation-agent": {"produces": ["TECH_ANALYSIS.md", "AUTO_STRATEGY.md", "PageObject.py", "test_scripts.py"], "depends_on": ["PAGE_CONTEXT.md", "TEST_CASES.md", "RISK_MODEL.md"]},
    "execution-agent": {"produces": ["evidence/"], "depends_on": ["PageObject.py", "test_scripts.py", "AUTO_STRATEGY.md"]},
    "bug-analysis-agent": {"produces": ["BUG_ANALYSIS.md"], "depends_on": ["evidence/", "TEST_CASES.md"]},
    "report-agent": {"produces": ["report/", "TEST_REPORT.xlsx"], "depends_on": ["evidence/", "BUG_ANALYSIS.md", "TEST_CASES.md"]},
    "knowledge-agent": {"produces": ["KNOWLEDGE_UPDATE"], "depends_on": ["all"]},
}

def _escape(val):
    if val is None: return "NULL"
    return "'" + str(val).replace("'", "''") + "'"

def _escape_json(val):
    if val is None: return "'[]'"
    return "'" + json.dumps(val, ensure_ascii=False).replace("'", "''") + "'"

def record_artifact(project: str, module: str, page: str, artifact_name: str, generated_by: str, depends_on: list[str] = None, version: str = "1", run_id: str = ""):
    now = datetime.now(timezone.utc).isoformat()
    pg_exec(f"INSERT INTO artifact_lineage (project, module, page, artifact_name, generated_by, depends_on, version, run_id, timestamp) VALUES ({_escape(project)}, {_escape(module)}, {_escape(page)}, {_escape(artifact_name)}, {_escape(generated_by)}, {_escape_json(depends_on or [])}, {_escape(version)}, {_escape(run_id or '')}, {_escape(now)})")

def get_lineage(project: str, module: str, page: str = "") -> dict:
    where = [f"project={_escape(project)}", f"module={_escape(module)}"]
    if page: where.append(f"page={_escape(page)}")
    records = pg_query(f"SELECT * FROM artifact_lineage WHERE {' AND '.join(where)} ORDER BY timestamp")
    nodes, edges, seen = [], [], set()
    def add_node(name, agent="", status="defined", run_id=""):
        if name not in seen:
            nodes.append({"id": name, "label": name.replace(".md","").replace(".py",""), "agent": agent, "status": status, "run_id": run_id})
            seen.add(name)
    def add_edge(source, target):
        edges.append({"source": source, "target": target})
    for r in records:
        add_node(r["artifact_name"], r["generated_by"], "generated", r.get("run_id") or "")
        for dep in (r.get("depends_on") or []):
            add_node(dep, "", "exists")
            add_edge(dep, r["artifact_name"])
    for agent, info in PHASE_ARTIFACTS.items():
        for artifact in info["produces"]:
            if artifact not in seen: add_node(artifact, agent, "pending")
            for dep in info.get("depends_on", []):
                if dep not in seen: add_node(dep, "", "defined")
                add_edge(dep, artifact)
    return {"project": project, "module": module, "page": page or "(all)", "nodes": nodes, "edges": edges, "total_artifacts": len(nodes), "generated": sum(1 for n in nodes if n["status"]=="generated"), "pending": sum(1 for n in nodes if n["status"]=="pending")}

def get_lineage_by_run(run_id: str) -> list[dict]:
    return pg_query(f"SELECT * FROM artifact_lineage WHERE run_id={_escape(run_id)} ORDER BY timestamp")

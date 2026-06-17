"""
ReviewGraph — Architecture Review Agent orchestration (P1).

Meta-governance graph. Standalone — not embedded in Test SOP or Dev SOP.
Orchestrates review skills: context → review phases → synthesis → report → emit.

Usage:
  python -m aitest.graphs.review_graph --mode=full
  python -m aitest.graphs.review_graph --mode=quick
  python -m aitest.graphs.review_graph --mode=architecture
  python -m aitest.graphs.review_graph --mode=cost --trigger=CostAnomaly
"""
from __future__ import annotations

import json, time, uuid
from pathlib import Path
from dataclasses import dataclass, field
from typing import Optional
from langgraph.graph import StateGraph, END

WORKSTUDY = Path(__file__).resolve().parent.parent.parent
GOVERNANCE = WORKSTUDY / "governance"
OUTPUT_DIR = GOVERNANCE / "artifacts" / "reviews" / "system"

# ═══════════════════════════════════════════════════════════════
# Review phase definitions
# ═══════════════════════════════════════════════════════════════

REVIEW_PHASES = [
    # Strategic layer
    {"key": "architecture",     "skill": "review/architecture-assessment",     "label": "Architecture Review"},
    {"key": "tech_debt",        "skill": "review/tech-debt-inventory",         "label": "Tech Debt Inventory"},
    {"key": "cohesion",         "skill": "review/component-cohesion",           "label": "Component Cohesion Review"},
    # Governance layer
    {"key": "governance",       "skill": "review/governance-coverage",          "label": "Governance Coverage Review"},
    {"key": "quality_trend",    "skill": "review/quality-regression-analysis",  "label": "Quality Trend Analysis"},
    {"key": "sop_effectiveness","skill": "review/sop-effectiveness",            "label": "SOP Effectiveness Review"},
    # Cost & Efficiency layer
    {"key": "token",            "skill": "review/token-efficiency",             "label": "Token Efficiency Review"},
    {"key": "model_selection",  "skill": "review/model-selection",              "label": "Model Selection Review"},
    {"key": "prompt",           "skill": "review/prompt-engineering",           "label": "Prompt Engineering Review"},
    {"key": "prompt_optimize",  "skill": "automation/prompt-engineering-expert","label": "Prompt Engineering Optimize"},
    # Production layer
    {"key": "production",       "skill": "review/production-readiness",         "label": "Production Readiness Review"},
    {"key": "observability",    "skill": "review/observability-gap",             "label": "Observability Gap Assessment"},
    {"key": "security",         "skill": "review/security-posture",              "label": "Security Posture Review"},
    # Meta layer
    {"key": "skill_health",     "skill": "review/skill-health",                  "label": "Skill Health Review"},
    {"key": "agent_health",     "skill": "review/agent-health",                  "label": "Agent Health Review"},
    {"key": "memory_quality",   "skill": "review/memory-quality",                "label": "Memory Quality Review"},
]

MODE_PHASE_MAP = {
    "full":         ["architecture", "tech_debt", "cohesion", "governance", "token", "prompt", "prompt_optimize", "production", "security"],
    "quick":        ["architecture", "governance"],
    "architecture": ["architecture"],
    "cost":         ["token", "model_selection"],
    "governance":   ["governance", "sop_effectiveness"],
    "quality":      ["prompt", "prompt_optimize", "quality_trend"],
    "optimize":     ["prompt", "prompt_optimize"],
    "production":   ["production", "observability", "security"],
    "debt":         ["tech_debt", "cohesion"],
    "health":       ["skill_health", "agent_health", "memory_quality"],
    "comprehensive": [p["key"] for p in REVIEW_PHASES],  # All 15 phases
}

EVENT_TRIGGER_MAP = {
    "StateDrift":       ["architecture"],
    "SOPViolation":     ["governance"],
    "CostAnomaly":      ["token"],
    "EvalRegressed":    ["architecture", "prompt"],
    "PromptChanged":    ["prompt", "prompt_optimize"],
    "AuditCompleted":   ["architecture"],
}

PHASE_TO_SKILL = {p["key"]: p["skill"] for p in REVIEW_PHASES}


# ═══════════════════════════════════════════════════════════════
# Context collection helpers
# ═══════════════════════════════════════════════════════════════

def _collect_review_context(state: dict) -> str:
    """Gather audit summaries, recent events, and KPI data for review context."""
    parts = []

    # Audit report list
    audit_dir = GOVERNANCE / "artifacts" / "audits"
    if audit_dir.exists():
        reports = sorted(audit_dir.glob("*.md"), key=lambda p: p.stat().st_mtime, reverse=True)[:5]
        parts.append("## Recent Audit Reports\n")
        for r in reports:
            parts.append(f"- {r.name} ({r.stat().st_mtime:.0f})")

    # SOP_STATUS summary
    sop_dir = GOVERNANCE / "artifacts" / "sop-status"
    if sop_dir.exists():
        parts.append("\n## Module SOP Status\n")
        for f in sorted(sop_dir.glob("SOP_STATUS_*.json")):
            try:
                data = json.loads(f.read_text(encoding="utf-8"))
                module = f.stem.replace("SOP_STATUS_", "")
                completed = len(data.get("completed_phases", [])) if isinstance(data, dict) else "?"
                parts.append(f"- {module}: {completed} phases completed")
            except Exception:
                pass

    # Trace stats
    trace_log = GOVERNANCE / ".traces" / "trace_log.jsonl"
    if trace_log.exists():
        lines = trace_log.read_text(encoding="utf-8").strip().split("\n")
        parts.append(f"\n## Trace Log\n- Total events: {len(lines)}")

    # Regression test coverage
    test_cases_yaml = GOVERNANCE / "tests" / "regression" / "test_cases.yaml"
    if test_cases_yaml.exists():
        import yaml
        try:
            with open(test_cases_yaml, "r", encoding="utf-8") as f:
                tc_data = yaml.safe_load(f)
            cases = tc_data.get("test_cases", []) if tc_data else []
            categories = set(c.get("tags", []) for c in cases if c.get("tags"))
            parts.append(f"\n## Regression Test Coverage\n- Total test cases: {len(cases)}")
            review_cases = [c for c in cases if "review" in str(c.get("tags", []))]
            parts.append(f"- Review skill cases: {len(review_cases)}")
        except Exception:
            pass

    # Workflow registry
    workflow_yaml = GOVERNANCE / "workflows" / "workflow-registry.yaml"
    if workflow_yaml.exists():
        import yaml
        try:
            with open(workflow_yaml, "r", encoding="utf-8") as f:
                wf_data = yaml.safe_load(f)
            workflows = wf_data.get("workflows", []) if wf_data else []
            parts.append(f"\n## Workflow Registry\n- Total workflows: {len(workflows)}")
            review_wf = [w for w in workflows if "review" in str(w.get("id", "")).lower()]
            parts.append(f"- Review workflows: {len(review_wf)}")
        except Exception:
            pass

    return "\n".join(parts)


# ═══════════════════════════════════════════════════════════════
# Graph nodes
# ═══════════════════════════════════════════════════════════════

def entry_node(state: dict) -> dict:
    """Entry: collect context, decide scope."""
    mode = state.get("mode", "full")
    trigger = state.get("trigger", "manual")

    # If event-triggered, determine phases from event type
    if trigger != "manual" and trigger in EVENT_TRIGGER_MAP:
        phases = EVENT_TRIGGER_MAP[trigger]
    else:
        phases = MODE_PHASE_MAP.get(mode, MODE_PHASE_MAP["full"])

    context_text = _collect_review_context(state)

    run_id = f"review-{mode}-{uuid.uuid4().hex[:8]}"

    return {
        **state,
        "run_id": run_id,
        "mode": mode,
        "trigger": trigger,
        "phases": phases,
        "phase_index": 0,
        "context_text": context_text,
        "review_results": {},
        "status": "running",
        "started_at": time.time(),
    }


def run_review_phase(state: dict) -> dict:
    """Run current review phase's skill. Uses DiffFirstReviewAdapter to optimize token usage."""
    idx = state.get("phase_index", 0)
    phases = state.get("phases", [])
    if idx >= len(phases):
        return {**state, "status": "all_phases_done"}

    phase_key = phases[idx]
    skill_id = PHASE_TO_SKILL.get(phase_key)
    if not skill_id:
        return {**state, "phase_index": idx + 1}

    from aitest.agents.agent_runner import run_skill
    from aitest.governance.diff_first_review_adapter import DiffFirstReviewAdapter

    # NEW: Use DiffFirstReviewAdapter to reduce token usage
    adapter = DiffFirstReviewAdapter(context_lines=3, full_file_threshold=100)
    review_input = adapter.prepare_review_input(
        ref1="HEAD~1",
        ref2="HEAD",
        fallback_to_full=True,
    )

    # Build review prompt with code diff priority
    user_input = adapter.build_review_prompt(
        skill_name=skill_id,
        review_input=review_input,
        context_text=state.get("context_text", ""),
        trigger=state.get("trigger", "manual"),
    )

    # Append prior review context
    user_input += f"""

## Trigger
{state.get("trigger", "manual")}

## Previously Completed Reviews
{json.dumps({k: v[:200] if isinstance(v, str) else v for k, v in state.get("review_results", {}).items()}, indent=2)}

Produce a complete review report following the standard REVIEW_REPORT.md template."""

    try:
        resp = run_skill(skill_id, user_input, provider="claude", max_tokens=8192)
        result = resp.content
    except Exception as e:
        result = f"[SKILL ERROR] {skill_id}: {str(e)}"

    results = dict(state.get("review_results", {}))
    results[phase_key] = result

    return {
        **state,
        "review_results": results,
        "phase_index": idx + 1,
        "last_review_strategy": review_input.get("strategy"),
    }


def synthesis_node(state: dict) -> dict:
    """Cross-review synthesis: combine all review findings into a unified report."""
    results = state.get("review_results", {})

    # Extract scores and findings from each review
    synthesis_parts = [
        "# Cross-Review Synthesis Report — AITest Platform\n",
        f"---",
        f"report_id: REVIEW-SYNTH-{time.strftime('%Y%m%d')}-{uuid.uuid4().hex[:8]}",
        f"mode: {state.get('mode', 'full')}",
        f"trigger: {state.get('trigger', 'manual')}",
        f"phases_executed: {', '.join(state.get('phases', []))}",
        f"created: {time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime())}",
        f"---\n",
    ]

    # Summary per phase
    synthesis_parts.append("## Phase Results\n")
    for phase_key in state.get("phases", []):
        content = results.get(phase_key, "")
        if content:
            # Extract score if available
            score_match = None
            for line in content.split("\n"):
                if "Overall" in line and "Score" in line:
                    score_match = line.strip()
                    break
            status = score_match if score_match else "Report generated"
            synthesis_parts.append(f"- **{phase_key}**: {status}")
            synthesis_parts.append(f"  - Output: {len(content)} chars")
        else:
            synthesis_parts.append(f"- **{phase_key}**: SKIPPED")

    # Cross-dimension patterns
    synthesis_parts.append("\n## Cross-Dimension Patterns\n")
    synthesis_parts.append("Automated cross-review analysis of findings across all executed review dimensions.\n")

    # Detect shared concerns across reviews
    all_content = " ".join(results.values())
    patterns = []
    if "tank" in all_content.lower() and "UI" in all_content:
        patterns.append("- **tank UI boundary** — detected across architecture, governance, and production reviews")
    if "knowledge agent" in all_content.lower() or "knowledge-agent" in all_content.lower():
        patterns.append("- **Knowledge Agent gaps** — governance coverage + event consumption chain")
    if "version" in all_content.lower() and "rollback" in all_content.lower():
        patterns.append("- **Skill version management** — prompt engineering + production readiness")
    if "agent runner" in all_content.lower() and "2046" in all_content:
        patterns.append("- **Agent Runner overload** — architecture + production readiness")

    if patterns:
        synthesis_parts.extend(patterns)
    else:
        synthesis_parts.append("No cross-dimensional patterns detected with high confidence.")

    # Aggregate action items
    synthesis_parts.append("\n## Aggregated Action Items\n")
    synthesis_parts.append("| Priority | Source | Action |")
    synthesis_parts.append("|----------|--------|--------|")

    for phase_key, content in results.items():
        if not content or "SKILL ERROR" in content:
            continue
        # Extract P0 items
        for line in content.split("\n"):
            if line.startswith("| P0") or "| P0 |" in line:
                synthesis_parts.append(f"| P0 | {phase_key} | {line.strip()} |")

    synthesis_text = "\n".join(synthesis_parts)
    return {**state, "synthesis_report": synthesis_text}


def report_node(state: dict) -> dict:
    """Generate and persist final review report."""
    synthesis = state.get("synthesis_report", "")
    results = state.get("review_results", {})

    # Save synthesis report
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    report_path = OUTPUT_DIR / f"SYNTHESIS_REVIEW-{time.strftime('%Y%m%d')}.md"
    report_path.write_text(synthesis, encoding="utf-8")

    # Save individual phase reports
    saved_paths = {}
    for phase_key, content in results.items():
        if content and "SKILL ERROR" not in content:
            skill_name = PHASE_TO_SKILL.get(phase_key, phase_key).replace("review/", "").upper()
            path = OUTPUT_DIR / f"{skill_name}_REVIEW-{time.strftime('%Y%m%d')}.md"
            path.write_text(content, encoding="utf-8")
            saved_paths[phase_key] = str(path)

    return {
        **state,
        "report_path": str(report_path),
        "saved_paths": saved_paths,
        "status": "completed",
    }


def emit_events_node(state: dict) -> dict:
    """Emit ReviewCompleted and domain-specific events to Event Bus."""
    try:
        from aitest.governance.event_bus import emit

        # Emit ReviewCompleted
        results = state.get("review_results", {})
        critical_count = sum(
            1 for c in results.values()
            if isinstance(c, str) and ("Critical" in c or "Blocker" in c)
        )

        emit("ReviewCompleted",
             review_type=state.get("mode", "full"),
             module=state.get("module", "system"),
             overall_score=0,  # Would need parsing from synthesis
             critical_count=critical_count,
             warning_count=0,
             report_path=state.get("report_path", ""))

        # Emit domain-specific events if findings warrant
        if critical_count > 0:
            emit("ArchitectureRiskDetected",
                 module=state.get("module", "system"),
                 risk_type="cross-review",
                 severity="critical",
                 description=f"Cross-review synthesis found {critical_count} critical issues",
                 recommendation="Review synthesis report for prioritized action items")

    except Exception as e:
        pass  # Non-fatal: event emission failure shouldn't block review

    return {**state, "events_emitted": True}


def exit_node(state: dict) -> dict:
    """Exit: finalize state."""
    return {
        **state,
        "status": state.get("status", "completed"),
        "completed_at": time.time(),
    }


# ═══════════════════════════════════════════════════════════════
# Route: should run next phase or move to synthesis?
# ═══════════════════════════════════════════════════════════════

def route_after_phase(state: dict) -> str:
    phases = state.get("phases", [])
    idx = state.get("phase_index", 0)
    if idx < len(phases):
        return "run_review_phase"
    return "synthesis"


# ═══════════════════════════════════════════════════════════════
# Graph builder
# ═══════════════════════════════════════════════════════════════

def build_review_graph() -> StateGraph:
    builder = StateGraph(dict)

    builder.add_node("entry", entry_node)
    builder.add_node("run_review_phase", run_review_phase)
    builder.add_node("synthesis", synthesis_node)
    builder.add_node("report", report_node)
    builder.add_node("emit_events", emit_events_node)
    builder.add_node("exit", exit_node)

    builder.set_entry_point("entry")

    # Entry → first review phase
    builder.add_edge("entry", "run_review_phase")

    # Review phase → next phase OR synthesis
    builder.add_conditional_edges(
        "run_review_phase",
        route_after_phase,
        {"run_review_phase": "run_review_phase", "synthesis": "synthesis"}
    )

    # Synthesis → report → emit → exit
    builder.add_edge("synthesis", "report")
    builder.add_edge("report", "emit_events")
    builder.add_edge("emit_events", "exit")
    builder.add_edge("exit", END)

    return builder


# ═══════════════════════════════════════════════════════════════
# CLI / Programmatic entry
# ═══════════════════════════════════════════════════════════════

def run_review(mode: str = "full", trigger: str = "manual", module: str = "system") -> dict:
    """Run a review orchestration."""
    graph = build_review_graph().compile()

    initial_state = {
        "mode": mode,
        "trigger": trigger,
        "module": module,
        "phases": [],
        "phase_index": 0,
        "review_results": {},
        "context_text": "",
    }

    final_state = graph.invoke(initial_state)
    return final_state


if __name__ == "__main__":
    import sys
    mode = sys.argv[1] if len(sys.argv) > 1 else "full"
    trigger = sys.argv[2] if len(sys.argv) > 2 else "manual"

    print(f"Review Graph: mode={mode}, trigger={trigger}")
    result = run_review(mode=mode, trigger=trigger)
    print(f"\nStatus: {result.get('status')}")
    print(f"Report: {result.get('report_path', 'N/A')}")
    print(f"Phases completed: {list(result.get('review_results', {}).keys())}")

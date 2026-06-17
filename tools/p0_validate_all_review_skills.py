"""
P0 Validation: Run remaining 4 review skills against AITest Platform.
Saves full reports to governance/artifacts/reviews/system/.
"""
import sys, os
sys.path.insert(0, "d:/Desktop/WorkStudy")

from pathlib import Path
from aitest.agent_runner import run_skill

WORKSTUDY = Path("d:/Desktop/WorkStudy")
TRACE_LOG = WORKSTUDY / "governance/.traces/trace_log.jsonl"
OUTPUT_DIR = WORKSTUDY / "governance/artifacts/reviews/system"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

def ok(msg): print(f"[OK] {msg}")
def info(msg): print(f"[--] {msg}")

def sample_traces(n=20):
    lines = []
    with open(TRACE_LOG, "r", encoding="utf-8") as f:
        for line in f:
            lines.append(line)
    return "".join(lines[-n:])[:3000]

def sample_kpi():
    kpi_dir = WORKSTUDY / "governance/kpi/timeseries"
    lines = []
    for f in sorted(kpi_dir.glob("cost-*.jsonl"))[:1]:
        with open(f, "r", encoding="utf-8") as fp:
            for line in fp:
                lines.append(line)
    return "".join(lines[-10:])[:2000]

def run_and_save(skill_id, user_input, out_name):
    info(f"Running {skill_id}...")
    resp = run_skill(skill_id, user_input, provider="claude", max_tokens=8192)
    out_path = OUTPUT_DIR / out_name
    out_path.write_text(resp.content, encoding="utf-8")
    # Count findings
    n_critical = resp.content.count("### Critical") + resp.content.count("## Critical")
    n_findings = resp.content.count("| C0") + resp.content.count("| W0") + resp.content.count("| B0")
    ok(f"{skill_id}: {resp.token_usage.get('output',0)} output tokens, model={resp.model}")
    ok(f"  Saved: {out_path}")
    return resp

TRACE_SAMPLE = sample_traces(20)
KPI_SAMPLE = sample_kpi()

# ============================================================
# Skill 2: token-efficiency
# ============================================================
info("=== Skill 2/5: review/token-efficiency ===")
run_and_save("review/token-efficiency", f"""分析 AITest Platform 的 Token 使用效率。

## Trace Log (recent 20 entries)
```
{TRACE_SAMPLE}
```

## KPI Cost Data
```
{KPI_SAMPLE}
```

## Context
- 17 Agents, 56 Skills
- Current provider: deepseek-v4-flash. Alternatives: Claude Opus/Sonnet/Haiku
- Known: some skill prompts >3000 chars, context injection growing over time

Evaluate token efficiency. Output optimization recommendations with estimated savings. Use English for all headings and content.""",
"TOKEN_REVIEW-20260616.md")

# ============================================================
# Skill 3: governance-coverage
# ============================================================
info("=== Skill 3/5: review/governance-coverage ===")
run_and_save("review/governance-coverage", """Evaluate governance coverage completeness for AITest Platform.

## Agents (17)
Test line (8): project-agent, requirement-agent, test-design-agent, automation-agent, execution-agent, bug-analysis-agent, report-agent, knowledge-agent
Dev line (9): pm-agent, req-agent, arch-agent, design-agent, frontend-agent, backend-agent, review-agent, dev-test-agent, debug-agent, build-agent

## Skills (56)
Test (24): project(3), requirements(2), test-design(6), automation(6), execution(2), diagnosis(3), knowledge(2), reporting(1)
Dev (32): plan(4), requirements-dev(4), architecture(4), component-design(4), frontend(5), backend(6), code-review(4), test-dev(3), debug(4), build(4)
New - review(5): architecture-assessment, token-efficiency, governance-coverage, prompt-engineering, production-readiness

## Auditor Coverage
- State Auditor: 7 checks (S/R/O/C/Q/T/Orphan), covers 10 modules
- SOP Auditor: 7 checks (P/S/G/H/B/L/X), trace-based
- Cost Auditor: 4 checks (Spike/Bloat/Trend/Model), all agents
- Regression Gate: 15 golden test cases, 10 skill categories

## Event Bus (19 event types)
Knowledge: AgentCompleted, BugClosed, CycleEnd, ContextUpdated
Governance: StateDrift, SOPViolation, PromptChanged, EvalRegressed, CostAnomaly, AuditCompleted
Quality: BusinessCoverageInsufficient, WorkflowCoverageInsufficient, TestDesignQualityRegressed
Review (new): ArchitectureRiskDetected, GovernanceGapDetected, TechnicalDebtDetected, ProductionRiskDetected, ReviewCompleted

## Module SOP Status
All 10 modules have SOP_STATUS JSON: equipment, lab, personnel, production, sales, system, system-management, system-role, tank, warehouse

## Known Gaps
- review skills not assigned to any agent
- Some skills lack regression test cases
- Some agents can bypass SOP Graph (direct AgentLoop invocation)

Output blind spot inventory and coverage completion roadmap. Use English.""",
"GOV_COVERAGE-20260616.md")

# ============================================================
# Skill 4: prompt-engineering
# ============================================================
info("=== Skill 4/5: review/prompt-engineering ===")
sample_skill_path = WORKSTUDY / "governance/skills-dev/review/architecture-assessment.md"
sample_skill_content = sample_skill_path.read_text(encoding="utf-8")[:3000]

run_and_save("review/prompt-engineering", f"""Review this Skill Prompt for quality.

## Skill: review/architecture-assessment v1.0
```
{sample_skill_content}
```

## Execution Data
- First run: 2026-06-16, Tokens: 4742 (input=2011, output=2731)
- Duration: 36.1s
- Output: 12 actionable findings (3 Critical, 5 Warning, 4 Observation)
- Output fully followed the template structure

## Version History
- v1.0 (2026-06-16): Initial version - 6-dimension architecture review

Evaluate across 6 dimensions: Structure, Clarity, Examples, Template Strictness, Efficiency, Version Evolution.
Give production-readiness verdict. Use English.""",
"PROMPT_REVIEW-20260616.md")

# ============================================================
# Skill 5: production-readiness
# ============================================================
info("=== Skill 5/5: review/production-readiness ===")
run_and_save("review/production-readiness", """Evaluate production readiness of AITest Platform.

## System Overview
- FastAPI + chat.html test workbench
- LangGraph SOP orchestration + SQLite checkpoint
- 17 Agents, 56 Skills
- LLM Provider: deepseek-v4-flash (primary), Claude models (alternative)
- Target system: https://aiwechatminidemo.cimc-digital.com/

## Recent Audit Summary
- State Audit: 10 modules have SOP_STATUS, no missing modules
- SOP Audit: baseline 62.4%, equipment unit + personnel exam 0 ERROR (fixed)
- Cost Audit: no Critical anomalies recently
- Governance Validation Sprint: 16 real issues found, 10 fixed

## Architecture Review Findings
- Architecture Score: 57/100 (Grade C)
- 3 Critical: tank custom UI boundary, SOP pattern asymmetry, high module extension cost
- 5 Warnings: state sync, implicit contracts, agent responsibility overlap, hardcoded fields, audit rule overlap

## Environment
- API Key: .env file, not in git
- Test URL: https://aiwechatminidemo.cimc-digital.com/
- Dev/Test environments mixed

## Known Issues
- Agent Runner 2046 lines, overloaded responsibilities
- chat.html low usage
- Skill version management lacks compatibility testing

Evaluate production readiness across 7 dimensions. Output Go/No-Go recommendation. Use English.""",
"PROD_READY-20260616.md")

info("=== P0 Validation Complete - all 5 review skills executed ===")

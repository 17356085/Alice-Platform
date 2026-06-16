# Governance Fixes — Round 2 (Deferred Items)

> Based on: GOVERNANCE_VALIDATION_SPRINT_2026-06-15.md — 4 items deferred from initial report
> Files changed: 3 | New checks: 3 | Test cases: 5→15

---

## Fix 1 (P1): O-Check — Agent Output Consistency

**File**: `aitest/state_auditor.py` — new `_run_o_check()` + `_check_output_consistency()` methods

**Problem**: Agent could claim "Phase complete" but produce garbage output (placeholders, TODO markers, repetitive filler, or content mismatched to phase). Q-Check only verifies line counts and keyword presence — doesn't detect placeholder spam or phase mismatch.

**Solution**: Three-tier consistency check:

1. **Placeholder detection**: Regex patterns for TODO/TBD/FIXME/待补充/待完善/to be determined. Flags if >30% of lines contain placeholders.

2. **Duplicate detection**: Same line repeated >40% of total lines → flagged as filler/spam.

3. **Phase-content matching**: Automation artifacts must contain tech terms (定位/xpath/css/selector); Test Design artifacts must contain test terms (用例/测试/场景/预期).

```python
PLACEHOLDER_PATTERNS = [
    (r"(?i)\b(TODO|TBD|FIXME|XXX|HACK)\b", "placeholder"),
    (r"(?i)(待补充|待完善|待填写|暂缺|暂无)", "CN-placeholder"),
    (r"(?i)(to be (determined|defined|decided|filled|written))", "TBD"),
]
DUPLICATE_LINE_RATIO_THRESHOLD = 0.4
```

**Verification**: Found 6 real issues in equipment module:
```
[o_check] RISK_MODEL.md (x4): test-design artifact lacks test terms
[o_check] TEST_DESIGN.md (x2): test-design artifact lacks test terms
```
These files have enough lines and pass Q-Check keyword markers, but their content doesn't match what a test-design phase agent should produce.

---

## Fix 2 (P1): C-Check Checkpoint Diagnostic

**File**: `aitest/state_auditor.py` — `_run_c_check()`

**Problem**: When SQLite checkpoint DB is missing or empty, C-Check silently returns with 0 findings. No indication that cross-source comparison couldn't run.

**Solution**: Added two diagnostic checks before the main comparison:

1. **DB missing**: If `checkpoints.sqlite` doesn't exist → info-level drift with suggestion to run full SOP Graph.

2. **DB empty**: If SOP_STATUS exists but checkpoint has no phase data → warning-level drift. Possible causes: dry-run mode, checkpoint write failure, or LangGraph checkpointer not compiled correctly.

```python
if not CHECKPOINT_DB.exists():
    self.drifts.append(DriftRecord(
        check_type="c_check", severity="info",
        description="SQLite checkpoint database not found...",
    ))
    return

if sop_status and not checkpoint_phases:
    self.drifts.append(DriftRecord(
        check_type="c_check", severity="warning",
        description="SOP_STATUS exists but checkpoint has no data...",
    ))
    return
```

**Verification**: Now correctly reports:
```
[c_check] warning: SOP_STATUS exists but SQLite checkpoint has no data
— possible dry-run or checkpoint write failure
```

---

## Fix 3 (P1): X-Check — Context Injection Completeness

**File**: `aitest/sop_auditor.py` — new `_run_x_check()` method

**Problem**: Context injector may fail silently. Skills that need context (PAGE_CONTEXT.md, RISK_MODEL.md via RAG) could run with zero injected context. This degrades output quality but was never detected.

**Solution**: Analyze trace `skill_execution` events. For skills in `CONTEXT_REQUIRED_SKILLS`, check `metadata.context_chars`:
- **>80% zero rate** with >=3 runs → warning: context injection broken
- **>30% zero rate** with >=3 runs → info: context injection unstable

```python
CONTEXT_REQUIRED_SKILLS = {
    "test-design/page-analysis", "test-design/risk-modeling",
    "test-design/testcase-design", "automation/tech-analysis",
    "automation/auto-strategy", "automation/code-generation",
    "execution/test-executor", "bug-analysis/bug-analyzer",
}
```

**Verification**: Found 2 real context injection gaps:
```
[x_check] warning: automation/tech-analysis: 100% context injection missing (4/4 runs)
[x_check] info: test-design/risk-modeling: 67% context injection unstable (4/6 runs)
```
`automation/tech-analysis` has context_chars=0 for every single run — the ContextInjector is completely failing for this skill. This explains poor tech analysis quality.

---

## Fix 4 (P2): Regression Test Case Expansion

**File**: `governance/tests/regression/test_cases.yaml`

**Problem**: Only 5 test cases covering 3 skill categories (test-design, automation, knowledge). 9% coverage of 56 skills.

**Solution**: Added 10 cases covering previously untested categories:

| # | Case ID | Skill | Category |
|---|---------|-------|----------|
| 6 | module-modeling-basic | requirements/module-modeling | requirements |
| 7 | requirement-analysis-basic | requirements/requirement-analysis | requirements |
| 8 | testcase-design-basic | test-design/testcase-design | test-design |
| 9 | page-object-generator-basic | automation/page-object-generator | automation |
| 10 | test-script-generator-basic | automation/test-script-generator | automation |
| 11 | code-consistency-basic | automation/code-consistency-checker | automation |
| 12 | allure-report-basic | execution/allure-report-analyzer | execution |
| 13 | bug-analysis-basic | diagnosis/bug-analysis | diagnosis |
| 14 | report-generator-basic | reporting/report-generator | reporting |
| 15 | knowledge-manager-basic | knowledge/knowledge-manager | knowledge |

All new cases use deterministic criteria (min_length + contains keywords) to avoid LLM non-determinism.

**Verification**: YAML parses correctly. 15 cases, version 0.3. Now covers 7/8 skill categories.

---

## Round 2 Summary

| Metric | Before | After |
|--------|--------|-------|
| State Drift Detection | ~55% (6 checks) | ~65% (7 checks) |
| SOP Compliance Checks | 6 dimensions | 7 dimensions |
| Agent output validated | Q-Check only (line/keyword) | Q+O-Check (placeholder/dup/phase-match) |
| C-Check diagnostic | silent on empty | reports missing/empty DB |
| Context injection monitored | no | yes, per-skill zero-rate tracking |
| Regression test cases | 5 (9% of 56 skills) | 15 (27% of 56 skills) |
| SOP categories covered | 3/8 | 7/8 |

### Real Issues Discovered by New Checks

| Check | Finding | Impact |
|-------|---------|--------|
| o_check | RISK_MODEL.md x4 lacks test terms | Agent output may be generic filler |
| o_check | TEST_DESIGN.md x2 lacks test terms | Test design content may be empty template |
| c_check | Checkpoint DB has no data | Cross-source consistency cannot be verified |
| x_check | tech-analysis 100% context missing | All tech analyses running blind |
| x_check | risk-modeling 67% context unstable | Risk models inconsistently informed |

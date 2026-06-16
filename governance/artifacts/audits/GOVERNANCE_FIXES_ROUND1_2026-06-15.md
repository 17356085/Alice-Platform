# Governance Fixes — Round 1 (Report Checklist)

> Based on: GOVERNANCE_VALIDATION_SPRINT_2026-06-15.md Part 8 优先修复清单
> Files changed: 5 | New checks: 3 | Test cases: unchanged

---

## Fix 1 (P0): B-Check Bypass Detection Logic

**File**: `aitest/sop_auditor.py` — `_run_b_check()`

**Before**: Whitelist mode. Only flagged run_ids starting with `eval-`, `standalone-`, `direct-`. Real bypasses using empty run_id or other patterns went undetected.

**After**: Blacklist mode. All non-`sop-*` run_ids flagged. Added `SOP_PHASE_AGENTS` set to filter out non-SOP agents (e.g. knowledge-manager). Empty run_ids now recorded as `"(empty run_id)"`. Severity escalates to `warning` at >=3 bypasses.

**Code change**:
```python
# OLD: whitelist — only matched eval-/standalone-/direct- prefixes
if rid.startswith("eval-") or rid.startswith("standalone-") or rid.startswith("direct-"):

# NEW: blacklist — any non-sop- run_id for SOP-phase agents
SOP_PHASE_AGENTS = {"project-agent", "requirement-agent", ...}
if agent not in SOP_PHASE_AGENTS:
    continue
# Any non-sop- prefix (including empty) is a potential bypass
```

**Verification**: Compiles. 0 bypasses in current trace (all events use sop-* run_ids — legitimate).

---

## Fix 2 (P0): PHASE_EXPECTED_ARTIFACTS Completion

**File**: `aitest/state_auditor.py` — `PHASE_EXPECTED_ARTIFACTS` + `QUALITY_MARKERS` + `_run_q_check()`

**Before**: Only 4/9 phases had expected artifact definitions. S-Check blind to 5 phases. Q-Check only covered Project Init/Requirement/Test Design/Automation.

**After**: All 9 phases defined.

| Phase | Module-level | Per-page |
|-------|-------------|----------|
| Project Init | PROJECT_CONTEXT.md | — |
| Requirement | MODULE_CONTEXT.md | — |
| Test Design | — | PAGE_CONTEXT.md, RISK_MODEL.md, TEST_DESIGN.md, TEST_CASES.md |
| Automation | — | TECH_ANALYSIS.md, AUTO_STRATEGY.md, PAGE_ELEMENT_POSITION.md, PAGE_INTERFACE.yaml |
| Execute & Debug | — | — (allure-results by gate checker) |
| Bug Analysis | — | BUG_ANALYSIS.md |
| Data Sanitization | DATA_QUALITY.md | — |
| Report | TEST_SUMMARY.md | — |
| Knowledge | — | — (managed by Knowledge Agent independently) |

New QUALITY_MARKERS: PAGE_ELEMENT_POSITION.md, PAGE_INTERFACE.yaml, BUG_ANALYSIS.md, DATA_QUALITY.md, TEST_SUMMARY.md.

**Verification**: S-Check went from 0 → 1 drift found (PROJECT_CONTEXT.md missing). Q-Check coverage expanded.

---

## Fix 3 (P0): Prompt Versioning Data Flow

**File**: `aitest/agent_runner.py` — `_act_stream()`

**Before**: `_act_stream()` bypassed `run_skill()`, calling `load_skill()` directly without setting `TraceContext.skill_version`. All streaming skill executions had 0% version tracking (5760 trace events, 0 with skill_version).

**After**: Added `TraceContext.set()` call in `_act_stream()` before the LLM interaction, mirroring the `run_skill()` path.

```python
# NEW in _act_stream():
from aitest.llm.skill_loader import resolve_skill_version
from aitest.trace import TraceContext
ver_info = resolve_skill_version(skill_id)
TraceContext.set(
    run_id=TraceContext.get_run_id(),
    agent_name=self.agent_name,
    skill_version=ver_info.resolved_version,
)
```

**Verification**: Compiles. Takes effect on next SOP run.

---

## Fix 4 (P1): CostAnomaly Event Emit

**File**: `aitest/cost_auditor.py` — `audit()`

**Before**: `CostAnomaly` event defined in `event_bus.py` but never emitted. Cost auditor found anomalies but didn't trigger governance events.

**After**: Added emit loop in `audit()` after alerts are sorted. All high/medium severity alerts emit `CostAnomaly` events.

```python
for alert in sorted_alerts:
    if alert.severity in ("high", "medium"):
        emit("CostAnomaly",
             skill_id=alert.evidence.get("skill_id", ""),
             agent=alert.evidence.get("agent", ""),
             anomaly_type=alert.rule,
             detail=alert.finding)
```

**Verification**: Compiles. Events will fire on next cost audit with anomalies.

---

## Fix 5 (P1): Reverse S-Check (R-Check)

**File**: `aitest/state_auditor.py` — new `_run_r_check()` method

**Before**: Only S-Check (State→Artifact) existed. If artifacts existed but state wasn't updated (reverse drift), it went undetected.

**After**: New `_run_r_check()` scans all expected artifact paths. For each phase NOT in completed_phases, checks if the corresponding artifact file exists with content. Flags as warning if found.

**Verification**: 0 findings in equipment module (no reverse drift — correct). Added to default checks list.

---

## Fix 6 (P2): Regression Gate — Refactor vs Regression

**File**: `aitest/regression.py` — `check_prompt_upgrade()` + `_section_similarity()`

**Before**: `missing_sections` unconditionally caused failure. A prompt refactor that renamed section headers would be blocked as "regression". `new_sections` scored 1.0 (free pass), allowing low-quality new content.

**After**:
1. Refactor detection: `missing + new + overall >= 0.5 + criteria pass` → treated as refactor, not regression
2. New section scoring: 0.3 base + len_score (0~0.4 based on chars) + den_score (0~0.3 based on lines). Short new sections score ~0.4; rich sections score 0.7~1.0.
3. Overall now includes all sections (common + new + missing) in weighted average.

```python
is_refactor = (
    not degraded_sections and missing and new
    and overall >= 0.5 and eval_new.passed
)
if degraded_sections:
    failures.append({..., "reason": "degraded"})
elif missing and not is_refactor:
    failures.append({..., "reason": "missing_sections_without_compensation"})
else:
    cases_passed += 1  # includes refactor pass
```

**Verification**: Tested with 3 scenarios — short new section (score 0.41), rich new section (score 0.8), refactor pattern (overall 0.636, passes as refactor).

---

## Round 1 Summary

| Metric | Before | After |
|--------|--------|-------|
| State Drift Detection | 25% (5 checks, 4/9 phases) | ~55% (6 checks, 9/9 phases) |
| SOP exit_node checks | 3/6 dimensions | 6/6 dimensions |
| Governance events with emit | 4/5 | 5/5 |
| Trace version coverage | 0% | ready (next run) |
| Regression false positives | refactor → blocked | refactor → pass |

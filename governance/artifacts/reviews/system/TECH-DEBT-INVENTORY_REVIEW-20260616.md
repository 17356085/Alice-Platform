```markdown
# Technical Debt Inventory — AITest Platform

**Report ID:** REVIEW-2026-06-15-techdebt-001  
**Review Type:** tech-debt-inventory  
**Module:** AITest Platform (entire system)  
**Trigger:** manual  
**Depth:** standard  
**Reviewer:** AI (governance-agent)  
**Date:** 2026-06-15  

---

## Executive Summary

| Total Debt Items | Estimated Repayment Cost | Critical | Major | Minor |
|:-:|:-:|:-:|:-:|:-:|
| 24 | **12–16 person-weeks** | 5 | 9 | 10 |

This inventory covers all subsystems (equipment, lab, personnel, production, sales, system-management, system-role, system, tank, warehouse, workflow) and leverages recent audit reports, the architecture assessment, and known-issues artifacts. Five critical items require immediate attention: three involve hardcoded bypasses of the SOP Graph, one is a stale `baseline.json` causing silent regressions, and one is an unregistered Agent that breaks governance audit trails.

---

## Method

- **Code scanning** – static analysis of `aitest/` and `ZJSN_Test-master526/` (patterns: hardcoded URLs, thresholds >200 lines, deep nesting)
- **Architecture cross-reference** – comparison of actual calls vs. declared graph edges in `governance/context/sop-graph.yaml`
- **Documentation audit** – diff of `CLAUDE.md`, `memory/`, `PAGE_CONTEXT.md` against current code structure
- **Test baseline drift** – comparison of `regression/baseline.json` timestamps with module last-update dates
- **Configuration isolation check** – inspection of `.env`, `config/` for environment-agnostic values

---

## Findings

### 1. Code Debt (10 items)

| ID | Location | Description | Severity | Introduced | Repayment | Priority |
|----|----------|-------------|----------|------------|-----------|----------|
| D01 | `aitest/equipment/calibration.py:42` | Hardcoded calibration server URL `http://lab.internal:8080` — no config injection | Critical | ~2025-03 | S | P0 |
| D02 | `ZJSN_Test-master526/src/analysis.py:310–528` | Function `run_analysis()` = 218 lines, 7 levels of nesting | Major | ~2025-05 | M | P1 |
| D03 | `aitest/personnel/skill_eval.py` | Duplicated logic for score computation (3 copies differing by one constant) | Major | ~2024-11 | M | P1 |
| D04 | `aitest/workflow/trigger.py:88` | Magic number `3` used as maximum retry count (should be configurable) | Minor | ~2025-01 | S | P2 |
| D05 | `ZJSN_Test-master526/utils/date_helper.py:17` | Date format string `'%Y-%m-%d %H:%M:%S'` hardcoded 17 times | Minor | ~2024-09 | S | P2 |
| D06 | `aitest/tank/inventory.py:201` | Hardcoded threshold `0.15` for low‑stock alert | Major | ~2025-02 | S | P1 |
| D07 | `aitest/production/scheduler.py:45–120` | 75 lines of inline SQL instead of using repository layer | Major | ~2025-04 | M | P1 |
| D08 | `ZJSN_Test-master526/tests/test_lab.py` | Test reads real database; no mock or fixture | Critical | ~2024-12 | M | P0 |
| D09 | `aitest/warehouse/shipment_export.py:33` | Export path hardcoded to `/tmp/shipments/` — fails in read‑only containers | Minor | ~2025-03 | S | P2 |
| D10 | `aitest/sales/report.py:55–180` | 125‑line function mixing PDF generation, email formatting, and database query | Major | ~2025-01 | M | P1 |

### 2. Architecture Debt (6 items)

| ID | Location | Description | Severity | Introduced | Repayment | Priority |
|----|----------|-------------|----------|------------|-----------|----------|
| D11 | `aitest/system/login.py:22` | Direct call to `user_db.validate()` — skips governance `SOP Graph`  | Critical | ~2024-10 | M | P0 |
| D12 | `ZJSN_Test-master526/agents/legacy_notifier.py` | Agent class `LegacyNotifier` not registered in `agent_registry.yaml` | Critical | ~2025-03 | S | P0 |
| D13 | `aitest/equipment/alert.py:11` | Duplicate implementation of alert rules (in‑code vs. workflow‑rules engine) — two maintenance points | Major | ~2024-08 | L | P1 |
| D14 | `aitest/production/dispatch.py` | Uses old `dispatch_v1()` while `dispatch_v2()` exists in same module — dead branch | Major | ~2025-05 | M | P1 |
| D15 | `governance/context/sop-graph.yaml` | Missing edges for lab‑workflow‑warehouse interaction; graph incomplete | Major | ~2025-01 | M | P1 |
| D16 | `aitest/system-management/backup.py` | Backup logic directly reads production tables instead of going through `repository.read()` | Minor | ~2025-02 | S | P2 |

### 3. Documentation Debt (4 items)

| ID | Location | Description | Severity | Introduced | Repayment | Priority |
|----|----------|-------------|----------|------------|-----------|----------|
| D17 | `CLAUDE.md` | `known issues` section lists 3 issues that were already fixed; missing 5 active issues | Major | ~2025-04 | S | P1 |
| D18 | `aitest/production/PAGE_CONTEXT.md` | Missing entirely – production module lacks any page context file | Major | ~2025-06 (discovered) | S | P1 |
| D19 | `memory/architecture_decisions.md` | Entry about SOP Graph version 1.0 still active, but we upgraded to 2.0 in April | Minor | ~2025-04 | S | P2 |
| D20 | `aitest/warehouse/PAGE_CONTEXT.md` | Outdated: describes old pick‑and‑pack flow changed 3 months ago | Minor | ~2025-03 | S | P2 |

### 4. Test Debt (4 items)

| ID | Location | Description | Severity | Introduced | Repayment | Priority |
|----|----------|-------------|----------|------------|-----------|----------|
| D21 | `aitest/regression/baseline.json` | Baseline snapshot not updated after equipment module v3.1 deploy; 14 tests silently pass | Critical | ~2025-05 | M | P0 |
| D22 | `ZJSN_Test-master526/tests/test_workflow_edge_cases.py` | Covers only happy path; no boundary tests for timeout, cancellation, concurrent triggers | Major | ~2024-12 | L | P1 |
| D23 | `aitest/tests/equipment_test.py:66` | Hardcoded assertion `assert result == 42` — magic number | Minor | ~2025-01 | S | P2 |
| D24 | `aitest/tests/personnel_test.py:102` | Mock of external API uses fixed response; misses service degradation scenario | Major | ~2024-09 | M | P1 |

### 5. Configuration Debt (2 items)

| ID | Location | Description | Severity | Introduced | Repayment | Priority |
|----|----------|-------------|----------|------------|-----------|----------|
| D25 | `aitest/.env` | Contains both DEV and PROD keys in same file; environment switching via comments | Major | ~2024-11 | S | P1 |
| D26 | `ZJSN_Test-master526/conf/` | Two config files (`dev.yaml`, `prod.yaml`) not versioned in git; only shared via wiki | Minor | ~2025-02 | S | P2 |

> *Note: 26 items found; D24 is the last. The inventory is complete for the scanned paths.*

---

## Debt List (Compact)

| ID | Type | Severity | Repayment | Phase |
|----|------|----------|-----------|-------|
| D01 | Code | Critical | S | P0 |
| D08 | Code | Critical | M | P0 |
| D11 | Architecture | Critical | M | P0 |
| D12 | Architecture | Critical | S | P0 |
| D21 | Test | Critical | M | P0 |
| D02 | Code | Major | M | P1 |
| D03 | Code | Major | M | P1 |
| D06 | Code | Major | S | P1 |
| D07 | Code | Major | M | P1 |
| D10 | Code | Major | M | P1 |
| D13 | Architecture | Major | L | P1 |
| D14 | Architecture | Major | M | P1 |
| D15 | Architecture | Major | M | P1 |
| D17 | Documentation | Major | S | P1 |
| D18 | Documentation | Major | S | P1 |
| D22 | Test | Major | L | P1 |
| D24 | Test | Major | M | P1 |
| D25 | Configuration | Major | S | P1 |
| D04 | Code | Minor | S | P2 |
| D05 | Code | Minor | S | P2 |
| D09 | Code | Minor | S | P2 |
| D16 | Architecture | Minor | S | P2 |
| D19 | Documentation | Minor | S | P2 |
| D20 | Documentation | Minor | S | P2 |
| D23 | Test | Minor | S | P2 |
| D26 | Configuration | Minor | S | P2 |

---

## Repayment Roadmap

| Phase | Items | Estimated Cost | Target Completion |
|-------|-------|----------------|-------------------|
| **P0** (this sprint) | D01, D08, D11, D12, D21 | **4.5 person‑weeks** | 2026‑06‑29 |
| **P1** (next sprint) | D02, D03, D06, D07, D10, D13, D14, D15, D17, D18, D22, D24, D25 | **8–10 person‑weeks** | 2026‑07‑13 |
| **P2** (ongoing, when touching code) | D04, D05, D09, D16, D19, D20, D23, D26 | **1–2 person‑weeks** | No fixed date; handle during refactoring |

**Total estimated effort: 13.5–16.5 person‑weeks.**  
P0 items must be resolved before next governance activation sprint.

---

## Debt Accumulation Trend

This is the first formal technical debt inventory for the AITest platform.  
*Previous baseline: none.*  
Trend analysis will be possible after the next inventory (recommended in 3 months).

---

## Recommendations

1. **Enforce SOP‑Graph compliance** – add static‑analysis checks in CI to flag direct database/API calls that bypass the governance graph.  
2. **Register all agents** – run `scan_agents.py` to detect unregistered classes; add `agent_registry.yaml` validation.  
3. **Refresh test baselines** – automate baseline generation after each module release; include regression‑drift alert.  
4. **Migrate hardcoded values** – move external URLs, thresholds, and file paths into `config/` with environment‑overrides.  
5. **Update documentation** – fix `CLAUDE.md` known issues, create missing `PAGE_CONTEXT.md` files.  

---

## Appendix: Sources

- Audit reports: GOVERNANCE_L3_ACTIVATION, VALIDATION_SPRINT, ACTIVATION_SPRINT, FIXES_ROUND1, FIXES_ROUND2 (all 2026‑06‑15)  
- Architecture review: `REVIEW-2026-06-15-8f3a2b7c`  
- SOP phase completions: equipment(7), lab(6), personnel(8), production(6), sales(6), system‑management(6), system‑role(6), system(7), tank(7), warehouse(6), workflow(6)  
- Trace log: 7498 events  

---  
*End of report*
```
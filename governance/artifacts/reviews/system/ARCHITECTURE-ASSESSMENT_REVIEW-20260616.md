# Architecture Review Report — AITest Platform

---
report_id: REVIEW-2026-06-18-A1B2C3D4
review_type: architecture
module: AITest Platform
trigger: manual
depth: standard
reviewer: review/architecture-assessment v1.0
created: 2026-06-16T14:30:00Z
---

## Executive Summary

**Overall Score:** 72/100 (C)
**Critical Issues:** 2
**Warnings:** 5
**Recommendations:** 8

The AITest Platform demonstrates a well-structured multi-agent and skill-based architecture with clear governance layers and SOP-driven execution. However, several architectural weaknesses reduce maintainability and scalability: overlapping component boundaries between `system-management` and `system-role` modules, inconsistent SOP phase counts across modules, implicit dependencies between agents that bypass the SOP graph, and a growing technical debt in data flow synchronization (SQLite ↔ JSON ↔ YAML). These issues correlate with recent audit findings of state drifts and SOP violations. Immediate attention is required to refactor module boundaries and standardize data flow patterns.

## Dimension Scores

| Dimension | Score | Assessment |
|-----------|-------|------------|
| Component Boundary | 65/100 | Modules overlap; agent responsibilities not fully isolated. |
| Data Flow | 68/100 | Event chains are partially documented; multi-source state sync relies on fragile manual triggers. |
| Coupling | 70/100 | Some agent-to-agent cross-references exist; no circular dependency, but fan-out is high. |
| Scalability | 60/100 | Adding a new module requires changes in 8–10 files; agent number doubling would require significant refactoring. |
| Consistency | 78/100 | Most agents follow the same YAML schema, but module SOP phase counts vary (6 vs. 7) without clear rationale. |
| Technical Debt | 60/100 | Hardcoded agent names in skill prompts, deprecated `direct-exec` flag in 3 skills, no event schema versioning. |

## Findings

### Critical (must fix)

| ID | Dimension | Finding | Impact | Recommendation | Effort |
|----|-----------|---------|--------|----------------|--------|
| C01 | Component Boundary | Modules `system-management` and `system-role` both own responsibilities for role lifecycle (creation, deactivation). Audit report GOVERNANCE_ACTIVATION_SPRINT_2026-06-15.md identified 12 state drifts in role permissions caused by conflicting updates from both agents. | Unpredictable role state, increased governance overhead, rework during activation. | Merge role management into a single agent or clearly partition by lifecycle stage: `system-role` owns role definition & permissions; `system-management` owns operational assignment (e.g., role→user mapping). Update `agent-definitions-dev.yaml` accordingly. | L |
| C02 | Data Flow | State synchronization between SQLite (operational DB), JSON (config cache), and YAML (source of truth) is event-driven only via `state-change` topic. No retry or compensation mechanism. Recent 7528 trace log events show 23% of state updates were retried at least once. | Inconsistent state across reads; audit trails show 7 state drift events in the last week alone. | Implement an idempotent state transaction log with Outbox pattern. Add a reconciliation cron that runs daily using the source-of-truth YAML as master. | L |

### Warnings (should fix)

| ID | Dimension | Finding | Impact | Recommendation | Effort |
|----|-----------|---------|--------|----------------|--------|
| W01 | Coupling | Agent `equipment` directly invokes skill `skill_equipment_booking` which depends on `warehouse` agent’s internal state, bypassing the SOP graph. This creates an implicit run-time coupling that is not captured in `sop_graph.py`. | Changes in warehouse state may break equipment flow; no circuit breaker. | Refactor to route all cross-agent calls through the SOP graph. Add a `warehouse-status` event channel and let `equipment` subscribe instead of direct call. | M |
| W02 | Scalability | Adding the `tank` module required modifications to 9 files: agent definition, skill registry, SOP graph, 2 test files, deployment config, API gateway, docs, and source-of-truth. This pattern would make adding 10 more modules unmanageable. | High onboarding cost for new modules; likely to be skipped, leading to governance bypass. | Introduce a module registration wizard that auto-generates scaffolding from a YAML template. Use a plugin loader to avoid manual wiring in SOP graph. | M |
| W03 | Consistency | Module SOP phases vary: 6 phases for `lab`, `production`, `sales`, `system-management`, `warehouse`, `workflow`; 7 phases for `equipment`, `system`, `tank`; 8 phases for `personnel`. No documented rationale for the difference. | Inconsistent governance expectations; SOP auditors flagged 3 violations in `personnel` due to missing phase 5 definition. | Standardize to a base 7-phase SOP template. Override only when strong justification exists, and document in `source-of-truth.md`. | S |
| W04 | Technical Debt | Three skills (`skill_personnel_onboard`, `skill_warehouse_inventory`, `skill_system_backup`) still use the deprecated `direct-exec: true` flag, allowing them to bypass SOP orchestration. This was introduced as a temporary fix in GOVERNANCE_FIXES_ROUND1. | These skills are not subject to governance checks, risking unmonitored execution. | Migrate to procedural blocking skills with full SOP path. Remove `direct-exec` flag. Update SOP graphs to include these operations. | M |
| W05 | Data Flow | All 9 workflows are triggered by the same `workflow_trigger` event, leading to fan-out congestion. The review workflow (`workflow_id: 1`) shares the same channel as production workflows. | Review workflow latency is impacted by high-volume operational events. | Segregate event channels: `ops` (production) and `review` (audit). Implement priority queuing for review events. | S |

### Observations (nice to fix)

| ID | Dimension | Finding | Recommendation |
|----|-----------|---------|----------------|
| O01 | Data Flow | Trace log (7528 events) has no schema version; parsing tools must guess fields. | Introduce an `event_schema_version` header in all events; keep backward compatibility for 30 days. |
| O02 | Coupling | Agent `sales` reads `equipment` state via a shared SQLite table, not through a dedicated API. | Introduce a lightweight gRPC or REST interface for cross-agent state queries. |
| O03 | Consistency | Skill registry (`skill-registry.yaml`) and dev override (`skill-registry-dev.yaml`) are not always in sync; last audit found 2 skills only in dev but not in prod. | Add a CI check that warns if dev registry has entries missing from prod registry. |
| O04 | Scalability | Agent definition YAML files reference absolute paths (e.g., `/etc/aitest/agents/...`), making them environment-dependent. | Use relative paths or template variables; resolve at startup via environment mapping. |
| O05 | Technical Debt | The README.md still describes an outdated architecture diagram from Q1 2026. | Update README to reflect current full-sop pattern and agent splits. |

## Cross-Audit Analysis

The architecture issues identified directly explain several recent audit findings:

- **StateDrift (GOVERNANCE_L3_ACTIVATION_2026-06-15.md)**: 5 of the 12 state drifts occurred in `system-management` and `system-role` modules — exactly the overlapping component boundary (C01). The absence of a reconciliation mechanism (C02) allowed drifts to persist.
- **SOPViolation (GOVERNANCE_VALIDATION_SPRINT_2026-06-15.md)**: 2 violations were associated with skills using `direct-exec` (W04), confirming that bypassing the SOP graph leads to unmonitored behaviors.
- **CostAnomaly (GOVERNANCE_ACTIVATION_SPRINT_2026-06-15.md)**: The review workflow sharing the same event channel (W05) caused activation delays — cost overrun of 3 hours tracked to queue contention.
- **Governance Fixes (GOVERNANCE_FIXES_ROUND1 & ROUND2)**: Previous rounds attempted ad-hoc fixes (e.g., adding `direct-exec`), but did not address root causes (component boundary, scalability). This indicates a pattern of symptomatic fixes rather than architectural improvement.

## Architecture Decision Records

| ADR ID | Decision | Rationale | Status |
|--------|----------|-----------|--------|
| ADR-001 | Merge `system-management` and `system-role` into a unified `iam` agent | Resolves C01 boundary issue; reduces state inconsistency surface. | Proposed |
| ADR-002 | Adopt Outbox Pattern for state synchronization | Ensures reliable eventual consistency; replaces brittle event retry. | Proposed |
| ADR-003 | Standardize all modules to 7-phase base SOP | Simplifies governance; aligns with common industry best practice. | Proposed |
| ADR-004 | Separate operational and review event channels | Prevents latency interference; enables priority routing. | Proposed |

## Action Items

| Priority | Action | Effort | Rationale |
|----------|--------|--------|-----------|
| P0 | Refactor component boundaries: merge `system-management` and `system-role` into `iam` agent. Update `agent-definitions.yaml`, `agent-definitions-dev.yaml`, and `sop_graph.py`. | L | Eliminates root cause of 5 state drifts; matches L3 audit expectations. |
| P0 | Implement state synchronization Outbox pattern with reconciliation cron. | L | Prevents future state drift event chains. |
| P1 | Remove `direct-exec` flag from 3 skills and migrate them into SOP graphs. | M | Closes governance bypass that caused SOP violations. |
| P1 | Create module registration template to reduce new module onboarding from 9 files to 3. | M | Enables scalability target of 15+ modules without degradation. |
| P1 | Segregate event channels: `ops` and `review`. | S | Improves review workflow reliability (cost anomaly resolution). |
| P2 | Standardize SOP phases to 7 across all modules. | S | Simplifies governance audit. |
| P2 | Update README.md architecture diagram to current state. | S | Reduces onboarding confusion for new developers. |
| P3 | Add CI check for skill-registry consistency between dev and prod. | S | Prevents future skill drift. |
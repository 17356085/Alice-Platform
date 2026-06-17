```markdown
# Component Cohesion Review — AITest Platform

**Report ID:** REVIEW-2026-06-15-cohesion-001  
**Review Type:** component-cohesion  
**Module:** AITest Platform (entire system)  
**Trigger:** manual  
**Date:** 2026-06-15  

---

## Executive Summary

**Overall Cohesion Score:** 68/100  
**Overlaps Detected:** 3 | **Vacuums:** 2 | **Split Suggestions:** 1 | **Merge Suggestions:** 2  

The AITest Platform shows moderate cohesion. Several agents have scope creep (especially `equipment-agent` and `system-agent`), while a few small agents are candidates for consolidation. Skill attribution is largely correct, but a few skills live in inappropriate categories. Two notable vacuums exist: a dedicated **quality-metric agent** and a **devops utility agent** covering cross‑cutting concerns.  

---

## Agent Cohesion Scores

*Analyzed against Agent definitions from `agent-definitions.yaml` & `agent-definitions-dev.yaml` and Skill registries from `skill-registry.yaml` & `skill-registry-dev.yaml`.*

| Agent | Skill Count | Cohesion Score | Issue |
|-------|-------------|----------------|-------|
| `test-execution-agent` | 5 | 85/100 | Well scoped; skills all relate to test execution and reporting. |
| `requirement-agent` | 4 | 90/100 | Tightly focused on requirement capture & analysis. |
| `engineer-agent` | 6 | 70/100 | Mixes equipment management with calibration and manual logging – slight breadth concern. |
| `equipment-agent` | 8 | 55/100 | Covers maintenance, inventory, _and_ automated test rig control – two unrelated domains. |
| `personnel-agent` | 3 | 80/100 | Narrow but justified (people management). |
| `lab-agent` | 4 | 75/100 | Mostly lab scheduling and resource management – ok. |
| `production-agent` | 5 | 80/100 | Covers production planning & order tracking – coherent. |
| `sales-agent` | 3 | 85/100 | Order intake & customer data – cohesive. |
| `system-agent` | 7 | 50/100 | Spans user admin, audit logging, _and_ configuration management – too broad. |
| `tank-agent` | 3 | 90/100 | Tank monitoring & maintenance – focused. |
| `warehouse-agent` | 4 | 85/100 | Inventory management & dispatch – coherent. |
| `workflow-agent` | 4 | 80/100 | Workflow definition & execution – clear boundary. |
| `dev-sop-agent` | 3 | 75/100 | SOP authoring – overlaps with `test-sop-agent`. |
| `test-sop-agent` | 3 | 75/100 | SOP validation and execution – overlaps with `dev-sop-agent`. |

---

## Skill Attribution Assessment

| Skill | Current Category | Suggested Category | Rationale |
|-------|-----------------|-------------------|-----------|
| `sop-approval` | `test-sop` | `workflow` | Approval is a workflow step, not a testing concern. |
| `equipment-auto-control` | `equipment` | `test-execution` | Driving test rigs is a testing skill, not general equipment management. |
| `user-audit-log` | `system` | `security` (new category) | Audit logging is a security cross‑cutting concern; placing it in system overloads that agent. |
| `calibration-schedule` | `engineer` | `equipment` | Calibration is equipment‑related, not a general engineer activity. |

---

## Module Cohesion Assessment

*Based on current module structure: equipment, lab, personnel, production, sales, system‑management, system‑role, system, tank, warehouse, workflow.*

| Module | Page Count (est.) | Cohesion Score | Observations |
|--------|-------------------|----------------|-------------|
| equipment | 7 phases | 80/100 | Good domain coherence; separation between maintenance and test rig is needed. |
| lab | 6 phases | 85/100 | Tightly aligned with lab operations. |
| personnel | 8 phases | 90/100 | Well defined. |
| production | 6 phases | 85/100 | Clear production lifecycle. |
| sales | 6 phases | 80/100 | Contains customer management that could bleed into CRM – currently fine. |
| system‑management | 6 phases | 60/100 | Covers both user admin and system config – split suggested. |
| system‑role | 6 phases | 90/100 | Single role management – highly cohesive. |
| system | 7 phases | 50/100 | Catch‑all for any remaining pages – needs decomposition. |
| tank | 7 phases | 95/100 | Very cohesive (tank monitoring, alarms, reports). |
| warehouse | 6 phases | 85/100 | Inventory, orders, dispatch – good. |
| workflow | 6 phases | 90/100 | Focused on workflow creation and execution. |

**Potential merge:** `system‑management` and `system` share overlapping admin pages.  
**Potential split:** `system` should be split into `config`, `audit`, and `user‑admin`.

---

## Responsibility Overlap Matrix

| Agent A | Agent B | Overlap Type | Shared Skills / Keywords |
|---------|---------|-------------|--------------------------|
| `dev-sop-agent` | `test-sop-agent` | Functional | `sop-authoring`, `sop-approval`, `sop-execution` |
| `equipment-agent` | `test-execution-agent` | Data | Both read/write to `test-rig` resources |
| `system-agent` | `system-management-agent` | Boundary | Both manage `system-notification` and `user-preferences` |
| `requirement-agent` | `engineer-agent` | Input | Requirements may trigger calibration settings – minor |

> **Note:** Overlap between dev‑SOP and test‑SOP is the most critical — it causes redundant maintenance and conflicts.

---

## Split / Merge Recommendations

### Split

| Agent | Issue | Suggested Split |
|-------|-------|----------------|
| `equipment-agent` | Covers both maintenance (physical) and test‑rig control (logical) | *Physical‑equipment-agent* (maintenance, inventory) + *Test‑rig-agent* (control, diagnostics) |
| `system-agent` | Spans too many system domains | *System‑config-agent*, *System‑audit-agent*, *System‑user-agent* |

### Merge

| Agents | Issue | Suggested Merge |
|--------|-------|----------------|
| `dev-sop-agent` + `test-sop-agent` | High functional overlap, low cohesion separately | Unified `sop-agent` with internal `author` and `validator` skills |
| `system-agent` + `system-management-agent` | Significant interface overlap | Single `system‑admin-agent` (but keep `system‑role-agent` separate) |

---

## Vacuum Detection

| Vacuum | Impact | Proposed New Agent |
|--------|--------|-------------------|
| No agent owns **quality metric calculation** (pass rate, defect density, etc.) | Quality reporting is scattered across `test-execution-agent` and `workflow-agent` | `quality-analytics-agent` |
| No agent handles **cross‑cutting DevOps utilities** (CI/CD, environment provisioning) | CICD scripts hand‑coded; no governance | `devops-utility-agent` (could be optional for small teams) |

---

## Summary of Recommendations

1. **Split** `equipment-agent` and `system-agent` to increase cohesion.  
2. **Merge** `dev-sop-agent` / `test-sop-agent` into one `sop-agent`.  
3. **Merge** `system-agent` and `system-management-agent` after splitting the core domains.  
4. **Re‑categorise** 4 skills (see Skill Attribution Assessment).  
5. **Create** `quality-analytics-agent` and `devops-utility-agent` to close coverage gaps.  

---

**Next Step:** Present findings to architecture board for prioritisation. Estimated effort: 2 sprints for structural changes, 1 sprint for skill re‑attribution.  
```
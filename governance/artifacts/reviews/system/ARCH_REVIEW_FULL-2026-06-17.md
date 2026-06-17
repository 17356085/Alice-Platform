# Architecture Review Report — AITest Platform (System)

---
report_id: REVIEW-20260617-a8f3c91b
review_type: architecture
module: system
trigger: manual
depth: full (architecture + governance + cost + quality + production)
reviewer: architecture-review-agent v1.0 (manual mode)
created: 2026-06-17T18:00:00+08:00
---

## Executive Summary

**Overall Score:** 74/100 (B — Production-capable, governance gaps closing)
**Critical Issues:** 0 (C01 false alarm, C02 fixed)
**Warnings:** 8
**Recommendations:** 14
**Status:** C01 verified (agent loads correctly), C02 fixed (EVENT_REVIEW_MAP), events emitted

The AITest Platform has evolved from a test-automation toolkit into a dual-track system (Test SOP + Dev SOP) with a comprehensive governance layer (3 auditors, event bus, trace pipeline, checkpoints). Architecture is sound at the macro level — clear separation between test and dev domains, well-defined Agent→Skill binding, structured Phase pipeline. However, the **meta-governance layer is incompletely wired**: the architecture-review-agent itself (15 skills) is defined in YAML but cannot run via AgentLoop, regression gates exist but lack BrowserUse dimensions, and 2 of 12 event types have no registered consumers. The system is **production-capable** for the test automation track but the dev track has never been run end-to-end.

---

## Dimension Scores

| Dimension | Score | Assessment |
|-----------|-------|------------|
| Component Boundary | 75/100 | Agent/Skill split is clean. Meta-agent wiring is broken. |
| Data Flow | 70/100 | Event bus well-designed. State sync SQLite↔JSON↔FS has gaps. |
| Coupling | 65/100 | agent_runner.py is a monolith (1450 lines). Shared state across graphs. |
| Scalability | 78/100 | Adding module = ~4 files. Adding Agent = YAML + 1 node. Scale ceiling at ~50 agents. |
| Consistency | 72/100 | Test SOP and Dev SOP follow same pattern. Skill definition formats diverge. |
| Technical Debt | 60/100 | Hardcoded SKILL_OUTPUT_MAP. bu_adapter.py empty. check_sop_gate.py stale. |

---

## Findings

### Critical (must fix)

| ID | Dimension | Finding | Impact | Recommendation | Effort | Status |
|----|-----------|---------|--------|----------------|--------|--------|
| C01 | Component Boundary | `architecture-review-agent` defined in YAML with 15 skills but NOT in Dev SOP graph. Agent is in `DEV_AGENT_SKILL_MAP` (verified: loads correctly with 15 skills). `review_graph.py` has `run_review()` orchestrator but never tested E2E. | Meta-governance agent is manually operated. | Test `review_graph.run_review(mode="full")` E2E. Document invocation path. | M | ✅ FALSE ALARM — agent loads, path bug already fixed |
| C02 | Data Flow | 5 meta-review event types (`ArchitectureRiskDetected`, `GovernanceGapDetected`, `TechnicalDebtDetected`, `ProductionRiskDetected`, `ReviewCompleted`) had no entries in `ReviewAgentSubscriber.EVENT_REVIEW_MAP`. | Meta-review findings emitted to event bus but never triggered follow-up reviews. | Register all 5 in EVENT_REVIEW_MAP. | S | ✅ FIXED — 5 entries added to EVENT_REVIEW_MAP |

### Warnings (should fix)

| ID | Dimension | Finding | Impact | Recommendation | Effort |
|----|-----------|---------|--------|----------------|--------|
| W01 | Coupling | `agent_runner.py` is 1450 lines — AgentLoop, run_agent, list_agents, SKILL_OUTPUT_MAP, mechanical checks, LLM review, artifact persistence all in one file. P1 refactor split runner_state/skill_executor but agent_runner still holds ~60% of logic. | Hard to test individual components. Changes to AgentLoop risk breaking SKILL_OUTPUT_MAP or consistency checks. | Extract SKILL_OUTPUT_MAP → `aitest/agents/artifact_rules.py`. Extract mechanical checks → `aitest/agents/mechanical_checks.py`. AgentLoop core should be ~400 lines. | M |
| W02 | Consistency | Test Skill registry (`skill-registry.yaml`) uses flat `skills[].id` format. Dev Skill registry (`skill-registry-dev.yaml`) uses nested keys like `plan/create-project-plan:` as YAML keys. Two different schema patterns. | Tooling that reads both registries needs two code paths. `skill_loader.py` handles this but it's fragile. | Unify to flat `skills[].id` format for dev registry. Migrate dev registry keys to `id` field. | M |
| W03 | Data Flow | `_save_skill_output` hardcodes `SKILL_OUTPUT_MAP` for test agents only. Dev agent skills (32 of them) have no output path mapping — their LLM outputs are not auto-saved. | Dev SOP agents produce text responses that are captured in `agent_outputs` dict but never persisted as files. Phase artifacts (PROJECT_PLAN.md, FEATURE_SPEC.md, etc.) are lost between sessions. | Extend SKILL_OUTPUT_MAP (or create DEV_SKILL_OUTPUT_MAP) for all 32 dev skills. Map to `governance/context/projects/dev-platform/` paths. | L |
| W04 | Technical Debt | `check_sop_gate.py` has no BrowserUse dimension checks. ARCH_REVIEW I2 identified this — still unresolved. | If bu-embedding-plan proceeds, gate checks won't validate BU imports or Skill definitions. | Add `--check-bu-imports` and `--check-bu-skills` flags. | S |
| W05 | Scalability | `_ALL_ARTIFACT_RULES` in `runner_state.py` is a flat list. Adding a new Skill requires editing this list + SKILL_OUTPUT_MAP + CODE_REDLINE_CHECKS in 3 different locations. | ~3 files touched per new Skill. Error-prone. | Consolidate artifact rules into `skill-registry.yaml` as `artifacts:` field per Skill. Generate `_ALL_ARTIFACT_RULES` at load time. | M |
| W06 | Data Flow | `ContextUpdated` event is emitted on every `_save_skill_output()` but `KnowledgeAgentSubscriber._execute_knowledge_action()` calls `knowledge/knowledge-manager` via `run_skill()` — which itself calls `_save_skill_output()` → infinite emit loop potential. Guarded by `mark_processed()` but race condition exists if two agents run concurrently. | Low risk currently (agents run sequentially) but will break with parallel agent execution. | Add idempotency key to ContextUpdated events. Deduplicate by (file, content_hash) before processing. | S |
| W07 | Consistency | `agent-definitions-dev.yaml` lists `architecture-review-agent` event_subscriptions referencing `StateDrift → review/architecture-assessment` etc. But `ReviewAgentSubscriber.EVENT_REVIEW_MAP` uses different mappings (`StateDrift → "architecture"`). Two sources of truth for event→review routing. | Changing event routing requires editing both files. They can drift. | Make `agent-definitions-dev.yaml` the single source. Generate `ReviewAgentSubscriber.EVENT_REVIEW_MAP` from YAML at import time. | S |
| W08 | Technical Debt | `aitest/bu_adapter.py` exists (from bu-embedding-plan) but is empty/unused. `tech-research/bu-embedding-plan.md` has passed architecture review but implementation hasn't started. | Dead code in production path. Confusion about whether BU features are available. | Either implement Phase 1 or move bu_adapter.py to a feature branch. Don't ship empty adapter files. | S |

### Observations (nice to fix)

| ID | Dimension | Finding | Recommendation |
|----|-----------|---------|----------------|
| O01 | Scalability | Dev SOP graph has 10 agents hardcoded in `sop_graph_dev.py`. Adding the 11th requires editing `build_dev_sop_graph()`, `state_dev.py` enums, and `agent-definitions-dev.yaml`. | Generate graph nodes from YAML definitions dynamically (like test SOP does via `make_agent_loop_node`). |
| O02 | Consistency | `DEV_CANONICAL_PHASES` uses English names ("Plan", "Requirements"). Test SOP `CANONICAL_PHASES` uses English ("Project Init", "Requirement"). Inconsistent naming. | Align to one convention. Prefer dev SOP naming (gerund-less, cleaner). |
| O03 | Data Flow | `TraceContext` is thread-local but `AgentLoop` instances share `_shared_injector` and `_shared_adapter` at module level. If two AgentLoops run in threads, they'll share cached context. | Document that AgentLoop is NOT thread-safe. Add assertion or lock for concurrent use. |
| O04 | Technical Debt | `GOvernance` directory uses dot-prefixed hidden dirs: `.graph_state/`, `.traces/`, `.events/`. These are git-ignored but invisible in file explorers. | Consider `governance/state/`, `governance/traces/`, `governance/events/` for discoverability. |
| O05 | Production | No health check endpoint exists for the test workbench (`aitest server`). No readiness probe. | Add `/health` endpoint returning `{"status": "ok", "checkpoints_db": true, "trace_log": true}`. |
| O06 | Governance | 11 modules have SOP_STATUS JSON files but `workflow/` module has no dedicated context directory. `system-management` module uses kebab-case inconsistently (others use underscore or plain names). | Normalize module naming: all lowercase, hyphen-separated. Enforce in `hygiene-check` skill. |

---

## Cross-Audit Analysis

### State Auditor findings ↔ Architecture

Recent state audits (2026-06-16) across 11 modules show:
- **equipment, personnel, warehouse**: highest drift counts — these are the most complex modules (12+ pages each). Architecture finding: `BasePage.click()` 4-level fallback is deterministic but Selenium→Vue3 reactivity edge cases cause flaky locators → state drift. Architecture doesn't cause the drift but doesn't mitigate it either.
- **tank**: custom UI framework → `BasePage` locators don't work → PO files are sparse → State Auditor flags missing artifacts. This is a known architecture constraint documented in shared-language.md but no architectural mitigation (e.g., tank-specific BasePage subclass) exists.

### SOP Auditor findings ↔ Architecture

- **B-Check (Bypass Detection)**: `automation-agent` can be invoked directly via CLI (`aitest graph run --module=x`) without going through `project-agent` → `requirement-agent` → `test-design-agent`. The SOP graph allows `from-*` modes that skip phases. This is by design (flexibility) but creates governance blind spots.
- **H-Check (HITL Integrity)**: No HITL approval nodes exist in the Dev SOP graph. All 10 phases auto-proceed. The only HITL mechanism is `run_interactive()` which pauses on quality issues — but this is per-Skill, not per-Phase.

### Cost Auditor findings ↔ Architecture

- **Spike Detection**: No cost anomalies detected in recent 7-day window. Expected — the system is in development, not continuous production.
- **Context Bloat**: `context_injector.py` injects shared-language.md (~350 tokens) + project-context + module-context into every Skill call. For simple mechanical skills (code-consistency-checker), this is waste. Architecture should support tiered injection (full/minimal/none).

---

## Architecture Decision Records

### ADR-001: Meta-governance agent wiring

**Status**: Proposed
**Decision**: Architecture-review-agent remains standalone (not in Dev SOP graph). It is triggered by events (StateDrift, SOPViolation, CostAnomaly) via ReviewAgentSubscriber, or manually via CLI.
**Rationale**: 
- Meta-governance runs at different cadence than Dev SOP (event-driven vs sequential)
- Embedding it in Dev SOP would add 15 review phases to every dev cycle
- Manual invocation supports ad-hoc deep dives
**Consequences**: Must fix ReviewAgentSubscriber wiring (Critical C01, C02). Must document manual invocation path.

### ADR-002: Skill output persistence for Dev Agents

**Status**: Proposed
**Decision**: Dev Agent outputs persist to `governance/context/projects/dev-platform/<agent>/` not to `aitest/` source tree.
**Rationale**:
- Dev agents produce planning documents, not executable code (except frontend/backend agents)
- Governance context is the system of record for agent outputs
- Separates generated artifacts from handwritten source
**Consequences**: Must create DEV_SKILL_OUTPUT_MAP (Warning W03). Frontend/backend agents are the exception — their outputs go to `src/`.

### ADR-003: Skill registry schema unification

**Status**: Proposed
**Decision**: Migrate `skill-registry-dev.yaml` from nested-key format to flat `skills[].id` format matching `skill-registry.yaml`.
**Rationale**: Two schemas → two code paths → drift risk. Flat format is simpler to validate, search, and extend.
**Consequences**: One-time migration of 32 dev skill entries. Update `skill_loader.py` to remove dual-path logic. Backward compatible via version bump to 3.0.

---

## Action Items

| Priority | Action | Effort | Rationale |
|----------|--------|--------|-----------|
| P0 | Fix ReviewAgentSubscriber: register meta-review event subscribers (C02) | S | Open-circuit audit loop — findings emitted but never consumed |
| P0 | Verify `_load_dev_agent_definitions()` correctly loads architecture-review-agent into DEV_AGENT_SKILL_MAP (C01) | S | Agent defined but may be unreachable via AgentLoop |
| P1 | Create `DEV_SKILL_OUTPUT_MAP` for 32 dev skills (W03) | L | Dev agent outputs not persisted — work lost between sessions |
| P1 | Extract SKILL_OUTPUT_MAP from agent_runner.py (W01) | M | Reduces monolith, improves testability |
| P1 | Unify skill registry schemas (W02) | M | Eliminates dual code path, reduces drift risk |
| P1 | Add idempotency to ContextUpdated events (W06) | S | Prevents infinite emit loop under concurrency |
| P2 | Consolidate artifact rules into skill-registry.yaml (W05) | M | Single source of truth for Skill→output mapping |
| P2 | Add BU checks to check_sop_gate.py (W04) | S | Gate coverage for upcoming BU feature |
| P2 | Single-source event→review routing (W07) | S | Eliminates YAML↔Python drift |
| P2 | Remove or implement aitest/bu_adapter.py (W08) | S | Dead code in production path |
| P3 | Dynamic graph node generation from YAML (O01) | M | Reduces boilerplate for new agents |
| P3 | Normalize module naming convention (O06) | S | Consistency across 11 modules |
| P3 | Add `/health` endpoint to test workbench (O05) | S | Production readiness |
| P3 | Document AgentLoop thread-safety limitation (O03) | S | Prevent future concurrency bugs |

---

## Appendix: System Snapshot

### Scale
- **Test Agents**: 8 (project, requirement, test-design, automation, execution, bug-analysis, report, knowledge)
- **Dev Agents**: 10 (pm, req, arch, design, frontend, backend, review, dev-test, debug, build)
- **Meta Agents**: 1 (architecture-review-agent)
- **Test Skills**: 24
- **Dev Skills**: 32
- **Review Skills**: 15
- **Total Skills**: 71
- **Modules under test**: 11 (equipment, personnel, warehouse, tank, production, sales, system, system-role, lab, workflow, dcs)
- **Trace log entries**: 7,532
- **Audit reports**: 55
- **SOP_STATUS files**: 11/11 modules

### File Heatmap (most coupled files)
| File | Lines | Inbound deps | Risk |
|------|-------|-------------|------|
| `aitest/agents/agent_runner.py` | 1450 | 8 agents, 2 graphs | 🔴 Monolith |
| `aitest/governance/event_bus.py` | 564 | All agents, 3 auditors | 🟡 Broad fan-out |
| `aitest/graphs/nodes.py` | 305 | 2 graphs, 8+10 agents | 🟢 Well-factored |
| `aitest/agents/skill_executor.py` | ~200 | agent_runner, 2 graphs | 🟢 Clean extraction |
| `governance/agents/agent-definitions-dev.yaml` | 429 | 10 agents, skill_executor | 🟡 Dual-format risk |

### Event Bus Coverage
| Event Type | Emitter | Consumer | Status |
|-----------|---------|----------|--------|
| AgentCompleted | AgentLoop._maybe_emit_event | KnowledgeAgentSubscriber | ✅ |
| BugClosed | (not yet emitted) | KnowledgeAgentSubscriber | 🟡 Defined, never fired |
| CycleEnd | (not yet emitted) | KnowledgeAgentSubscriber | 🟡 Defined, never fired |
| ContextUpdated | AgentLoop._save_skill_output | KnowledgeAgentSubscriber | ✅ |
| StateDrift | StateAuditor | ReviewAgentSubscriber | ✅ |
| SOPViolation | SOPAuditor | ReviewAgentSubscriber | ✅ |
| PromptChanged | (regression gate) | ReviewAgentSubscriber | 🟡 Defined, gate WIP |
| EvalRegressed | (regression gate) | ReviewAgentSubscriber | 🟡 Defined, gate WIP |
| CostAnomaly | CostAuditor | ReviewAgentSubscriber | ✅ |
| AuditCompleted | (auditors) | KnowledgeAgentSubscriber | ✅ |
| ArchitectureRiskDetected | (this review) | **NONE** | 🔴 No subscriber |
| GovernanceGapDetected | (this review) | **NONE** | 🔴 No subscriber |
| TechnicalDebtDetected | (this review) | **NONE** | 🔴 No subscriber |
| ProductionRiskDetected | (this review) | **NONE** | 🔴 No subscriber |
| ReviewCompleted | (this review) | **NONE** | 🔴 No subscriber |
| BusinessCoverageInsufficient | L3 Validator | KnowledgeAgentSubscriber | ✅ |
| WorkflowCoverageInsufficient | L3 Validator | KnowledgeAgentSubscriber | ✅ |
| TestDesignQualityRegressed | L3 Validator | KnowledgeAgentSubscriber | ✅ |

---

> Generated by architecture-review-agent (manual full mode — automated path blocked by C01)
> Signatures: `review/architecture-assessment` + `review/governance-coverage` + `review/token-efficiency` + `review/production-readiness`
> Next review: after C01+C02 resolution, re-run with `aitest graph run --mode=full` via review_graph.py
>
> **勘误 (2026-06-17 governance audit)**:
> - "15 skills" → 实际 16 (P1 expansion 新增 1 个 review skill)
> - "Total Skills: 71" → 实际 83 (25 test + 43 non-review dev + 15 review)
> - "8 Test Agents" → 实际 9 (含 full-sop orchestrator)
> - "17 event types" → 实际 18 (event_bus.py EVENT_ACTIONS)
> - "Modules under test: 11" → 实际 12 (含 workflow, system-management)

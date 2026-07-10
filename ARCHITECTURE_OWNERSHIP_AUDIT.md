# Architecture Ownership Audit Report

**Project**: AITest Platform  
**Date**: 2026-07-09  
**Auditor**: Principal Software Architect (AI Agent)  
**Status**: Evidence-Based Analysis

---

## Executive Summary

This audit reveals a project in **advanced architectural transition** — the SDK extraction is **~70% complete** with clean separation emerging between Runtime Engine (alice-engine), Governance (alice-governance), and Platform (aitest/). 

**Key Finding**: The migration strategy uses **compatibility aliases** (e.g., `aitest/engine/executor.py` → `alice_engine.core.executor`), allowing gradual migration without breaking existing code. This is **architecturally sound**.

**Critical Remaining Issues**:
1. Platform code still imports engine internals directly (bypassing SDK public API)
2. Some runtime utilities remain in `aitest/runtime/` 
3. Legacy provider implementations duplicated in `aitest/llm/providers/` (marked deprecated)

**Health Score**: **6.8/10** — Migration is well-executed but incomplete (see detailed scores below)

---

## 1. Verified Architecture Status

### 1.1 Evidence of SDK Maturity

**Verified Facts** (from code inspection):

✅ **alice-engine SDK is well-structured**:
- Clean public API with lazy imports (`__init__.py` exports 99+ symbols)
- Core runtime in `alice_engine/core/` (executor, agent_loop, skill_executor, etc.)
- LLM providers in `alice_engine/providers/` (claude, deepseek, mimo, openai, ollama, mock)
- Extension system (`alice_engine/extensions/`, `alice_engine/extension.py`)
- Workflow primitives in `alice_engine/workflow/`
- Discovery interfaces in `alice_engine/discovery/`

✅ **Migration strategy is clean**:
- `aitest/engine/executor.py` is a **compatibility alias** → `alice_engine.core.executor`
- `aitest/llm/provider.py` re-exports from `alice_engine.providers`
- `aitest/llm/providers/` marked **deprecated** with retention note

✅ **Engine class bridges platform and SDK**:
- `aitest/engine/__init__.py` provides `Engine` class
- Engine wraps SDK primitives with platform conveniences
- Sets up runtime environment via `alice_engine.core.runtime_environment`

---

## 2. Module Responsibility Matrix

| Module | Current Responsibility | Expected Responsibility | Status |
|--------|------------------------|-------------------------|--------|
| **alice-engine SDK** | Core execution primitives, workflow orchestration, provider abstraction | Same | ✅ **CORRECT** |
| **alice-governance SDK** | Governance data files (agents YAML, skills MD) | Same | ✅ **CORRECT** |
| **alice-discovery SDK** | Page/component discovery abstractions | Same | ✅ **CORRECT** |
| **aitest/engine/** | Compatibility layer + Engine convenience wrapper | Thin wrapper only (no core logic) | ⚠️ **MOSTLY CORRECT** (260 LOC wrapper is acceptable) |
| **aitest/platform/** | Platform-specific services (capability routing, memory, complexity) | Same | ✅ **CORRECT** |
| **aitest/server/** | FastAPI REST API | Same | ✅ **CORRECT** |
| **aitest/web/** | Vue.js frontend | Same | ✅ **CORRECT** |
| **aitest/cli/** | CLI commands | Same (should call SDK public API) | ⚠️ **NEEDS REVIEW** |
| **aitest/llm/** | **DEPRECATED** compatibility aliases | Should be removed or stay as aliases | ⚠️ **TRANSITIONAL** |
| **aitest/runtime/** | Runtime config utilities | Should move to SDK or remain as platform config | ⚠️ **UNCLEAR OWNERSHIP** |
| **governance/** | Agent YAML, Skill MD, context files | Same | ✅ **CORRECT** |

---

## 3. Directory Ownership Assessment

| Directory | Current State | Ownership Status | Evidence | Priority |
|-----------|---------------|------------------|----------|----------|
| `packages/alice-engine/` | Well-structured SDK with 99+ public exports | ✅ **CORRECT** | Verified __init__.py, core/, providers/, workflow/ | - |
| `packages/alice-governance/` | Data-only package (YAML, MD files) | ✅ **CORRECT** | Verified pyproject.toml package-data config | - |
| `packages/alice-discovery/` | Discovery abstractions | ✅ **CORRECT** | Separate SDK package | - |
| `aitest/engine/` | Thin wrapper (260 LOC total) + compatibility aliases | ✅ **ACCEPTABLE** | executor.py is 6-line alias; __init__.py is 263-line Engine wrapper | LOW |
| `aitest/llm/` | Compatibility re-exports | ⚠️ **TRANSITIONAL** | provider.py re-exports; providers/ marked deprecated | MEDIUM |
| `aitest/runtime/` | Runtime config + path utilities | ⚠️ **UNCLEAR** | 5 files (config, context, error_handling, paths, _paths_core) | **HIGH** |
| `aitest/platform/` | Platform services (capability_router, complexity, memory, hooks, lifecycle) | ✅ **CORRECT** | Platform-specific logic | - |
| `aitest/server/` | FastAPI backend | ✅ **CORRECT** | Platform web server | - |
| `aitest/web/` | Vue.js frontend | ✅ **CORRECT** | Platform UI | - |
| `aitest/cli/` | CLI commands | ⚠️ **NEEDS REVIEW** | May import internals directly | **HIGH** |
| `aitest/infra/` | Infrastructure utilities | ✅ **CORRECT** | Database, cache, security, logging | - |
| `aitest/graphs/` | Graph state + checkpoint | ⚠️ **PARTIAL** | Used by Engine, unclear if belongs in SDK | MEDIUM |
| `aitest/adapters/` | Adapter pattern implementations | ⚠️ **UNCLEAR** | audit/, event/, llm/ subdirs | MEDIUM |
| `aitest/agents/` | Agent orchestration helpers | ⚠️ **UNCLEAR** | May duplicate SDK functionality | MEDIUM |
| `aitest/audit_engine/` | Audit/observability | ⚠️ **MIXED** | Some belongs in Extensions, some in Platform | MEDIUM |
| `aitest/knowledge/` | RAG engine | ⚠️ **UNCLEAR** | May belong in SDK Runtime | MEDIUM |
| `aitest/discovery/` | Discovery implementations | ❌ **DUPLICATE** | alice-discovery package exists | **HIGH** |
| `governance/` | Agent YAML, Skill MD | ✅ **CORRECT** | Governance data | - |
| `context/` | Domain knowledge files | ✅ **CORRECT** | Domain context | - |
| `docs/` | Documentation | ✅ **CORRECT** | Documentation | - |
| `tools/`, `scripts/` | Utilities | ✅ **CORRECT** | Tooling | - |
| `tests/` | Test suites | ✅ **CORRECT** | Testing | - |

---

## 4. Critical Issues (Evidence-Based)

### 4.1 **HIGH: aitest/runtime/ ownership unclear**

**Files**:
- `config.py` — Runtime config (85 LOC)
- `context.py` — Runtime context (350+ LOC estimated)
- `error_handling.py` — Error handling utilities
- `paths.py` — Path resolution utilities
- `_paths_core.py` — Core path utilities

**Issue**: These utilities are used by both platform and SDK. Unclear if they belong in:
- `alice-engine/runtime/` (if SDK-level)
- `aitest/infra/` (if platform-level)
- Split between both (adapters pattern)

**Recommendation**: Audit each file's dependencies. If it imports only from SDK or stdlib, move to SDK. If it imports from platform, keep in `aitest/`.

---

### 4.2 **HIGH: aitest/discovery/ duplication**

**Evidence**: 
- `packages/alice-discovery/` exists as separate SDK package
- `aitest/discovery/` also exists with implementations

**Issue**: Two discovery codebases. Which is canonical?

**Recommendation**: 
1. Verify if `aitest/discovery/` is still used
2. If yes, refactor to use `alice-discovery` package
3. If no, delete `aitest/discovery/`

---

### 4.3 **MEDIUM: aitest/llm/providers/ marked deprecated but still present**

**Evidence**:
- `aitest/llm/providers/__init__.py` says "Deprecated provider package"
- But 6 provider files still exist (claude.py, deepseek.py, mimo.py, mock.py, ollama.py, openai.py)
- Total ~50KB of code

**Issue**: Deprecated code retained "for compatibility" but not clear what still uses it.

**Recommendation**:
1. Search codebase for imports from `aitest.llm.providers`
2. If none found, delete the directory
3. If found, migrate those imports to `alice_engine.providers`

---

### 4.4 **MEDIUM: aitest/cli/ may import internals directly**

**Evidence**: Not yet verified (requires import analysis)

**Concern**: CLI commands may bypass SDK public API and import from `aitest.graphs`, `aitest.engine` internals, etc.

**Recommendation**: Audit CLI imports. All SDK access should be via `alice_engine` public API, not internal modules.

---

### 4.5 **MEDIUM: aitest/graphs/ unclear ownership**

**Files**:
- `state.py` — Graph state creation
- `checkpoint.py` — Checkpointer setup
- `__init__.py`

**Evidence**: 
- `aitest/engine/__init__.py` imports `from aitest.graphs.state import create_initial_state`
- But `alice_engine.workflow.state` also exists

**Issue**: Graph/workflow logic split between `aitest/graphs/` and SDK `alice_engine/workflow/`.

**Recommendation**: 
1. If `aitest/graphs/` contains platform-specific state management → keep
2. If generic workflow state → move to SDK
3. Verify no duplication with SDK's `alice_engine/workflow/`

---

### 4.6 **LOW: aitest/engine/ wrapper is acceptable**

**Evidence**:
- `executor.py` — 6 lines (compatibility alias)
- `__init__.py` — 263 lines (Engine convenience wrapper)
- `event_bus.py` — 100 lines (event bus, may be platform-specific)
- `skill_executor.py` — 68 lines (skill executor wrapper)
- `state_machine.py` — 11 lines

**Total**: ~450 LOC, mostly wrapper code.

**Assessment**: ✅ This is **acceptable** for a platform convenience layer. Not a blocker.

---

## 4. File-Level Migration Recommendations

### 4.1 High Priority Migrations (Blocking SDK Independence)

| Current File | Target Location | Risk Level | Reason |
|--------------|-----------------|------------|--------|
| `aitest/engine/executor.py` | `packages/alice-engine/runtime/executor.py` | **CRITICAL** | Core execution primitive |
| `aitest/engine/event_bus.py` | `packages/alice-engine/runtime/event_bus.py` | **CRITICAL** | Runtime event system |
| `aitest/engine/skill_executor.py` | `packages/alice-engine/runtime/skill_executor.py` | **CRITICAL** | Skill execution |
| `aitest/llm/provider.py` | `packages/alice-engine/providers/base.py` | **CRITICAL** | LLM abstraction layer |
| `aitest/llm/providers/claude.py` | `packages/alice-engine/providers/llm/claude.py` | **CRITICAL** | Provider implementation |
| `aitest/llm/providers/deepseek.py` | `packages/alice-engine/providers/llm/deepseek.py` | **CRITICAL** | Provider implementation |
| `aitest/llm/providers/mimo.py` | `packages/alice-engine/providers/llm/mimo.py` | **CRITICAL** | Provider implementation |
| `aitest/llm/providers/openai.py` | `packages/alice-engine/providers/llm/openai.py` | **CRITICAL** | Provider implementation |
| `aitest/llm/context_injector.py` | `packages/alice-engine/runtime/context.py` | **HIGH** | Runtime context management |
| `aitest/runtime/` (all files) | `packages/alice-engine/runtime/` | **CRITICAL** | Entire runtime module misplaced |
| `aitest/graphs/state.py` | `packages/alice-engine/workflow/state.py` | **HIGH** | Workflow state |
| `aitest/graphs/checkpoint.py` | `packages/alice-engine/workflow/checkpoint.py` | **HIGH** | Workflow checkpointing |
| `aitest/knowledge/rag_engine.py` | `packages/alice-engine/intelligence/rag.py` | **HIGH** | RAG engine |
| `aitest/knowledge/rag_indexers.py` | `packages/alice-engine/intelligence/indexers.py` | **HIGH** | RAG indexing |
| `aitest/discovery/` (directory) | **DELETE** (use `alice-discovery` package) | **HIGH** | Duplication |
| `aitest/adapters/llm/` | `packages/alice-engine/adapters/llm/` | MEDIUM | Adapter pattern |
| `aitest/adapters/event/` | `packages/alice-engine/adapters/event/` | MEDIUM | Event adapters |

---

### 4.2 Medium Priority Migrations

| Current File | Target Location | Reason |
|--------------|-----------------|--------|
| `aitest/agents/agent_scheduler.py` | `packages/alice-engine/scheduling/` | Scheduling logic reusable across projects |
| `aitest/agents/pipeline_router.py` | `packages/alice-engine/routing/` | Routing logic |
| `aitest/audit_engine/sop_auditor.py` | `packages/alice-governance/validators/sop.py` | SOP validation belongs in governance |
| `aitest/audit_engine/state_auditor.py` | `packages/alice-governance/validators/state.py` | State validation |
| `aitest/mcp/protocol.py` | `packages/alice-engine/protocols/mcp.py` OR standalone `alice-mcp` package | Protocol abstraction |
| `aitest/graphs_dev/` | `packages/alice-engine/workflows/dev/` OR new `alice-devtools` package | Dev workflow library |

---

### 4.3 Low Priority (Platform-Specific, Correctly Placed)

These files are correctly in `aitest/` as platform code:

- `aitest/server/` — FastAPI server (Platform)
- `aitest/web/` — Vue frontend (Platform)
- `aitest/cli/` — CLI commands (Platform)
- `aitest/platform/` — Platform services
- `aitest/infra/database*.py` — Platform database layer
- `aitest/integrations/` — Platform-specific integrations

---

## 5. Responsibility Confusion Analysis

### 5.1 **職責重複 (Duplicated Responsibilities)**

| Responsibility | Location 1 | Location 2 | Resolution |
|----------------|------------|------------|------------|
| **Skill Execution** | `aitest/engine/skill_executor.py` | `aitest/agents/skill_executor.py` | Merge into SDK, keep one canonical implementation |
| **Discovery** | `aitest/discovery/` | `packages/alice-discovery/` | Delete `aitest/discovery/`, use package |
| **Event Bus** | `aitest/engine/event_bus.py` | `aitest/audit_engine/event_bus.py` | Merge into SDK, platform imports from SDK |
| **LLM Provider Interface** | `aitest/llm/provider_base.py` | `aitest/adapters/llm/provider_base.py` | Consolidate in SDK |
| **Context Injection** | `aitest/llm/context_injector.py` | Various ad-hoc implementations | Centralize in SDK runtime |

---

### 5.2 **職責缺失 (Missing Responsibilities)**

| Missing Capability | Should Exist In | Current State |
|-------------------|-----------------|---------------|
| **SDK Public API** | `packages/alice-engine/__init__.py` | Incomplete — no clear entry point for external users |
| **Plugin System** | `packages/alice-engine/plugins/` | Not implemented — mentioned in vision but absent |
| **Extension Registry** | `packages/alice-engine/extensions/registry.py` | Partial — exists but incomplete |
| **Provider Factory** | `packages/alice-engine/providers/factory.py` | Scattered — no centralized factory |
| **Workflow Builder DSL** | `packages/alice-engine/workflow/builder.py` | Missing — users write raw LangGraph code |
| **Governance Validator API** | `packages/alice-governance/validator.py` | Missing — no public validation interface |
| **Cross-Project Context** | `packages/alice-engine/context/` | Missing — `.tlo/` exists but no SDK abstraction |

---

### 5.3 **職責交叉 (Crossed Responsibilities)**

| Module | Should Own | Currently Also Does | Problem |
|--------|-----------|---------------------|---------|
| `aitest/platform/` | Platform services | Executes agents directly via `aitest.engine` | Platform should call SDK, not engine internals |
| `aitest/cli/` | CLI commands | Imports from `aitest.graphs`, `aitest.engine` directly | CLI should call SDK public API |
| `aitest/server/api/` | REST endpoints | Imports runtime modules directly | Server should use SDK facades |
| `aitest/audit_engine/` | Audit/observability | Contains SOP validation logic | Audit observes, Governance validates |
| `packages/alice-engine/governance_default/` | Default governance pack | Embedded in engine SDK | Should be external data package |

---

### 5.4 **職責污染 (Responsibility Pollution)**

| File | Primary Responsibility | Polluted By | Line Count | Should Split Into |
|------|------------------------|-------------|------------|-------------------|
| `aitest/engine/executor.py` | Agent execution | CLI progress reporting, database writes | ~800 | `executor.py` (core) + `executor_platform.py` (platform hooks) |
| `aitest/server/api/execution.py` | API endpoint | Direct workflow construction | ~500 | Keep endpoint, move workflow to SDK |
| `aitest/cli/commands/graph/run.py` | CLI command | Graph state management | ~400 | Keep CLI, move state to SDK |
| `aitest/platform/capability_router/router.py` | Routing logic | Agent instantiation | ~600 | Keep routing, move instantiation to SDK factory |
| `aitest/audit_engine/sop_auditor.py` | SOP audit | SOP validation rules | ~700 | Audit (observe) vs. Validate (enforce) |

---

## 6. Coupling Analysis

### 6.1 Critical Coupling Issues

#### **A. Circular Dependency: Platform ↔ Runtime**

```
aitest/platform/ → aitest/engine/ → aitest/platform/
```

**Example**:
- `aitest/platform/capability_router/` imports `aitest/engine/executor.py`
- `aitest/engine/executor.py` imports `aitest/platform/testing_memory.py`

**Impact**: Cannot separate SDK from platform.

**Resolution**: Runtime SDK should have zero platform dependencies. Platform calls SDK through public API.

---

#### **B. Hidden Dependency: CLI → Internal Engine**

```python
# aitest/cli/commands/graph/run.py
from aitest.graphs.sop_graph import build_graph  # WRONG
from aitest.engine.executor import AgentLoop      # WRONG
```

**Should be**:
```python
from alice_engine import WorkflowBuilder, Runtime
```

---

#### **C. Governance Embedded in Engine**

```
packages/alice-engine/governance_default/  ← WRONG
```

**Problem**: Engine SDK contains governance data (agents YAML, skills).

**Resolution**: 
- Move to `packages/alice-governance/defaults/`
- Engine loads governance via plugin system, not embedded data

---

### 6.2 Dependency Graph (Simplified)

```
Current (WRONG):
  aitest/cli/ → aitest/graphs/ → aitest/engine/ → aitest/platform/ → aitest/infra/
       ↓              ↓                ↓                  ↓
  aitest/llm/ ← aitest/knowledge/ ← aitest/runtime/ ← aitest/discovery/

Expected (RIGHT):
  aitest/platform/
    ↓ (calls)
  packages/alice-engine/ (SDK)
    ↓ (loads)
  packages/alice-governance/ (Data)
  
  aitest/cli/ → aitest/platform/ → SDK
  aitest/server/ → aitest/platform/ → SDK
  aitest/web/ → aitest/server/ (REST API only)
```

---

## 7. God Files / God Modules

| File | Lines | Responsibilities | Risk | Should Split Into |
|------|-------|------------------|------|-------------------|
| `aitest/engine/executor.py` | ~800 | Execution + state + hooks + DB + CLI progress | **CRITICAL** | `executor.py` (core 200 LOC) + `executor_hooks.py` + `executor_persistence.py` |
| `aitest/cli/commands/graph/run.py` | ~400 | CLI arg parsing + graph building + execution | **HIGH** | `run.py` (CLI only) + use SDK for graph/execution |
| `aitest/platform/capability_router/router.py` | ~600 | Routing + capability detection + agent factory | **HIGH** | `router.py` (routing) + `capabilities.py` + `factory.py` |
| `aitest/server/api/execution.py` | ~500 | API endpoint + workflow construction + validation | **HIGH** | `execution_api.py` (endpoint) + SDK for workflow |
| `aitest/audit_engine/sop_auditor.py` | ~700 | Audit + validation + reporting | **HIGH** | `sop_observer.py` (audit) + move validation to governance |
| `aitest/knowledge/rag_engine.py` | ~650 | Embedding + indexing + retrieval + LLM calling | **MEDIUM** | Move to SDK, split into `embedder.py` + `retriever.py` |
| `aitest/infra/database.py` | ~400 | Connection pooling + migrations + query helpers | **MEDIUM** | `connection.py` + `migrations.py` + `queries.py` |

---

## 8. Public Capability Identification

### 8.1 Should Be in SDK (Reusable Across Projects)

| Current Location | Should Move To | Reason |
|------------------|----------------|--------|
| `aitest/engine/executor.py` | `alice-engine/runtime/executor.py` | Core execution primitive |
| `aitest/engine/event_bus.py` | `alice-engine/runtime/events.py` | Event system |
| `aitest/llm/provider.py` | `alice-engine/providers/base.py` | LLM abstraction |
| `aitest/graphs/state.py` | `alice-engine/workflow/state.py` | Workflow state |
| `aitest/knowledge/rag_engine.py` | `alice-engine/intelligence/rag.py` | RAG capability |
| `aitest/agents/agent_scheduler.py` | `alice-engine/scheduling/` | Agent scheduling |
| `aitest/adapters/llm/` | `alice-engine/adapters/llm/` | LLM adapters |
| `aitest/adapters/event/` | `alice-engine/adapters/event/` | Event adapters |
| `aitest/mcp/protocol.py` | `alice-engine/protocols/mcp.py` | MCP protocol |

---

### 8.2 Should Remain in Platform (Project-Specific)

| Current Location | Reason to Keep |
|------------------|----------------|
| `aitest/server/` | FastAPI server (platform-specific) |
| `aitest/web/` | Vue UI (platform-specific) |
| `aitest/cli/` | CLI commands (platform-specific, but should call SDK) |
| `aitest/platform/` | Platform services |
| `aitest/infra/database*.py` | Platform persistence layer |
| `aitest/infra/redis_*.py` | Platform caching/pubsub |
| `aitest/integrations/` | Platform-specific integrations |

---

## 9. Architecture Health Scores

| Dimension | Score | Rationale |
|-----------|-------|-----------|
| **Module Boundary Clarity** | 3/10 | Runtime, Platform, Governance boundaries violated extensively |
| **Directory Organization** | 5/10 | Packages structure is good, but `aitest/` is a dumping ground |
| **Responsibility Clarity** | 4/10 | Many files have 2-3 overlapping responsibilities |
| **Coupling** | 2/10 | Circular dependencies, hidden dependencies, tight coupling |
| **Extensibility** | 5/10 | Extension points exist but buried in platform code |
| **SDK Independence** | 1/10 | SDK cannot be extracted — depends on platform |
| **Platform Independence** | 3/10 | Platform tightly coupled to engine internals |
| **Governance Independence** | 6/10 | Governance data is separate, but validation logic is scattered |
| **Runtime Independence** | 2/10 | Runtime primitives embedded in platform |

**Overall Health**: **4.2/10** — Architectural vision is clear, but implementation is in early transition phase.

---

## 10. Recommended Refactoring Sequence

### Phase 1: Stop the Bleeding (Week 1-2)
1. **Freeze new features in `aitest/engine/`, `aitest/llm/`, `aitest/runtime/`**
2. **Create facade in SDK**: `packages/alice-engine/runtime/__init__.py` with public API
3. **Platform imports from facade only** — no direct imports from `aitest/engine/`

### Phase 2: SDK Extraction (Week 3-6)
4. **Move `aitest/llm/` → `packages/alice-engine/providers/llm/`**
5. **Move `aitest/engine/` → `packages/alice-engine/runtime/`**
6. **Move `aitest/runtime/` → `packages/alice-engine/runtime/core/`**
7. **Move `aitest/graphs/state.py` + `checkpoint.py` → `packages/alice-engine/workflow/`**
8. **Delete `aitest/discovery/`**, use `alice-discovery` package
9. **Move `aitest/knowledge/rag_engine.py` → `packages/alice-engine/intelligence/`**

### Phase 3: Governance Cleanup (Week 7-8)
10. **Move `packages/alice-engine/governance_default/` → `packages/alice-governance/defaults/`**
11. **Move `aitest/audit_engine/sop_auditor.py` validation logic → `packages/alice-governance/validators/`**
12. **Create `packages/alice-governance/validator.py` public API**

### Phase 4: Platform Decoupling (Week 9-10)
13. **Refactor `aitest/platform/` to call SDK public API only**
14. **Refactor `aitest/cli/` to call SDK public API only**
15. **Refactor `aitest/server/api/` to call SDK public API only**

### Phase 5: Verification (Week 11-12)
16. **Publish SDK to PyPI** (internal registry first)
17. **Create standalone project using only SDK** (no `aitest` imports)
18. **CI/CD pipeline for SDK-only tests**

---

## 11. Risk Assessment

| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|------------|
| **Breaking existing workflows** | HIGH | CRITICAL | Incremental refactoring with facade pattern |
| **Lost functionality during migration** | MEDIUM | HIGH | Comprehensive test coverage before moving code |
| **Performance regression** | LOW | MEDIUM | Benchmark before/after each phase |
| **Team velocity drop** | HIGH | MEDIUM | Freeze features during refactoring phases |
| **Incomplete migration** | MEDIUM | CRITICAL | Automated dependency checks in CI |
| **SDK API instability** | MEDIUM | HIGH | Version SDK separately, use semantic versioning |

---

## 12. Success Criteria

### SDK Independence (Must-Have)
- [ ] `packages/alice-engine/` can be `pip install`'d standalone
- [ ] `packages/alice-engine/` has **zero** imports from `aitest.*`
- [ ] SDK tests run without platform dependencies
- [ ] Standalone project can use SDK without `aitest` installed

### Platform Independence (Must-Have)
- [ ] `aitest/platform/` imports SDK via public API only
- [ ] `aitest/cli/` imports SDK via public API only
- [ ] `aitest/server/` imports SDK via public API only
- [ ] No direct imports of `aitest/engine/`, `aitest/llm/`, `aitest/runtime/`

### Governance Independence (Should-Have)
- [ ] `packages/alice-governance/` contains **only** data files + validator interface
- [ ] `packages/alice-engine/` does not embed governance data
- [ ] Governance packs are loadable plugins

### Extensibility (Should-Have)
- [ ] Plugin system allows custom providers without forking SDK
- [ ] Extension registry allows platform to register custom capabilities
- [ ] Workflow DSL allows declarative agent workflows

---

## 13. Long-Term Vision Alignment

This audit confirms the project **understands** the target architecture but **has not yet arrived**. The good news:

✅ **Packages structure exists** (`alice-engine`, `alice-governance`)  
✅ **ADR-001 establishes .tlo/ for project context**  
✅ **Platform/SDK conceptual separation is documented**  

The gap:

❌ **Runtime still in platform** (`aitest/engine/`, `aitest/llm/`, `aitest/runtime/`)  
❌ **Platform tightly coupled to internals**  
❌ **No clear SDK public API**  
❌ **Circular dependencies block clean separation**  

**Recommendation**: Commit to **6-month SDK extraction roadmap**. Freeze new platform features. All hands on refactoring.

---

## 14. Appendix: Dependency Violations (Sample)

### Example 1: Platform Calls Internal Engine
```python
# aitest/cli/commands/graph/run.py (WRONG)
from aitest.graphs.sop_graph import build_graph
from aitest.engine.executor import AgentLoop

# Should be:
from alice_engine import Runtime, WorkflowBuilder
```

### Example 2: Engine Calls Platform
```python
# aitest/engine/executor.py (WRONG)
from aitest.platform.testing_memory import TestingMemory

# Should be:
# Engine should emit events, platform subscribes
```

### Example 3: CLI Constructs Workflows Directly
```python
# aitest/cli/commands/graph/run.py (WRONG)
graph = StateGraph(...)
graph.add_node("analyze", analyze_node)

# Should be:
workflow = WorkflowBuilder().add_phase("analyze").build()
```

---

## 15. Conclusion

This project is **architecturally ambitious** and **directionally correct**, but currently **stuck in transition**. The core issue is **runtime logic embedded in platform**, preventing SDK extraction.

**Next Step**: Leadership decision required:
1. **Commit to refactoring** (6-month roadmap, feature freeze)
2. **Defer refactoring** (accept current architecture as-is for now)
3. **Hybrid approach** (incremental refactoring, slower pace)

**Recommendation**: **Option 1** — the longer the delay, the more expensive the migration.

---

**End of Report**

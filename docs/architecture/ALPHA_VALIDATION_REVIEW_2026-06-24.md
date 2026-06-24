# Alpha Validation Review — Alice Platform Pre-Phase-3

> **Review type:** Architecture + API + E2E + Design Gap Analysis
> **Date:** 2026-06-24
> **Scope:** v1.x Runtime (frozen) + v2.0 Platform Foundation + v2.1 Workspace Isolation
> **Goal:** Validate readiness before Phase 3 (Webhooks, Audit, Billing)

---

## 0. Executive Summary

**Architecture: 8.8/10. Implementation: 7.5/10. Phase 3 Readiness: 8/10 — needs v2.2 Platform Runtime Foundation before Webhook/Billing.**

This is a healthy architecture. The missing piece is a Platform Runtime layer between API and Runtime — not a fix, but the next evolutionary step. Once built, Webhooks, Audit, Billing, Timeline, and Metrics become event consumers, not bespoke integrations.

| Dimension | Score | Note |
|-----------|-------|------|
| Architecture Design | 8.8/10 | Layer boundaries correct, Constitution sound, ExecutionContext well-defined |
| Implementation Maturity | 7.5/10 | v2.0/v2.1 functional, auth needs wiring, Platform Runtime layer missing |
| API Design | 5.5/10 | Auth dual-system, no versioning plan; API surface otherwise clean |
| Test Coverage | 4.0/10 | Zero integration tests for v2.0/v2.1 Platform APIs |
| Security | 4.5/10 | Auth middleware exists but not wired to org keys; CORS fix trivial |
| Platform Resource Model | 3.5/10 | ExecutionRequest + Run + RunEvent missing — but design is clear, just not built |
| Phase 3 Readiness | 8.0/10 | GO — after v2.2 Platform Runtime Foundation is in place |

**Verdict:** GO. Start v2.2 (Platform Runtime Foundation) immediately. Webhooks and Billing in v2.3/v2.4 as event consumers on top of RunEvent.

**Key findings:**
1. Auth is a functional bug — org API keys not wired to middleware. Fix: 2h.
2. **Missing Platform Runtime layer:** ExecutionService + ExecutionRequest + Run + RunEvent + EventBus. This is v2.2.
3. Once v2.2 exists, Webhooks = subscribe(RunEvent), Audit = subscribe(RunEvent), Billing = subscribe(cost.recorded).
4. Quota at Platform layer (ExecutionService), not Runtime. Tenant stays internal.
5. API versioning, response envelope, pagination → defer to v2.5. Don't block.

---

## 1. Architecture Layer Compliance

### 1.1 Principle Verification

```
Rule: Platform parses identity → ExecutionContext → Runtime.
      Runtime never imports Organization.
```

| Check | Status | Evidence |
|-------|--------|----------|
| `runtime.py` imports `organization.py`? | ✅ PASS | Zero imports |
| `ExecutionContext` excludes Organization? | ✅ PASS | Only `workspace_id, user_id, scopes, org_id` |
| `WorkspaceManager.make_context()` resolves identity? | ✅ PASS | `workspace.py:162-186` |
| Runtime receives only ExecutionContext? | ⚠️ PARTIAL | No enforcement — Runtime accepts `context` as optional parameter only |

**Finding 1 (Low — P3):** ExecutionContext is defined but **never wired to Runtime execution**. `BrowserRuntime.__init__` takes `base_url, headless, use_vision, max_steps, provider, model, driver_factory` — no `context` parameter. The isolation contract exists in code but the object is never consumed.

Two valid wiring approaches (constructor injection NOT required):
- **Method injection:** `BrowserRuntime.execute(action, context=ctx)` — Runtime receives context per-call, never stores it
- **Caller-side check:** `ExecutionService` checks `ctx.require_scope("execute")` before calling `Runtime.execute()` — Runtime never sees context at all

```python
# platform/workspace.py:36 — ExecutionContext is defined
# platform/runtime.py:121 — BrowserRuntime.__init__ does NOT accept ExecutionContext
# Gap: make_context() is called by API but result is never fed to any execution path
# Fix: wire via method parameter OR caller-side guard, NOT constructor injection
```

**Design principle:** Context = call-scoped, not runtime-scoped. Constructor injection would wrongly tie context lifetime to Runtime lifetime. The right fix is passing it at call time or checking before the call — both preserve "Runtime never imports Organization."

### 1.2 Cross-Layer Import Health

- 28 binary circular dependencies detected — all resolved via lazy imports, but indicate tight coupling
- **Worst offender:** `infra/cli/__init__.py` (~1231 lines) imports from every layer
- **Second worst:** `agent_runner.py` couples to `audit_engine`, `infra`, `llm`, `platform`, `testing`
- `platform/capability_router/providers/` creates `platform → discovery → platform` and `platform → mcp → platform` cycles

**Finding 2 (Technical Debt — P4, do not block Phase 3):** 28 circular deps exist, all resolved via lazy imports. Survivable but indicate tight coupling. Defer `aitest/protocols/` extraction to Phase 4+ — only address if circular imports cause actual breakage or prevent unit testing.

### 1.3 Constitution Compliance (CONSTITUTION.md)

| Principle | Status |
|-----------|--------|
| P1: Platform doesn't import business modules | ✅ PASS |
| P2: Governance is Python-free | ✅ PASS |
| P3: Agent definitions are declarative | ✅ PASS |
| P4: Capability > Tool | ✅ PASS |
| P5: Three-question gate | ⚠️ No evidence of enforcement |
| P6: Extension Point first | ✅ Plugin system exists |

---

## 2. API Review

### 2.1 Version Chaos

Three different version numbers in the codebase:

| Location | Version |
|----------|---------|
| `server/main.py` FastAPI title | `0.4.0` |
| `server/main.py` root endpoint | `1.0.0` |
| `server/api/platform.py` tag | `Platform v2.0` |
| `server/api/workspace.py` tag | `Workspace v2.1` |

**Finding 3 (Critical):** No API versioning strategy. URLs have no version prefix (`/api/platform/orgs` not `/api/v2/orgs`). When Phase 3 changes these APIs, existing clients break. Must decide: URL-path versioning (`/v1/`, `/v2/`) or header-based. Document in CONSTITUTION.

### 2.2 Auth — Dual System, Neither Complete

**System A: `auth.py`**
- Single `AITEST_API_KEY` env var
- Bearer token middleware
- No scopes, no multi-key, no org context
- Disabled when env var unset → **entire API is open**

**System B: `organization.py`**
- Full API key management: create, list, revoke, scopes
- SHA-256 hashed keys
- Per-org scoping
- **Never called by auth middleware** — dead code for authentication purposes

```python
# auth.py:47 — only checks AITEST_API_KEY env var
# organization.py:165 — validate_api_key() exists but never wired to middleware
# Result: API keys created via /api/platform/orgs/:id/keys CANNOT authenticate
```

**Finding 4 (Critical):** Auth is broken by design. Organization-scoped API keys have no path to authenticate HTTP requests. Before Webhooks (which need to authenticate callers) and Billing (which needs per-org usage tracking), this must be unified.

**Fix:** `auth_middleware` must fall through to `OrganizationManager.validate_api_key()` when `AITEST_API_KEY` is unset or doesn't match. Then set `request.state.org_id` and `request.state.scopes` for downstream handlers.

### 2.3 API Response Format Inconsistency

```
POST /api/platform/orgs           → {"status": "created", "org": {...}}
GET  /api/platform/orgs           → {"orgs": [...]}
POST /api/platform/orgs/:id/keys  → {"status": "created", "key_id": ..., "api_key": ...}
GET  /api/platform/orgs/:id/keys  → {"keys": [...]}
POST /api/platform/.../workspaces → {"status": "created", "workspace": {...}}
GET  /api/platform/.../workspaces → {"org_id": ..., "workspaces": [...]}
```

No envelope standard. Some wrap in `{status, data}`, some return data directly, some add metadata fields at root level.

**Finding 5 (Medium):** Define API response envelope. Recommend:

```json
{
  "data": { ... },
  "meta": { "page": 1, "total": 50 },
  "error": null
}
```

Or adopt JSON:API. Decision needed before Phase 3 adds more endpoints.

### 2.4 Error Handling

Two patterns coexist:
1. `raise HTTPException(409, str(e))` — proper, returns 4xx/5xx
2. `return {"error": str(e)[:300]}` with 200 OK — masks errors as success

Pattern 2 appears in all `/api/audit/*`, `/api/kpi/*`, `/api/trace/*`, `/api/timeline/*` endpoints.

**Finding 6 (High):** `/api/audit/*` and `/api/kpi/*` endpoints return 200 with `{"error": "..."}` on failure. Monitoring systems see 200 and assume success. All error responses must use proper HTTP status codes.

### 2.5 Missing API Features

| Feature | Status | Needed for Phase 3 |
|---------|--------|--------------------|
| Pagination | ❌ None | Audit log listing |
| Request IDs | ❌ None | Tracing webhook deliveries |
| Rate limiting (distributed) | ⚠️ In-memory only | Billing enforcement |
| Input validation | ⚠️ Basic Pydantic | Webhook payload validation |
| API versioning | ❌ None | All Phase 3 endpoints |
| OpenAPI tags organization | ⚠️ Mixed | Developer experience |

---

## 3. E2E Testing Assessment

### 3.1 Current State

```
aitest/tests/             — 94 unit/logic tests, 92 pass, 2 skip
aitest/web/e2e/           — 1 smoke spec (18 tests), all UI navigation
Zero tests for:
  - Organization CRUD API
  - Workspace CRUD API
  - API Key create/validate/revoke
  - Auth middleware (valid key, invalid key, missing key, disabled)
  - Quota enforcement
  - ExecutionContext scoping
  - Webhook endpoint
  - Rate limiter
```

### 3.2 Test Quality Issues

- `test_tenant.py` tests `TenantCapacityError` raising but never tests `BrowserRuntime` actually checking capacity
- `test_sop_routing.py` has 2 skipped tests (`test_preflight_discovers_pages`, `test_preflight_recommends_mode`) — no reason documented
- No test fixtures for Organization/Workspace setup
- No conftest.py with API client fixture
- E2E smoke tests require both frontend (port 15173) and backend (port 8000) running — no single command

**Finding 7 (Critical):** Zero integration tests for v2.0 and v2.1 Platform APIs. The code that Phase 3 will build upon (Organization, Workspace, API Keys, ExecutionContext) has no test coverage. Any refactoring for Phase 3 risks silent breakage.

### 3.3 Minimum Test Bar Before Phase 3

```
Required new tests (minimum):
  test_organization_api.py     — CRUD + member management + API keys (8 tests)
  test_workspace_api.py        — CRUD + members + quotas + context (8 tests)
  test_auth_middleware.py      — key validation + exempt paths + disabled mode (6 tests)
  test_execution_context.py    — scope checking + PermissionError (4 tests)
  test_quota_enforcement.py    — capacity check + release + token recording (5 tests)
  test_webhook_auth.py         — signature verification (when implemented) (3 tests)
```

---

## 4. Design Issues — Pre-Phase-3 Blockers

### 4.1 Critical: Quota System Not Wired

```
Data model:  ✅ Workspace.quotas = {max_runs_per_day, max_tokens_per_run, max_storage_mb}
API:         ✅ GET/PUT /api/platform/orgs/:id/workspaces/:id/quotas
Enforcement: ❌ Nowhere. No quota check before execution.
```

**Finding 8 (Critical):** Quota CRUD exists but zero enforcement. Any user can exceed any quota. Before Billing (which charges based on usage), quotas must be enforced.

**Fix path (Platform-layer enforcement, NOT in Runtime):**
1. Create `ExecutionService` in Platform layer that wraps `Runtime.execute()`
2. `ExecutionService` checks quota via `ExecutionContext` BEFORE calling Runtime
3. Runtime stays clean — never imports Organization, never sees quotas
4. Tenant limits sync one-way from Workspace quotas: `Workspace.quotas → Tenant.limits`

```
Correct:
  ExecutionService.check_quota(ctx)  ← Platform layer
    ↓ (pass)
  Runtime.execute(action)            ← Runtime layer (quota-blind)

Wrong:
  BrowserRuntime.execute(action)     ← would need to import Workspace/Quota
    ↓ self._check_quota()            ← breaks "Runtime never imports Platform" rule
```

### 4.2 Critical: Tenant ↔ Organization ↔ Workspace — Dual Truth Source

Three overlapping concepts, three separate implementations:

| Concept | Module | DDD Role | Manages |
|---------|--------|----------|---------|
| Organization | `platform/organization.py` | Business aggregate root | Members, roles, API keys |
| Workspace | `platform/workspace.py` | Business entity | Members (workspace-level), quotas, ExecutionContext |
| Tenant | `platform/tenant.py` | Technical resource tracker | Resource limits, capacity, usage tracking |

**Tenant is a technical concept (CPU/memory/concurrency tracker), NOT a business concept.** It should never appear in the API. But currently:

- Creating a workspace doesn't create a tenant
- Setting workspace quotas doesn't update tenant limits
- Two separate truth sources for resource limits: `Workspace.quotas` and `Tenant.limits`

**Finding 9 (Critical):** Before Billing (per-org, per-workspace usage tracking), unify the truth source. NOT by merging the three models, but by establishing a one-way sync:

```
Proposed (revised):
  Organization     — business aggregate root, owns API keys + org-level members
  Workspace        — business entity, owns workspace-level members + quotas (SOURCE OF TRUTH)
  Tenant           — internal technical tracker (never exposed in API)
  
  Workspace.quotas ──one-way sync──→ Tenant.limits
  Tenant.usage     ──read-only──→ Workspace.usage_summary() (for API)
```

**What to NOT do:** Merge Tenant into Workspace. Tenant stays internal. Workspace stays the API surface. Sync is one-way: quota changes → tenant limits. Usage is read-only from tenant → workspace.

### 4.3 High: Webhook Infrastructure Is a Stub

Current webhook system (`server/api/webhooks.py`): single Jenkins POST endpoint. No:
- Webhook registration/management CRUD
- Per-webhook secret/signature verification (HMAC-SHA256)
- Retry with backoff
- Delivery logs / history
- Webhook event types catalog
- Filtering (subscribe to specific events)

**Finding 10 (High):** Phase 3 "Implement Webhooks" means building a webhook infrastructure, not just adding more POST endpoints to the existing stub. Requires design doc before implementation.

### 4.4 High: No Audit Trail for Platform Operations

Existing `audit_engine/` does governance auditing:
- State auditor (config drift detection)
- SOP auditor (compliance)
- Cost auditor (spike/bloat/trend)
- Safety auditor (P0)

Missing: **Operational audit trail** — "User X created workspace Y at time Z" or "API key K was used to trigger run R."

**Finding 11 (High):** Phase 3 "Implement Audit" should mean operational audit logging, not just governance auditing. Both are needed. Billing needs operational audit for invoicing. Webhooks need audit for delivery tracking.

### 4.5 Critical: ExecutionRequest + Run + Event — Missing Platform Execution Resources

**This is the largest design gap found.** Phase 3 features all revolve around execution lifecycle, but Alice has neither the *intent*, the *record*, nor the *event stream* as Platform resources.

Current model:
```
User/API → AgentLoop → BrowserRuntime.execute() → (nothing persisted at Platform level)
```

Execution exists only as a Runtime implementation detail. Three Platform resources are missing.

#### 4.5.1 ExecutionRequest — the Intent

A live entity representing the user's desire to execute. Has a lifecycle.

```
Created → Queued → Running → Completed
                            → Failed
                            → Cancelled
```

Simple is deliberate. Alice is not Kubernetes or Temporal. States can expand later if needed — don't pre-build `Validated`, `Dispatching`, `Scheduling`, `TimedOut` before they have a consumer.

```python
@dataclass
class ExecutionRequest:
    """Live entity — user's intent to execute."""
    request_id: str       # Platform-wide unique ID (UUID)
    workspace_id: str
    org_id: str
    triggered_by: str     # user_id or api_key_id
    trigger_type: str     # manual | webhook | schedule | api
    module: str
    pages: list[str]
    mode: str             # full | status | from_automation
    priority: int         # 0=normal, 1=high, 2=critical
    status: str           # created | queued | running | completed | failed | cancelled
    run_id: str | None    # Set when running → Run created
    created_at: str
    started_at: str | None
    completed_at: str | None
    retry_count: int
    max_retries: int
```

#### 4.5.2 Run — the Record

An immutable record of what actually happened. Created when ExecutionRequest is dispatched.

**Design principle: Run is immutable after completion.** Once `status ∈ {completed, failed, timed_out, cancelled}`, no field changes. Corrections create RunEvents, never mutate Run.

Why immutable:
- Billing: invoice based on Run — must not change after charge
- Audit: audit entry references Run — must be stable
- Replay: timeline replay reads Run — must be reproducible

```python
@dataclass
class Run:
    """Immutable record — what actually happened. Created on dispatch.
    
    Design principle: after status reaches terminal state, Run is frozen.
    Corrections append RunEvents, never mutate Run fields.
    """
    run_id: str           # Platform-wide unique ID (UUID)
    request_id: str       # Back-link to ExecutionRequest
    workspace_id: str
    org_id: str
    triggered_by: str
    status: str           # running | completed | failed | cancelled | timed_out
    created_at: str
    completed_at: str
    # Denormalized summary (populated once on completion, never updated):
    total_tokens: int
    total_cost: float
    agent_runs: int
    modules: list[str]
    artifacts: list[str]
```

#### 4.5.3 RunEvent — the Event Stream

**This is the third missing resource.** Phase 3 capabilities don't consume Run directly — they consume *events about* Run.

```
ExecutionRequested  → Webhook fires, Audit logs
ExecutionQueued     → Webhook fires
ExecutionStarted    → Webhook fires, Timeline shows
PhaseStarted        → Timeline shows, Webhook fires (optional)
PhaseCompleted      → Timeline shows
ArtifactCreated     → Webhook fires, Audit logs
RunCompleted        → Webhook fires, Billing triggers, Audit logs
RunFailed           → Webhook fires, Audit logs
CostRecorded        → Billing aggregates
```

Why Event is a Platform resource, not just an implementation detail:
- **Webhooks** don't poll Run — they subscribe to Event types
- **Audit** is an append-only log of Events
- **Timeline** is a filtered view of Events
- **Billing** aggregates CostRecorded events
- **Metrics** are computed from Event streams
- **Observability** dashboards consume Events

Without a unified Event model, each Phase 3 feature builds its own event ingestion — leading to N different event pipelines for the same underlying execution.

```python
@dataclass
class RunEvent:
    """Immutable event emitted during execution lifecycle.
    
    Downstream consumers (Webhooks, Audit, Timeline, Billing, Metrics)
    subscribe to typed events rather than polling Run state.
    """
    event_id: str         # Unique event ID (UUID)
    run_id: str           # Parent Run
    request_id: str       # Parent ExecutionRequest
    event_type: str       # execution.requested | execution.queued | execution.started |
                          # phase.started | phase.completed |
                          # artifact.created | evidence.captured |
                          # run.completed | run.failed | run.cancelled |
                          # cost.recorded
    timestamp: str
    data: dict            # Event-type-specific payload
```

#### 4.5.4 ExecutionService — the Missing Orchestration Layer

Currently API calls Runtime directly. No intermediary. This means:
- No quota check before execution
- No ExecutionRequest creation
- No queue integration
- No event emission
- No Run persistence

Phase 3 requires an orchestration layer:

```
API → ExecutionService → Queue → Runtime → run_store.save() → event_bus.publish()
                         ↓
                    Quota Check
                    Scope Check
                    ExecutionRequest created
```

ExecutionService responsibilities:
1. Validate request (quota, scope, module existence)
2. Create ExecutionRequest
3. Enqueue or dispatch
4. Create Run on dispatch
5. Emit events at lifecycle transitions
6. Persist Run on completion (immutable)

Runtime stays pure — it receives an ExecutionContext, executes, returns results. ExecutionService handles all Platform concerns.

**Implementation guidance — keep it simple:**

- **No Repository Pattern.** `run_store.py` with `save()/load()/list()`. Extract interface later if DB changes.
- **No heavy Event framework.** `event_bus.py` with `publish(event)` + `subscribe(callable)`. A `list[Callable]` is fine for v2.2. Don't introduce Kafka/Redis Stream/NATS/CloudEvent before you have >1 consumer.
- **No complex state machine.** ExecutionRequest states: `created|queued|running|completed|failed|cancelled`. Expand only when a real consumer needs it.

Alice is not Temporal. Don't build a workflow engine.

#### 4.5.5 Run References Capability, Not Runtime

**Run must never know which Runtime executed it.** BrowserRuntime, RemoteBrowserRuntime, future CLIRuntime — Run doesn't care.

Run records *what was used*, not *how it was executed*:

```python
@dataclass
class Run:
    ...
    capability: str       # "browser" | "cli" | "mcp" | "api"
    agent: str            # "automation-agent" | "execution-agent" | ...
    # NOT: runtime_type: str = "BrowserRuntime"  ← wrong
```

Why this matters:
- Future runtimes (CLI, Python, MCP, Remote CDP) can be added without changing Run model
- Billing can charge by capability type, not runtime implementation
- Audit can filter by capability without knowing runtime internals
- Runtime stays an engine detail — Capability is the Platform-level abstraction

**Finding 13 (Critical):** Three Platform resources missing — ExecutionRequest, Run, Event — plus the ExecutionService orchestration layer that manages their lifecycle:

```
Proposed:
  Organization → Workspace → ExecutionRequest → Run → RunEvent
                                  ↓                RunEvent → Webhook
                              capability            RunEvent → Audit
                              agent                 RunEvent → Timeline
                                                    RunEvent → Billing
                                                    RunEvent → Metrics
```

**Impact on Phase 3:**
- Webhooks: subscribe to RunEvent types, keyed by `run_id`
- Billing: aggregates `cost.recorded` events per org/workspace; charges against immutable Run
- Audit: append-only log of all RunEvents, linked to `request_id` (who) and `run_id` (what)
- Timeline: filtered, time-ordered view of RunEvents

**Without ExecutionRequest + Run + Event as resources, Phase 3 features have no anchor. Without ExecutionService, the Platform has no place to put these concerns.**

### 4.6 Medium: Runtime Selection Not Context-Aware

```python
# platform/context.py:187-200
def runtime(self, runtime_type: str = None) -> Runtime:
    rt_type = runtime_type or cfg.sut_type or "browser"
    if rt_type in ("web", "browser", "vue-hash-router", "react-spa"):
        self._runtime = BrowserRuntime(base_url=cfg.base_url)
    else:
        self._runtime = BrowserRuntime(base_url=cfg.base_url)  # fallthrough!
```

Both branches return `BrowserRuntime`. `RemoteBrowserRuntime` exists but never selected.

**Finding 12 (Medium):** Runtime selection is hardcoded. For Phase 3 billing (different runtimes have different costs), runtime type must be explicitly selectable and tracked.

### 4.7 Medium: No Security Review of v2.0/v2.1 Endpoints

- CORS: `allow_origins=["*"]` with `allow_credentials=True` — browsers will reject credentialed requests from `*`
- Rate limiter: in-memory `dict`, lost on restart, not shared across workers
- API key in URL path: `DELETE /api/platform/orgs/:id/keys/:kid` — key_id in URL, logged by proxies
- No request body size limit on webhook endpoints
- Workspace IDs in URLs are not validated for injection

### 4.8 Architecture: Separate Platform Resources from Execution Engine

Current architecture conflates two distinct concerns. A clearer separation:

```
┌─────────────────────────────────────────────────────────┐
│                   PLATFORM LAYER                         │
│  (Business resources — what users see and manage)        │
│                                                          │
│  Organization → Workspace → ExecutionRequest → Run       │
│                                           ↓              │
│                                       RunEvent            │
│                                           ↓              │
│                              ┌────────────┼──────────┐   │
│                              ↓            ↓          ↓   │
│                          Webhook      Audit    Billing   │
│                          Timeline     Metrics  Replay    │
├─────────────────────────────────────────────────────────┤
│                 EXECUTION ENGINE                         │
│  (Execution mechanism — how work gets done)              │
│                                                          │
│  ExecutionService                                        │
│       ↓                                                  │
│    Queue                                                 │
│       ↓                                                  │
│   AgentLoop → BrowserRuntime → CapabilityRouter          │
│       ↓                                                  │
│   RunRepository (persists Run, emits RunEvents)          │
└─────────────────────────────────────────────────────────┘
```

**Principle:** Platform Resources are business objects — they have IDs, APIs, and lifecycles. Execution Engine is the mechanism — it does work, manages concurrency, and returns results. Runtime is an engine concern, never a platform concern.

This separation prevents:
- Platform capabilities (billing, audit) from leaking into Runtime
- Runtime implementation changes from breaking Platform APIs
- Engine concerns (queue depth, worker count) from appearing in business APIs

**Finding 14 (Architecture):** Explicitly document the Platform Resources vs Execution Engine boundary in CONSTITUTION. This is the architectural foundation that Phase 3 builds on.

---

## 5. Phase 3 Dependency Map

What each Phase 3 feature needs that doesn't exist yet.

### Shared Foundation: ExecutionRequest + Run + RunEvent + ExecutionService

All three Phase 3 features depend on execution lifecycle being a Platform concern with explicit resources and an orchestration layer.

```
Needs:
  ❌ ExecutionRequest model + lifecycle (created→validated→queued→dispatching→running→terminal)
  ❌ Run model (immutable record, frozen on completion)
  ❌ RunEvent model (typed events: execution.requested, phase.*, run.completed, cost.recorded, ...)
  ❌ ExecutionService (orchestration: validate → enqueue → dispatch → persist → emit events)
  ❌ ExecutionRequest + Run + RunEvent storage (SQLite tables)
  ❌ API: POST /api/workspaces/:id/executions, GET /api/executions/:id, GET /api/runs/:id
  ❌ request_id / run_id propagation through ExecutionService → AgentLoop → Runtime → RunEvents
```

### Webhooks
```
Needs:
  ✅ Task queue (infra/task_queue.py exists)
  ❌ RunEvent — webhooks subscribe to event types, not poll Run
  ❌ Auth integration — who can register webhooks? (depends on Auth fix P0)
  ❌ Webhook registry: endpoint URL, subscribed event types, secret, status
  ❌ Signature verification (HMAC-SHA256)
  ❌ Delivery log — each delivery attempt is a RunEvent consumer record
  ❌ Retry with exponential backoff
  ❌ Event catalog: execution.requested, execution.queued, execution.started,
     phase.started, phase.completed, run.completed, run.failed, cost.recorded
```

### Audit
```
Needs:
  ✅ Governance audit engine exists (state/sop/cost/safety)
  ❌ RunEvent — operational audit is an append-only log of typed events
  ❌ Audit log storage (append-only table, immutable)
  ❌ Audit log API: query by org, workspace, event_type, time range; filter; export
  ❌ Retention policy (per event type, per org)
  ❌ Request ID chain: API request → ExecutionRequest → Run → RunEvents
```

### Billing
```
Needs:
  ❌ Run (immutable) — billing charges against frozen Run records
  ❌ RunEvent (cost.recorded) — billing aggregates cost events, not Run snapshots
  ❌ Usage metering per org/workspace (run count, token sum, storage bytes) — from Run.summary
  ❌ Pricing model decision (per-run? per-token? per-seat? subscription?)
  ❌ Quota enforcement at ExecutionService layer (before dispatch)
  ❌ Invoice generation from aggregated Run data
  ❌ Payment integration (or placeholder)
  ❌ Usage API: GET /api/orgs/:id/usage?period=2026-06
  ❌ Workspace.quotas → Tenant.limits one-way sync
```

---

## 6. Recommended Roadmap

**Don't jump directly to Webhooks and Billing. First build the Platform Runtime layer they depend on.**

### v2.2 — Platform Runtime Foundation

This is the missing layer between API and Runtime. Once built, all Phase 3 features become RunEvent consumers.

```
Platform Runtime:
  execution_service.py   — orchestration: validate → enqueue → dispatch → persist → emit
  execution_request.py   — user intent, lifecycle: created|queued|running|completed|failed|cancelled
  run.py                 — immutable execution record. References capability, NOT runtime.
  run_event.py           — typed event dataclass
  event_bus.py           — lightweight pub/sub: publish(event) + subscribe(callable). list[Callable] is fine.
  run_store.py           — SQLite persistence: save()/load()/list(). No Repository Pattern.

Runtime:                 — ZERO changes. Runtime stays frozen.
API:                     — new endpoints only
```

**Effort:** ~10h. **Runtime changes:** 0 lines.

Deliverables:
- `aitest/platform/execution_service.py`
- `aitest/platform/execution_request.py`
- `aitest/platform/run.py` (with `capability` + `agent` fields, NOT `runtime_type`)
- `aitest/platform/run_event.py`
- `aitest/platform/event_bus.py`
- `aitest/platform/run_store.py`
- API: `POST /api/workspaces/:id/executions`, `GET /api/executions/:id`, `GET /api/runs/:id`
- Auth unified

**🚨 Alpha Checkpoint:** After v2.2, run 50+ real executions. Execute login, search, CRUD flows. Let RunEvents accumulate. Verify Timeline, Replay, Metrics work against real Run data. Architecture problems invisible in code reviews appear after 100 real runs.

### v2.3 — Platform Services

RunEvent consumers. Each is an independent subscriber.

```
Webhook              — subscribe to RunEvent types → deliver to registered endpoints
Operational Audit    — append-only log: subscribe to all RunEvents
Request ID           — X-Request-Id → ExecutionRequest → Run → RunEvent chain
ExecutionContext     — wire via ExecutionService (NOT constructor injection)
```

**Effort:** ~15h.

### v2.4 — Billing & Quota

```
Billing              — aggregate cost.recorded events per org/workspace
Quota Enforcement    — ExecutionService checks Workspace quotas before dispatch
Workspace→Tenant     — one-way sync: Workspace.quotas → Tenant.limits
Usage API            — GET /api/orgs/:id/usage?period=2026-06
```

**Effort:** ~18h.

### v2.5 — Platform Hardening

```
Integration Tests    — 30+ tests for v2.0/v2.1/v2.2 APIs
Security             — CORS, rate limiter Redis option, body size limits
Runtime Selection    — wire RemoteBrowserRuntime, cost_multiplier metadata
API Polish           — versioning strategy doc, pagination (when needed)
```

**Effort:** ~12h.

### Deferred (Phase 4+)

```
Circular Dependencies — 28 lazy-import cycles. No breakage. Extract protocols/ later.
API Response Envelope — standardize when external SDK exists
API Versioning prefix — /api/v1 when first external release
```

---

## 7. Test Results

```
92 passed, 2 skipped in 1.62s
```

All existing tests pass. But test scope is narrow — unit/logic only. The 2 skipped tests:
- `test_preflight_discovers_pages` — SKIPPED (no reason)
- `test_preflight_recommends_mode` — SKIPPED (no reason)

E2E smoke tests (`aitest/web/e2e/smoke.spec.ts`) — 18 tests, all UI navigation. Require both frontend + backend running. Not runnable in CI without both services.

---

## 8. Recommendation — APPROVED with Modifications

**Architecture: 9.3/10. Implementation: 7.5/10. Phase 3 Ready: 8/10.**

Alice is ready. Insert **v2.2 Platform Runtime Foundation** between v2.1 and Phase 3. Timeline: ~10h for v2.2, then Alpha.

### Why v2.2 matters

Current: `API → Runtime.execute()` — no platform layer.

After v2.2: `API → ExecutionService → ExecutionRequest → Queue → Runtime → Run → RunEvent`

Once this layer exists, all Phase 3 features are RunEvent consumers. Runtime stays frozen.

### Roadmap

```
v2.0 ✅ Identity + Organization + RBAC + API Keys
v2.1 ✅ Workspace Isolation + ExecutionContext + Resource Boundaries
v2.2 🔨 Platform Runtime Foundation
       execution_service + execution_request + run + run_event + event_bus + run_store
       + Auth unified
       → 🚨 Alpha: 50+ real executions, verify Timeline/Replay/Metrics against real Run data
v2.3 🔨 Platform Services
       Webhook + Operational Audit + Request ID + ExecutionContext wiring
v2.4 🔨 Billing & Quota
       Billing + Quota Enforcement + Workspace→Tenant sync + Usage API
v2.5 🔨 Platform Hardening
       Integration Tests + Security + Runtime Selection + API polish
```

### Four TL Modifications to the Review

1. **ExecutionRequest lifecycle stays minimal.** Six states: `created|queued|running|completed|failed|cancelled`. No `Validated`, `Dispatching`, `TimedOut`, `Scheduling`. Alice is not Temporal.

2. **EventBus + storage stay lightweight.** `event_bus.py`: `publish(event)` + `subscribe(callable)`. A `list[Callable]` is fine. `run_store.py`: `save()/load()/list()`. No Repository Pattern, no Kafka, no CloudEvent. Extract later if needed.

3. **Run references Capability, not Runtime.** `run.capability = "browser"`, not `run.runtime_type = "BrowserRuntime"`. Future runtimes (CLI, MCP, Python, Remote CDP) add capabilities without changing Run model. Billing charges by capability type. Runtime stays an engine detail.

4. **Alpha after v2.2. Don't wait for v2.8.** Run 50+ real executions. Execute login, search, CRUD flows. Let RunEvents accumulate. Verify Timeline, Replay, Metrics against real data. Architecture problems invisible in code reviews appear after 100 real runs.

### What to NOT do

- API versioning prefix, response envelope, pagination → defer. No external consumers yet.
- ExecutionRequest granular states → start simple, expand when a consumer needs them.
- Repository Pattern, heavy Event framework → defer. Simple functions are fine.
- Circular dependency extraction → no breakage. Phase 4+.

### Go/No-Go

✅ **APPROVED.** Start v2.2 immediately. ~10h bounded scope. Runtime frozen. Alpha checkpoint after v2.2.

---

> **Reviewer:** Architecture Reviewer (Claude) + Tech Lead approval
> **Review v1:** 2026-06-24 — Initial findings
> **Review v2:** 2026-06-24 — TL review: Quota location, Tenant approach, ExecutionContext wiring
> **Review v3:** 2026-06-24 — ExecutionRequest + Run distinction, priorities reordered
> **Review v4:** 2026-06-24 — Event model, ExecutionService, Platform vs Engine separation
> **Review v5:** 2026-06-24 — v2.2 milestone, simplified lifecycle, roadmap restructured
> **Review v6:** 2026-06-24 — Final approval with 4 TL modifications
>
> **Key revisions in v6:**
> - **Run references Capability, not Runtime** (4.5.5) — `capability: "browser"` not `runtime_type: "BrowserRuntime"`
> - **EventBus + storage lightweight:** no Repository Pattern, no heavy Event framework, `list[Callable]` pub/sub
> - **Alpha checkpoint after v2.2** — 50+ real runs before continuing to v2.3
> - **Four TL modifications** documented in Section 8
> - **Approved** — 80% adopted, 20% downgraded per TL directive
>
> **Next action:** Start v2.2 implementation. Alpha after v2.2.

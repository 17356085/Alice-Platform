# Stabilization Roadmap — Alice Platform v2.x Stage 2

> **Date:** 2026-06-28
> **Status:** ACTIVE
> **Predecessor:** [Architecture Freeze v1.0](ARCHITECTURE_FREEZE_V1.md)
> **Constitution:** [CONSTITUTION.md](CONSTITUTION.md)

---

## Phase Summary

```
✓ Foundation
✓ Identity
✓ Execution Model
✓ Observability
✓ Governance
────────────── Architecture Freeze (2026-06-24) ──────────────

Stage 2 — Stabilization  ← CURRENT
├── 1. Memory Audit
├── 2. Long Running Test
├── 3. React Render Audit
├── 4. Observability Dashboards
├── 5. Pressure Testing
├── 6. Recoverability
└── 7. Developer Experience

────────────── Production Ready ──────────────

v3.x (Future — NOT now)
├── Plugin Marketplace
├── Multi-node Execution
├── Distributed Scheduler
├── Remote Workers
├── Cloud Deployment
└── Enterprise Features
```

---

## Rationale

System risk has shifted from architecture to **engineering quality**.
Recent issues (2026-06-24 through 2026-06-28) show the primary failure
mode is not missing abstractions — it's resource leaks, unbounded growth,
and insufficient observability under sustained load.

Architecture Freeze has held. Frozen modules remain at zero changes.
This proves the extension model works. Now we harden what exists.

**Goal:** Alice runs continuously for 24–72 hours with stable resource usage.

**Non-goal:** New features, new APIs, new events, new consumers.

---

## Workstreams

### 1. Memory Audit

**Objective:** Zero unbounded memory growth under sustained operation.

| Check | Target | Signal |
|-------|--------|--------|
| Object lifecycle | All resources freed after Run completes | No lingering references |
| RunStore | Stable after Run count stabilizes | No monotonic growth |
| EventStore | Bounded by retention policy | No infinite append |
| audit.db | Bounded size | No unbounded WAL/journal growth |
| WebSocket connections | Freed on disconnect | Connection count returns to baseline |
| asyncio Tasks | All tasks awaited/cancelled | `asyncio.all_tasks()` stable |
| BrowserRuntime | browser/page/context freed | No orphaned Chromium processes |

**Method:** Code audit — trace every `__init__` / `create` / `open` / `subscribe` to its
corresponding `close` / `dispose` / `unsubscribe` / `cancel`. Then verify with
tracemalloc under load.

**Deliverable:** Memory leak report with root cause per finding.

### 2. Long Running Test

**Objective:** 72-hour continuous run with stable resource profile.

**Durations:** 24h → 48h → 72h

**Metrics tracked:**

| Metric | Baseline | Threshold |
|--------|----------|-----------|
| RSS | Cold start | Must not double over 72h |
| CPU % | Idle | Must not drift upward |
| Thread count | Cold start | ±10% over 72h |
| SQLite size | Initial | Must plateau after warmup |
| Queue depth | 0 | Must return to 0 after bursts |
| Event count | 0 | Bounded by retention |
| Run count | 0 | No leak per-run |
| WebSocket count | 0 | Returns to baseline after disconnect |
| GC generations | Normal | gen2 count must stabilize |

**Hard requirement:** No metric may show monotonic increase over the full duration.
A metric that plateaus is acceptable. A metric that never stops growing is a leak.

### 3. React Render Audit

**Objective:** Zero unnecessary re-renders, re-fetches, re-connects.

**Checklist:**

| Area | Problem | Detection |
|------|---------|-----------|
| StrictMode | Double-mount side effects | Console warnings, duplicate WS |
| Context | Unnecessary provider re-renders | React DevTools Profiler |
| Store (Zustand) | Selector causing re-render on unchanged slice | `useShallow` audit |
| Hooks | `useEffect` dependency array causing loops | Infinite render guard |
| Suspense | Suspense waterfall instead of parallel | Network waterfall chart |
| WS Provider | Reconnect loops on connection drop | WS frame log |
| React Query | `refetchInterval` without backoff, staleTime=0 | Query devtools |
| Virtual List | Re-render on every scroll event | Profiler flamegraph |

**Method:** React DevTools Profiler + custom `why-did-you-render` instrumentation.
Audit every `useEffect`, `useMemo`, `useCallback`, and store selector.

### 4. Observability Dashboards

**Objective:** Self-serve diagnostics without external tools (py-spy, tracemalloc).

**New dashboards** (all served from the platform UI):

| Dashboard | Key Metrics |
|-----------|-------------|
| Memory | RSS, heap, GC stats, per-Run memory delta |
| Thread | Thread count, thread states, deadlock detection |
| Task | asyncio task count, pending tasks, task age |
| Queue | Queue depth, processing rate, age histogram |
| GC | Gen 0/1/2 collections, object count by generation |
| WebSocket | Connection count, message rate, reconnect count |

**Existing dashboards** (already built): Timeline, Audit, Metrics, History.

**Principle:** Every dashboard answers one question: "Is the platform healthy right now?"
No dashboard requires reading Python source code to interpret.

### 5. Pressure Testing

**Objective:** Find degradation thresholds before they hit production.

**Load scenarios:**

| Scenario | Scale | Pass Criteria |
|----------|-------|---------------|
| 100 Runs | Concurrent | All complete, no errors |
| 1,000 Runs | Sequential over 1h | Queue depth returns to 0 |
| 10,000 Events | Burst within 60s | EventBus latency < 100ms p99 |
| 50,000 Events | Sustained over 10min | No dropped events |
| 100 WebSocket | Concurrent connections | All connect, message latency < 50ms |
| 20 BrowserRuntime | Concurrent browsers | Memory returns to baseline after close |
| 500 Artifacts | Mixed sizes (1KB–10MB) | Storage bounded, no OOM |

**Method:** Synthetic load generators. Not real test runs — controlled payloads to
isolate platform overhead from Agent/LLM variability.

### 6. Recoverability

**Objective:** Platform survives and recovers from failure modes.

| Capability | Scope | Acceptance |
|------------|-------|------------|
| Retry | Per-Run, exponential backoff + jitter | 3 retries, then dead-letter |
| Resume | Paused Run continues from checkpoint | State restored correctly |
| Cancel | In-flight Run terminated cleanly | Resources freed, no zombie tasks |
| Timeout | Per-Run wall-clock deadline | Run killed, resources freed |
| Crash Recovery | Process restart after SIGKILL | In-flight Runs detected, restarted or failed |
| Restart Recovery | Clean shutdown + restart | All state restored, no data loss |
| Checkpoint | Periodic state snapshot per Run | Resume from last checkpoint, not start |

**Principle:** Every Run has a defined termination path — success, failure, timeout,
or cancel. No Run enters an unrecoverable limbo state.

### 7. Developer Experience (DX)

**Objective:** External consumers can build on the platform without reading source code.

| Tool | Description |
|------|-------------|
| Run Inspector | UI to inspect any Run: events, timeline, artifacts, state |
| Event Inspector | UI to browse/filter/replay events |
| Artifact Viewer | UI to browse Run artifacts (screenshots, traces, logs) |
| OpenAPI | Auto-generated `/openapi.json`, complete + accurate |
| SDK | Python `aitest-client` package wrapping REST API |
| CLI | `aitest run inspect`, `aitest event tail`, `aitest artifact list` |
| Replay | Re-run a past Run with same inputs, compare outputs |
| Debug Panel | Per-Run debug view: LLM calls, tool calls, skill invocations |

---

## Consumer-First Principle

**Rule:** New capabilities default to RunEvent consumers. A new abstraction (class,
interface, protocol) is only justified when **two concrete consumers** independently
need the same abstraction.

```
Allowed (no review):
  class NewConsumer:
      def __init__(self):
          get_bus().subscribe(EventType.RUN_COMPLETED, self._handle)

Requires justification:
  class NewAbstractThing:  # ← why does this exist?
      ...
```

This rule has been in effect since Architecture Freeze (2026-06-24). It continues
throughout Stage 2.

---

## Governance

### Decision Rights

| Decision | Who |
|----------|-----|
| Prioritize workstream order | This document |
| Choose tooling per workstream | Implementer |
| Add new workstream | Architecture Review |
| Skip or reduce a workstream | Architecture Review |
| Declare Stage 2 complete | All 7 workstreams pass acceptance |

### Freeze Continuity

Architecture Freeze v1.0 remains in full effect. Frozen modules remain frozen.
The extension mechanism (RunEvent consumers) remains the default for new capability.

### Success Criteria for Stage 2

1. All 7 workstreams completed
2. 72-hour continuous run with stable resource profile
3. No known memory leaks
4. All observability dashboards operational
5. Pressure test thresholds documented
6. Recoverability: crash + restart cycle passes 10 iterations

---

## Related Documents

| Document | Relationship |
|----------|-------------|
| [ARCHITECTURE_FREEZE_V1.md](ARCHITECTURE_FREEZE_V1.md) | Predecessor — frozen modules, extension model |
| [CONSTITUTION.md](CONSTITUTION.md) | Governing principles — Platform Core, Extension Points |
| [MEMORY_LEAK_RCA_2026-06-24.md](MEMORY_LEAK_RCA_2026-06-24.md) | Prior memory leak investigation |
| [MEMORY_LEAK_RCA_FRONTEND_2026-06-24.md](MEMORY_LEAK_RCA_FRONTEND_2026-06-24.md) | Prior frontend memory investigation |
| [ARCHITECTURE_REVIEW_2026-06-27.md](ARCHITECTURE_REVIEW_2026-06-27.md) | Most recent architecture review |

---

> **本路线图自 2026-06-28 起生效。**
> **Stage 2 期间不新增功能。所有精力投入稳定化。**
> **v3.x 在 Stage 2 全部完成前不启动。**

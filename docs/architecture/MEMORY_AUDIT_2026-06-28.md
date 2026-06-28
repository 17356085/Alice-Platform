# Memory Audit Report — 2026-06-28

> **Status:** COMPLETE (Phase 1 — Discovery)
> **Scope:** RunStore, EventStore, BrowserRuntime, WebSocket, asyncio Task
> **Next:** Phase 2 — Fix verified leaks, add retention policies

---

## Executive Summary

| Path | Severity | Leaks Found | Action |
|------|----------|-------------|--------|
| RunStore | MEDIUM | 0 (but unbounded growth) | Add retention policy |
| EventStore | HIGH | 4 systems, 1 with cap | Add pruning to 3 of 4 |
| BrowserRuntime | **CRITICAL** | 3 definite leak paths | Fix immediately |
| WebSocket | LOW | 1 manager missing cleanup | Register in lifecycle |
| asyncio Task | LOW | 2 fire-and-forget | Track or remove |

---

## Path 1: RunStore

**File:** `aitest/platform/run_store.py`

**Architecture:** Singleton SQLite store. 3 tables: `runs`, `run_events`, `execution_requests`.
No in-memory cache. Every operation is direct SQLite I/O.

**Finding:** Zero eviction mechanism.

```
No delete() method exists
No close() / cleanup() / shutdown() method
No TTL / max-age / max-rows
No VACUUM call
```

**Current state:** 61 KB (`governance/.data/runs.db`). Grows with every Run + every RunEvent.

**Risk:** Under 72h of sustained usage, `runs.db` could reach many MB. Under 1000 Runs, the
`run_events` table grows N× faster than `runs` (multiple events per Run). Query performance
degrades as tables grow without indexes on timestamp columns used in `list_events` filtering.

**Recommendation:**
1. Add `delete_runs_older_than(days: int)` method
2. Add retention config (default: 30 days)
3. Call retention cleanup on server start + periodic sweep
4. Add VACUUM after bulk deletes
5. Add indexes on `(run_id, timestamp)` for `run_events`

---

## Path 2: EventStore

**Finding:** No single EventStore class exists. Four independent event storage systems,
three with no retention.

### System A: File-based Governance Events

**File:** `aitest/audit_engine/event_bus.py`
**Storage:** `governance/.events/*.json` (one file per event)
**Retention:** Manual CLI only (`event_bus clean` — removes processed events >24h)
**Current:** 3 files

**Risk:** Every governance event (CostAnomaly, SOPViolation, StateDrift, SafetyViolation,
AgentCompleted, CycleEnd, etc.) writes a JSON file. Under 72h load this could reach
thousands of files. No automated pruning.

### System B: Platform RunEvents (SQLite)

**File:** `aitest/platform/run_store.py` (`run_events` table in `runs.db`)
**Retention:** None

### System C: Observation Bus (In-Memory)

**File:** `aitest/platform/observation_bus.py`
**Retention:** Cap of 1000 events (auto-prune). **Only system with a cap.**

### System D: Audit Log (SQLite)

**File:** `aitest/platform/audit_log.py`
**Storage:** `governance/.data/audit.db`
**Retention:** None. Subscribes to `"*"` on EventBus — every RunEvent is persisted.
**Current:** 33 KB

### Bonus: LangGraph Checkpoints

**File:** `governance/.graph_state/checkpoints.sqlite`
**Size:** 200 MB
**Retention:** None. LangGraph SqliteSaver appends checkpoints. No cleanup mechanism.

**Recommendation:**
1. System A: Add cron-based cleanup (T+7d), or move to SQLite with TTL index
2. System B: Same retention as RunStore (30-day retention on `run_events`)
3. System D: Add `DELETE FROM audit_entries WHERE timestamp < ?` with configurable TTL
4. Checkpoints: Add `delete_old_checkpoints(max_keep=N)` or rely on LangGraph's built-in
5. Unify retention config into single `RetentionPolicy` in `aitest/config.py`

---

## Path 3: BrowserRuntime — CRITICAL

**Finding:** Three definite leak paths where BrowserUseDriver / Playwright Browser is
created but never closed.

### Leak 1: ProjectContext.runtime()

**File:** `aitest/platform/context.py:188`
```python
def runtime(self) -> BrowserRuntime:
    if self._runtime is None:
        self._runtime = BrowserRuntime(self.config)
    return self._runtime
```
No `close()` method on ProjectContext. No cleanup in `__del__`. BrowserRuntime holds
a BrowserUseDriver which holds a `browser_use.Browser` → Chromium process.
Every ProjectContext that calls `.runtime` leaks a Chromium process.

### Leak 2 & 3: CapabilityRouter Browser Providers

**File:** `aitest/platform/capability_router/providers/browser.py:37`
```python
class BrowserNavigateProvider:
    async def execute(self, ...):
        driver = BrowserUseDriver(...)  # ← created
        await driver.start()            # ← spawns Chromium
        # ... use ...
        # NEVER CLOSED — no driver.close(), no __aexit__
```

**File:** `aitest/platform/capability_router/providers/browser.py:78`
```python
class BrowserScreenshotProvider:
    async def execute(self, ...):
        driver = BrowserUseDriver(...)  # ← same pattern
        await driver.start()
        # NEVER CLOSED
```

Both providers create a new `BrowserUseDriver()` per invocation, call `start()`
(spawning Chromium), but never call `close()`. Each invocation leaks one Chromium
process + one Playwright Browser + one Page.

### Safe Paths (verified)

- `BrowserUseSkillAdapter` (`bu_adapter.py:239`): uses `async with BrowserUseDriver()` — safe
- `OnboardingAgent._release_resources()` (`onboarding/project_onboarding_agent.py:604`): calls `await discovery.close()` in finally — safe
- `BrowserMCPServer.browser_close` tool (`mcp/browser_server.py:214`): manual but functional

### MCP Browser Server

**File:** `aitest/mcp/browser_server.py:283`
```python
asyncio.run(main())  # infinite loop, no shutdown cleanup
```
If the MCP server is killed, no browser cleanup runs.

**Recommendation (immediate):**
1. Add `close()` to `ProjectContext` — call `self._runtime.close()` if exists
2. Wrap CapabilityRouter providers with `async with` or add `finally: await driver.close()`
3. Add `ProjectContext.__del__` with best-effort close
4. Add `atexit` handler for MCP browser server cleanup

---

## Path 4: WebSocket

**Finding:** One manager missing lifecycle registration. No idle timeout on any endpoint.

### KanbanWSManager — Missing Cleanup

**File:** `aitest/server/api/kanban.py:59`
```python
_kanban_ws = KanbanWSManager()  # module-level singleton
```
Not registered in `lifecycle_registry`. On server shutdown, connections are not
gracefully closed. Compare with `AgentTerminalWSManager` which IS registered.

### No Idle Timeout

None of the three WS endpoints (terminal, kanban, onboarding) have per-connection
idle timeout. A client that connects and never sends data holds the connection
indefinitely.

### Frontend Reconnect

Kanban + Terminal have auto-reconnect with exponential backoff (1s–30s).
This is correct behavior but without server-side idle timeout, abandoned browser
tabs hold connections until the browser GCs them.

**Recommendation:**
1. Register `KanbanWSManager` in `lifecycle_registry` for graceful shutdown
2. Add idle timeout (e.g., 300s) with ping-pong keepalive on all endpoints
3. Consider per-IP connection limit to prevent accidental DoS

---

## Path 5: asyncio Task

**Finding:** Two true fire-and-forget tasks. Core task tracking is solid.

### Fire-and-Forget 1: Session Persist

**File:** `aitest/server/api/chat.py:579`
```python
loop.create_task(_persist_session(...))  # no handle, no cancel
```
If the server shuts down while a persist is in-flight, the task is abandoned.
Low risk — session persist is fast and idempotent.

### Fire-and-Forget 2: BrowserUseDriver.__del__

**File:** `aitest/integrations/bu_driver.py:194`
```python
def __del__(self):
    loop.create_task(self.close())  # best-effort fallback
```
This is a defensive fallback, not a leak. But if the event loop is already closed
when `__del__` runs, this will fail silently.

### TaskGuard Coverage

`TaskGuard` (`aitest/platform/ownership.py:619`) tracks all tasks created through it:
- `_active_task_ids` set
- `_total_created/completed/cancelled` counters
- `cancel_all()` called on server shutdown

Background loops (audit_scheduler, lifecycle_sweep, rate_state_cleanup) are all created
through `TaskGuard` and are cancellable.

### Daemon Threads (not asyncio)

Five daemon threads exist alongside the async task system:
- `agent_runner.py` — metrics recording
- `core.py` — 4 agent execution threads
- `redis_pubsub.py` — Redis subscriber
- `task_queue.py` — task queue worker
- `kanban.py` — SOP background runner

These are Python threads (not asyncio tasks). They have `daemon=True` so they die with
the process. No join() or explicit cleanup.

**Recommendation:**
1. Track `_persist_session` task and cancel on shutdown
2. Replace `loop.create_task(self.close())` in `__del__` with `atexit` registration
3. Document daemon thread cleanup expectations

---

## Unbounded SQLite Growth Summary

| Database | Path | Size | Retention | Risk |
|----------|------|------|-----------|------|
| `runs.db` | `governance/.data/` | 61 KB | None | HIGH |
| `audit.db` | `governance/.data/` | 33 KB | None | HIGH |
| `checkpoints.sqlite` | `governance/.graph_state/` | 200 MB | None | **CRITICAL** |
| `.events/*.json` | `governance/.events/` | 3 files | Manual CLI | MEDIUM |

---

## Prioritized Fix Queue

| # | Severity | Path | Fix | Effort |
|---|----------|------|-----|--------|
| 1 | CRITICAL | BrowserRuntime | Add close() to CapabilityRouter providers | 30 min |
| 2 | CRITICAL | BrowserRuntime | Add close() to ProjectContext | 15 min |
| 3 | CRITICAL | Checkpoints | Add LangGraph checkpoint retention | 1 hr |
| 4 | HIGH | audit.db | Add TTL-based DELETE | 30 min |
| 5 | HIGH | runs.db | Add retention policy + VACUUM | 45 min |
| 6 | MEDIUM | .events/ | Add automated cleanup (7-day TTL) | 30 min |
| 7 | LOW | WebSocket | Register KanbanWSManager in lifecycle | 15 min |
| 8 | LOW | asyncio Task | Track _persist_session task | 10 min |
| 9 | LOW | WebSocket | Add idle timeout to all WS endpoints | 30 min |

---

## Phase 2 Plan

After fixes applied:
1. Run all existing tests to confirm no regression
2. Create leak reproduction scripts per path
3. Verify each fix with before/after RSS measurement
4. Proceed to Long Running Test (24h → 48h → 72h)

---

> **审计完成时间:** 2026-06-28
> **审计方法:** 静态代码分析 — 追踪每个 `__init__`/`create`/`open`/`subscribe`/`create_task` 到其对应 `close`/`dispose`/`unsubscribe`/`cancel`
> **覆盖率:** 5/5 路径，42 文件，~150 站点

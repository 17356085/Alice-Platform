# Architecture Freeze v1.0 — Alice Platform

> **Date:** 2026-06-24
> **Scope:** v2.0 → v2.4
> **Status:** ACTIVE

---

## Freeze Declaration

The core execution model is stable. v2.0 through v2.4 form a complete architecture
loop where each layer builds on the previous, none overturned:

```
v2.0  Foundation         Organization, RBAC, API Keys
v2.1  Identity           Workspace, ExecutionContext, Resource Boundaries
v2.2  Execution Model    ExecutionRequest 1→N Run, RunEvent, EventBus
v2.3  Observability      Timeline, AuditLog, ExecutionHistory
v2.4  Governance         Webhook, BillingHook, QuotaUsage, Metrics
```

## Frozen Modules

These modules are architecture-frozen. Changes require Architecture Review.

| Module | Frozen Since | Reason |
|--------|-------------|--------|
| `platform/runtime.py` | v1.x | Runtime never imports Organization |
| `platform/execution_service.py` | v2.2 | Stable orchestration boundary |
| `platform/run.py` | v2.2 | Immutable record model |
| `platform/run_event.py` | v2.2 | Stable event schema |
| `platform/event_bus.py` | v2.2 | publish/subscribe API |
| `platform/consumer.py` | v2.4 | RunEventConsumer Protocol |

## Verified Stability

| Metric | Result |
|--------|--------|
| ExecutionService changes since v2.2 | 0 lines |
| Runtime changes since v1.x | 0 lines |
| RunEvent field changes since v2.2 | 0 |
| EventBus API changes since v2.2 | 0 |
| New core abstractions since v2.4 | 0 |

## Extension Mechanism

New platform capabilities default to **RunEvent consumers**:

```python
class NewCapability:
    def __init__(self):
        bus = get_bus()
        bus.subscribe(EventType.RUN_COMPLETED, self._handle)

    def _handle(self, event: RunEvent):
        # consume event
        pass
```

No new abstractions unless **two concrete capabilities demand the same one**.

## Compatibility Rules

1. **RunEvent fields** — additive only, backward compatible.
2. **Event types** — stable, not renamed for implementation changes.
3. **Consumers** — depend only on public events, not internal state.
4. **Consumers are unordered** — no dependency between consumers.
5. **Consumers are idempotent** — Billing, Quota, Webhook handle duplicate delivery.

## Phase 2 Directions

| Priority | Area | Rationale |
|----------|------|-----------|
| 1 | **Recoverability** — Retry, Cancel, Timeout, Resume | Production reliability |
| 2 | **Artifacts** — Traces, Screenshots, Reports, Logs | User-facing value |
| 3 | **Policy** — Workspace limits, capability gates | Data-driven after usage |
| 4 | **DX** — OpenAPI, SDK, Run Inspector, Event Replay | External consumption |

## Governance

- Architecture Review required to modify any Frozen Module.
- New EventBus consumers: no review needed.
- New RunEvent types: light review (additive only).
- New abstractions: must justify with two concrete use cases.

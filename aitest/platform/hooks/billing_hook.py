"""
BillingHookConsumer — emit billing events on run completion. v2.4

Does NOT deduct balance. Does NOT implement invoicing.
Emits structured billing events that future billing systems consume.

Hook, not billing. Platform, not business logic.

Usage:
    from aitest.platform.hooks.billing_hook import BillingHookConsumer

    hook = BillingHookConsumer()
    hook.start()   # subscribes to run.completed + cost.recorded
"""

from __future__ import annotations

import json
import threading
from pathlib import Path
from datetime import datetime, timezone

from ..consumer import RunEventConsumer
from ..run_event import RunEvent, EventType, make_event, RunCompletedData, CostRecordedData, EventDataKey as K
from ..event_bus import get_bus
from ..event_replay import mark_event_seen, is_event_seen
from ..config_registry import cfg


def _billing_dir() -> Path:
    return cfg.billing_dir


class BillingHookConsumer:
    """Emits billing events. Does NOT touch balance, invoicing, or payments.

    Consumes:
      - run.completed → emits billing.usage_recorded
      - cost.recorded  → emits billing.cost_recorded

    Future billing systems subscribe to billing.* events.

    Args:
        bus: EventBus instance. If None, uses get_bus() singleton.
    """

    def __init__(self, bus=None):
        self._dir = _billing_dir()
        self._dir.mkdir(parents=True, exist_ok=True)
        self._lock = threading.Lock()
        self._active = False
        self._consumer_name = "billing-hook"
        self._bus = bus  # injected EventBus (None = lazy singleton)
        self._seen: set[str] = set()  # backward-compatible in-memory view for tests

    def start(self):
        if self._active:
            return
        bus = self._bus or get_bus()
        bus.subscribe(EventType.RUN_COMPLETED, self._on_run_completed, priority=10)  # HIGH: financial data
        bus.subscribe(EventType.COST_RECORDED, self._on_cost_recorded, priority=10)
        self._active = True

    def stop(self):
        if not self._active:
            return
        bus = self._bus or get_bus()
        bus.unsubscribe(EventType.RUN_COMPLETED, self._on_run_completed)
        bus.unsubscribe(EventType.COST_RECORDED, self._on_cost_recorded)
        self._active = False

    @property
    def is_active(self) -> bool:
        return self._active

    # ── Handlers ──────────────────────────────────────────────────────

    def _on_run_completed(self, event: RunEvent):
        """Emit billing.usage_recorded with run summary."""
        if is_event_seen(event.event_id, self._consumer_name):
            return  # already processed (PG dedup)
        billing_event = {
            "version": 1,
            "event": "billing.usage_recorded",
            "run_id": event.run_id,
            "request_id": event.request_id,
            "org_id": event.data.get(K.ORG_ID, ""),
            "workspace_id": event.data.get(K.WORKSPACE_ID, ""),
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "usage": {
                "total_tokens": event.data.get(K.TOTAL_TOKENS, 0),
                "agent_runs": event.data.get(K.AGENT_RUNS, 0),
                "module": event.data.get(K.MODULE, ""),
                "capability": "browser",
            },
        }
        self._persist(billing_event)
        mark_event_seen(event.event_id, self._consumer_name)
        self._seen.add(event.event_id)

    def _on_cost_recorded(self, event: RunEvent):
        """Emit billing.cost_recorded."""
        if is_event_seen(event.event_id, self._consumer_name):
            return  # already processed (PG dedup)
        billing_event = {
            "version": 1,
            "event": "billing.cost_recorded",
            "run_id": event.run_id,
            "request_id": event.request_id,
            "org_id": event.data.get(K.ORG_ID, ""),
            "workspace_id": event.data.get(K.WORKSPACE_ID, ""),
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "cost": {
                "amount": event.data.get(K.TOTAL_COST, 0.0),
                "currency": "USD",
                "tokens": event.data.get(K.TOTAL_TOKENS, 0),
            },
        }
        self._persist(billing_event)
        mark_event_seen(event.event_id, self._consumer_name)
        self._seen.add(event.event_id)

    def _persist(self, record: dict):
        """Append billing record to JSONL. Simple, auditable, replayable."""
        with self._lock:
            f = self._dir / "billing.jsonl"
            with open(f, "a", encoding="utf-8") as fp:
                fp.write(json.dumps(record, ensure_ascii=False, default=str) + "\n")

    def query(self, *, org_id: str = "", limit: int = 50) -> list[dict]:
        """Read recent billing records. Filterable by org_id."""
        records = []
        f = self._dir / "billing.jsonl"
        if not f.exists():
            return []
        with open(f, "r", encoding="utf-8") as fp:
            for line in fp:
                line = line.strip()
                if not line:
                    continue
                try:
                    r = json.loads(line)
                    if org_id and r.get("org_id", "") != org_id:
                        continue
                    records.append(r)
                    if len(records) >= limit:
                        break
                except Exception:
                    pass
        return records


# ── Singleton ────────────────────────────────────────────────────────────

_hook: BillingHookConsumer | None = None
_hook_lock = threading.Lock()


def get_billing_hook(bus=None) -> BillingHookConsumer:
    """Get the global BillingHookConsumer singleton. Creates one on first call."""
    global _hook
    with _hook_lock:
        if _hook is None:
            _hook = BillingHookConsumer(bus=bus)
        return _hook

"""
BillingHookConsumer — emit billing events on run completion. v2.4

Does NOT deduct balance. Does NOT implement invoicing.
Emits structured billing events that future billing systems consume.

Hook, not billing. Platform, not business logic.

Usage:
    from aitest.platform.billing_hook import BillingHookConsumer

    hook = BillingHookConsumer()
    hook.start()   # subscribes to run.completed + cost.recorded
"""

from __future__ import annotations

import json
import threading
from pathlib import Path
from datetime import datetime, timezone

from .consumer import RunEventConsumer
from .run_event import RunEvent, EventType, make_event
from .event_bus import get_bus


def _billing_dir() -> Path:
    base = Path(__file__).resolve().parent.parent.parent
    return base / "governance" / ".data" / "billing"


class BillingHookConsumer:
    """Emits billing events. Does NOT touch balance, invoicing, or payments.

    Consumes:
      - run.completed → emits billing.usage_recorded
      - cost.recorded  → emits billing.cost_recorded

    Future billing systems subscribe to billing.* events.
    """

    def __init__(self):
        self._dir = _billing_dir()
        self._dir.mkdir(parents=True, exist_ok=True)
        self._lock = threading.Lock()
        self._active = False
        self._seen: set[str] = set()  # Idempotency

    def start(self):
        if self._active:
            return
        bus = get_bus()
        bus.subscribe(EventType.RUN_COMPLETED, self._on_run_completed)
        bus.subscribe(EventType.COST_RECORDED, self._on_cost_recorded)
        self._active = True

    def stop(self):
        if not self._active:
            return
        bus = get_bus()
        bus.unsubscribe(EventType.RUN_COMPLETED, self._on_run_completed)
        bus.unsubscribe(EventType.COST_RECORDED, self._on_cost_recorded)
        self._active = False

    @property
    def is_active(self) -> bool:
        return self._active

    # ── Handlers ──────────────────────────────────────────────────────

    def _on_run_completed(self, event: RunEvent):
        """Emit billing.usage_recorded with run summary."""
        if event.event_id in self._seen:
            return
        self._seen.add(event.event_id)
        billing_event = {
            "event": "billing.usage_recorded",
            "run_id": event.run_id,
            "request_id": event.request_id,
            "org_id": event.data.get("org_id", ""),
            "workspace_id": event.data.get("workspace_id", ""),
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "usage": {
                "total_tokens": event.data.get("total_tokens", 0),
                "agent_runs": event.data.get("agent_runs", 0),
                "module": event.data.get("module", ""),
                "capability": "browser",
            },
        }
        self._persist(billing_event)
        # Re-emit as billing event for future consumers
        bus = get_bus()
        bus.publish(make_event(
            "billing.usage_recorded",
            run_id=event.run_id,
            request_id=event.request_id,
            **billing_event["usage"],
        ))

    def _on_cost_recorded(self, event: RunEvent):
        """Emit billing.cost_recorded."""
        if event.event_id in self._seen:
            return
        self._seen.add(event.event_id)
        billing_event = {
            "event": "billing.cost_recorded",
            "run_id": event.run_id,
            "request_id": event.request_id,
            "org_id": event.data.get("org_id", ""),
            "workspace_id": event.data.get("workspace_id", ""),
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "cost": {
                "amount": event.data.get("cost", 0.0),
                "currency": "USD",
                "tokens": event.data.get("tokens", 0),
            },
        }
        self._persist(billing_event)

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


def get_billing_hook() -> BillingHookConsumer:
    global _hook
    with _hook_lock:
        if _hook is None:
            _hook = BillingHookConsumer()
        return _hook

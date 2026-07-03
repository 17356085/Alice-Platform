"""
QuotaUsageConsumer — track resource usage per workspace. v2.4

Statistics only. No enforcement. Does NOT reject execution.
Quota enforcement comes later (v2.5+) — this builds the data it needs.

Tracks per workspace:
  - run_count (today, this month)
  - token_usage (today, this month)
  - storage_bytes (current)
  - last_updated

Usage:
    from aitest.platform.hooks.quota_usage import QuotaUsageConsumer

    qu = QuotaUsageConsumer()
    qu.start()
    usage = qu.get_usage("ws-1")
"""

from __future__ import annotations

import threading
from pathlib import Path
from datetime import datetime, timezone, date

from ..consumer import RunEventConsumer
from ..run_event import RunEvent, EventType, RunCompletedData, RunFailedData, EventDataKey as K
from ..event_bus import get_bus, PRIORITY_MEDIUM_HIGH
from ..run_store import get_run_store
from ..ttl_set import TTLSet
from ..config_registry import cfg


def _usage_dir() -> Path:
    return cfg.usage_dir


class QuotaUsageConsumer:
    """Tracks resource usage. Stats only. No enforcement.

    Args:
        store: RunStore instance. If None, uses get_run_store() singleton.
        bus: EventBus instance. If None, uses get_bus() singleton.
    """

    def __init__(self, store=None, bus=None):
        self._dir = _usage_dir()
        self._dir.mkdir(parents=True, exist_ok=True)
        self._lock = threading.Lock()
        self._active = False
        self._seen = TTLSet(max_size=10_000, max_age_s=86_400)  # Idempotency: 10k entries, 24h TTL
        self._usage: dict[str, dict] = {}  # workspace_id → counters
        self._MAX_USAGE_ENTRIES = 500  # RC2 fix: cap per-workspace entries
        self._store = store  # injected RunStore (None = lazy singleton)
        self._bus = bus       # injected EventBus (None = lazy singleton)

    def start(self):
        if self._active:
            return
        bus = self._bus or get_bus()
        bus.subscribe(EventType.RUN_COMPLETED, self._on_run_completed, priority=PRIORITY_MEDIUM_HIGH)  # after billing
        bus.subscribe(EventType.RUN_FAILED, self._on_run_completed, priority=PRIORITY_MEDIUM_HIGH)
        self._active = True

    def stop(self):
        if not self._active:
            return
        bus = self._bus or get_bus()
        bus.unsubscribe(EventType.RUN_COMPLETED, self._on_run_completed)
        bus.unsubscribe(EventType.RUN_FAILED, self._on_run_completed)
        self._active = False

    @property
    def is_active(self) -> bool:
        return self._active

    # ── Handler ───────────────────────────────────────────────────────

    def _on_run_completed(self, event: RunEvent):
        if not self._seen.add(event.event_id):
            return  # already processed (TTLSet atomic check-and-add)
        ws_id = event.data.get(K.WORKSPACE_ID, "")
        org_id = event.data.get(K.ORG_ID, "")
        tokens = event.data.get(K.TOTAL_TOKENS, 0)
        cost = event.data.get(K.TOTAL_COST, 0.0)

        with self._lock:
            # RC2 fix: LRU eviction if at capacity
            if ws_id not in self._usage and len(self._usage) >= self._MAX_USAGE_ENTRIES:
                oldest = min(self._usage.keys(),
                             key=lambda k: self._usage[k].get("last_updated", ""))
                del self._usage[oldest]

            if ws_id not in self._usage:
                self._usage[ws_id] = self._empty_usage(ws_id, org_id)

            u = self._usage[ws_id]
            u["run_count"] += 1
            u["token_usage"] += tokens
            u["cost_total"] += cost
            u["last_updated"] = datetime.now(timezone.utc).isoformat()

    @staticmethod
    def _empty_usage(workspace_id: str, org_id: str) -> dict:
        return {
            "workspace_id": workspace_id,
            "org_id": org_id,
            "run_count": 0,
            "token_usage": 0,
            "cost_total": 0.0,
            "storage_bytes": 0,
            "last_updated": "",
        }

    # ── Query ─────────────────────────────────────────────────────────

    def get_usage(self, workspace_id: str) -> dict:
        """Current usage for a workspace. Also counts from RunStore for accuracy."""
        with self._lock:
            usage = dict(self._usage.get(workspace_id, {}))
            if not usage:
                usage = self._empty_usage(workspace_id, "")

        # Cross-check with RunStore for total counts (more durable)
        try:
            store = self._store or get_run_store()
            count = store.count_runs(workspace_id=workspace_id)
            if count > usage.get("run_count", 0):
                usage["run_count_from_store"] = count
        except Exception:
            pass

        return usage

    def list_all(self) -> list[dict]:
        with self._lock:
            return list(self._usage.values())

    def snapshot(self) -> list[dict]:
        """All current usage, with RunStore cross-check."""
        return [self.get_usage(ws_id) for ws_id in self._usage]


# ── Singleton ────────────────────────────────────────────────────────────

_quota: QuotaUsageConsumer | None = None
_quota_lock = threading.Lock()


def get_quota_usage(store=None, bus=None) -> QuotaUsageConsumer:
    """Get the global QuotaUsageConsumer singleton. Creates one on first call.

    Args:
        store: RunStore instance to inject. Only used on first creation.
        bus: EventBus instance to inject. Only used on first creation.
    """
    global _quota
    with _quota_lock:
        if _quota is None:
            _quota = QuotaUsageConsumer(store=store, bus=bus)
        return _quota

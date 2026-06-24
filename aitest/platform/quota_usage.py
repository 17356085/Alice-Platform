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
    from aitest.platform.quota_usage import QuotaUsageConsumer

    qu = QuotaUsageConsumer()
    qu.start()
    usage = qu.get_usage("ws-1")
"""

from __future__ import annotations

import threading
from pathlib import Path
from datetime import datetime, timezone, date

from .consumer import RunEventConsumer
from .run_event import RunEvent, EventType
from .event_bus import get_bus
from .run_store import get_run_store


def _usage_dir() -> Path:
    base = Path(__file__).resolve().parent.parent.parent
    return base / "governance" / ".data" / "usage"


class QuotaUsageConsumer:
    """Tracks resource usage. Stats only. No enforcement."""

    def __init__(self):
        self._dir = _usage_dir()
        self._dir.mkdir(parents=True, exist_ok=True)
        self._lock = threading.Lock()
        self._active = False
        self._seen: set[str] = set()  # Idempotency
        self._usage: dict[str, dict] = {}  # workspace_id → counters

    def start(self):
        if self._active:
            return
        bus = get_bus()
        bus.subscribe(EventType.RUN_COMPLETED, self._on_run_completed)
        bus.subscribe(EventType.RUN_FAILED, self._on_run_completed)
        self._active = True

    def stop(self):
        if not self._active:
            return
        bus = get_bus()
        bus.unsubscribe(EventType.RUN_COMPLETED, self._on_run_completed)
        bus.unsubscribe(EventType.RUN_FAILED, self._on_run_completed)
        self._active = False

    @property
    def is_active(self) -> bool:
        return self._active

    # ── Handler ───────────────────────────────────────────────────────

    def _on_run_completed(self, event: RunEvent):
        if event.event_id in self._seen:
            return
        ws_id = event.data.get("workspace_id", "")
        org_id = event.data.get("org_id", "")
        tokens = event.data.get("total_tokens", 0)
        cost = event.data.get("total_cost", 0.0)

        with self._lock:
            self._seen.add(event.event_id)
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
            store = get_run_store()
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


def get_quota_usage() -> QuotaUsageConsumer:
    global _quota
    with _quota_lock:
        if _quota is None:
            _quota = QuotaUsageConsumer()
        return _quota

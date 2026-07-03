"""
MetricsConsumer — platform aggregate statistics. v3.1

Subscribes to run.completed and run.failed events.
Maintains in-memory counters + persists to PG metrics_daily table.

v3.1: Dual persistence — in-memory for real-time snapshot, PG for historical trends.

Usage:
    from aitest.platform.hooks.metrics_consumer import MetricsConsumer

    mc = MetricsConsumer()
    mc.start()   # subscribes to EventBus
    snap = mc.snapshot()   # current stats
    trends = mc.query_trends(days=7)  # historical from PG
"""

from __future__ import annotations

import threading
import time
from datetime import datetime, timezone

from ..consumer import RunEventConsumer
from ..run_event import RunEvent, EventType, RunCompletedData, RunFailedData, EventDataKey as K
from ..event_bus import get_bus
from ..ttl_set import TTLSet


class MetricsConsumer:
    """Aggregate execution metrics from RunEvents.

    Args:
        bus: EventBus instance. If None, uses get_bus() singleton.
    """

    def __init__(self, bus=None):
        self._lock = threading.Lock()
        self._active = False
        self._seen = TTLSet(max_size=10_000, max_age_s=86_400)  # Idempotency: 10k entries, 24h TTL
        self._bus = bus  # injected EventBus (None = lazy singleton)

        # Counters
        self._total_runs = 0
        self._completed_runs = 0
        self._failed_runs = 0
        self._cancelled_runs = 0
        self._total_tokens = 0
        self._total_cost = 0.0
        self._total_duration_ms = 0.0

        # Per-module breakdown — capped LRU eviction (RC2 fix)
        self._by_module: dict[str, dict] = {}  # module → {runs, completed, tokens, cost}
        self._by_agent: dict[str, dict] = {}   # agent → {runs, completed, tokens, cost}
        self._MAX_BY_MODULE = 200
        self._MAX_BY_AGENT = 200

    # ── Lifecycle ─────────────────────────────────────────────────────

    def start(self):
        if self._active:
            return
        bus = self._bus or get_bus()
        bus.subscribe(EventType.RUN_COMPLETED, self._on_run_completed, priority=20)  # NORMAL: aggregation
        bus.subscribe(EventType.RUN_FAILED, self._on_run_failed, priority=20)
        bus.subscribe(EventType.RUN_CANCELLED, self._on_run_cancelled, priority=20)
        self._active = True

    def stop(self):
        if not self._active:
            return
        bus = self._bus or get_bus()
        bus.unsubscribe(EventType.RUN_COMPLETED, self._on_run_completed)
        bus.unsubscribe(EventType.RUN_FAILED, self._on_run_failed)
        bus.unsubscribe(EventType.RUN_CANCELLED, self._on_run_cancelled)
        self._active = False

    @property
    def is_active(self) -> bool:
        return self._active

    # ── Handlers ──────────────────────────────────────────────────────

    def _on_run_completed(self, event: RunEvent):
        if not self._seen.add(event.event_id):
            return  # already processed (TTLSet atomic check-and-add)
        with self._lock:
            self._total_runs += 1
            self._completed_runs += 1
            self._accumulate(event)

    def _on_run_failed(self, event: RunEvent):
        if not self._seen.add(event.event_id):
            return
        with self._lock:
            self._total_runs += 1
            self._failed_runs += 1
            self._accumulate(event)

    def _on_run_cancelled(self, event: RunEvent):
        if not self._seen.add(event.event_id):
            return
        with self._lock:
            self._total_runs += 1
            self._cancelled_runs += 1

    def _accumulate(self, event: RunEvent):
        tokens = event.data.get(K.TOTAL_TOKENS, 0)
        cost = event.data.get(K.TOTAL_COST, 0.0)
        module = event.data.get(K.MODULE, "unknown")
        agent = event.data.get(K.AGENT, "unknown")
        org_id = event.data.get(K.ORG_ID, "")
        workspace_id = event.data.get(K.WORKSPACE_ID, "")
        is_completed = event.event_type == EventType.RUN_COMPLETED
        is_failed = event.event_type == EventType.RUN_FAILED

        self._total_tokens += tokens
        self._total_cost += cost

        now = time.monotonic()

        # By module — with LRU eviction cap (RC2 fix)
        if module not in self._by_module:
            if len(self._by_module) >= self._MAX_BY_MODULE:
                oldest = min(self._by_module.keys(),
                             key=lambda k: self._by_module[k].get("_last_ts", 0))
                del self._by_module[oldest]
            self._by_module[module] = {"runs": 0, "completed": 0, "failed": 0, "tokens": 0, "cost": 0.0}
        self._by_module[module]["runs"] += 1
        if is_completed:
            self._by_module[module]["completed"] += 1
        if is_failed:
            self._by_module[module]["failed"] += 1
        self._by_module[module]["tokens"] += tokens
        self._by_module[module]["cost"] += cost
        self._by_module[module]["_last_ts"] = now

        # By agent — with LRU eviction cap (RC2 fix)
        if agent not in self._by_agent:
            if len(self._by_agent) >= self._MAX_BY_AGENT:
                oldest = min(self._by_agent.keys(),
                             key=lambda k: self._by_agent[k].get("_last_ts", 0))
                del self._by_agent[oldest]
            self._by_agent[agent] = {"runs": 0, "completed": 0, "failed": 0, "tokens": 0, "cost": 0.0}
        self._by_agent[agent]["runs"] += 1
        if is_completed:
            self._by_agent[agent]["completed"] += 1
        if is_failed:
            self._by_agent[agent]["failed"] += 1
        self._by_agent[agent]["tokens"] += tokens
        self._by_agent[agent]["cost"] += cost
        self._by_agent[agent]["_last_ts"] = now

        # v3.1: Persist to PG for historical trends
        self._persist_to_pg(module, agent, org_id, workspace_id,
                            is_completed, is_failed, tokens, cost)

    # ── Snapshot ──────────────────────────────────────────────────────

    def snapshot(self) -> dict:
        with self._lock:
            return {
                "ts": datetime.now(timezone.utc).isoformat(),
                "runs": {
                    "total": self._total_runs,
                    "completed": self._completed_runs,
                    "failed": self._failed_runs,
                    "cancelled": self._cancelled_runs,
                    "success_rate": round(
                        self._completed_runs / self._total_runs, 3
                    ) if self._total_runs > 0 else 0,
                },
                "cost": {
                    "total_tokens": self._total_tokens,
                    "total_cost": round(self._total_cost, 4),
                    "avg_tokens_per_run": round(
                        self._total_tokens / self._total_runs, 1
                    ) if self._total_runs > 0 else 0,
                    "avg_cost_per_run": round(
                        self._total_cost / self._total_runs, 4
                    ) if self._total_runs > 0 else 0,
                },
                "by_module": self._by_module,
                "by_agent": self._by_agent,
            }

    # ── v3.1: PG persistence for historical trends ─────────────────
    # flush() removed — PG metrics_daily is now the source of truth.
    # JSONL backup removed to reduce maintenance burden.

    def _persist_to_pg(self, module: str, agent: str, org_id: str,
                       workspace_id: str, is_completed: bool, is_failed: bool,
                       tokens: int, cost: float):
        """Upsert daily metrics to PG metrics_daily table."""
        try:
            from aitest.infra.sql import safe_exec, safe_query
            today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
            now = datetime.now(timezone.utc).isoformat()

            # Try update first
            safe_exec(
                "UPDATE metrics_daily SET "
                "run_count = run_count + 1, "
                "completed_count = completed_count + ?, "
                "failed_count = failed_count + ?, "
                "total_tokens = total_tokens + ?, "
                "total_cost = total_cost + ? "
                "WHERE date = ? AND module = ? AND agent = ? AND org_id = ? AND workspace_id = ?",
                [1 if is_completed else 0, 1 if is_failed else 0,
                 tokens, cost, today, module, agent, org_id, workspace_id],
            )

            # If no rows updated, insert
            rows = safe_query(
                "SELECT COUNT(*) as cnt FROM metrics_daily "
                "WHERE date = ? AND module = ? AND agent = ? AND org_id = ? AND workspace_id = ?",
                [today, module, agent, org_id, workspace_id],
            )
            if rows and rows[0]["cnt"] == 0:
                safe_exec(
                    "INSERT INTO metrics_daily "
                    "(date, module, agent, org_id, workspace_id, run_count, completed_count, "
                    "failed_count, total_tokens, total_cost, created_at) "
                    "VALUES (?, ?, ?, ?, ?, 1, ?, ?, ?, ?, ?)",
                    [today, module, agent, org_id, workspace_id,
                     1 if is_completed else 0, 1 if is_failed else 0,
                     tokens, cost, now],
                )
        except Exception:
            pass  # Best-effort: don't break event processing if PG fails

    def query_trends(self, days: int = 7, module: str = "") -> list[dict]:
        """Query historical metrics from PG.

        Args:
            days: Number of days to look back
            module: Filter by module (optional)

        Returns:
            List of daily metrics records
        """
        from aitest.infra.sql import safe_query
        from datetime import timedelta

        since = (datetime.now(timezone.utc) - timedelta(days=days)).strftime("%Y-%m-%d")
        if module:
            return safe_query(
                "SELECT * FROM metrics_daily WHERE date >= ? AND module = ? "
                "ORDER BY date DESC, module, agent",
                [since, module],
            )
        return safe_query(
            "SELECT * FROM metrics_daily WHERE date >= ? "
            "ORDER BY date DESC, module, agent",
            [since],
        )


# ── Singleton ────────────────────────────────────────────────────────────

_metrics: MetricsConsumer | None = None
_metrics_lock = threading.Lock()


def get_metrics_consumer(bus=None) -> MetricsConsumer:
    """Get the global MetricsConsumer singleton. Creates one on first call."""
    global _metrics
    with _metrics_lock:
        if _metrics is None:
            _metrics = MetricsConsumer(bus=bus)
        return _metrics

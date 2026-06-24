"""
MetricsConsumer — platform aggregate statistics. v2.4

Subscribes to run.completed and run.failed events.
Maintains in-memory counters. Periodically flushes to JSONL for trending.

Pure consumer. No effect on execution. No new abstractions.

Usage:
    from aitest.platform.metrics_consumer import MetricsConsumer

    mc = MetricsConsumer()
    mc.start()   # subscribes to EventBus
    snap = mc.snapshot()   # current stats
"""

from __future__ import annotations

import json
import threading
import time
from pathlib import Path
from datetime import datetime, timezone

from .consumer import RunEventConsumer
from .run_event import RunEvent, EventType
from .event_bus import get_bus


def _metrics_dir() -> Path:
    base = Path(__file__).resolve().parent.parent.parent
    return base / "governance" / ".data" / "metrics"


class MetricsConsumer:
    """Aggregate execution metrics from RunEvents."""

    def __init__(self):
        self._dir = _metrics_dir()
        self._dir.mkdir(parents=True, exist_ok=True)
        self._lock = threading.Lock()
        self._active = False
        self._seen: set[str] = set()  # Idempotency: track processed event_ids

        # Counters
        self._total_runs = 0
        self._completed_runs = 0
        self._failed_runs = 0
        self._cancelled_runs = 0
        self._total_tokens = 0
        self._total_cost = 0.0
        self._total_duration_ms = 0.0

        # Per-module breakdown
        self._by_module: dict[str, dict] = {}  # module → {runs, completed, tokens, cost}
        self._by_agent: dict[str, dict] = {}   # agent → {runs, completed, tokens, cost}

    # ── Lifecycle ─────────────────────────────────────────────────────

    def start(self):
        if self._active:
            return
        bus = get_bus()
        bus.subscribe(EventType.RUN_COMPLETED, self._on_run_completed)
        bus.subscribe(EventType.RUN_FAILED, self._on_run_failed)
        bus.subscribe(EventType.RUN_CANCELLED, self._on_run_cancelled)
        self._active = True

    def stop(self):
        if not self._active:
            return
        bus = get_bus()
        bus.unsubscribe(EventType.RUN_COMPLETED, self._on_run_completed)
        bus.unsubscribe(EventType.RUN_FAILED, self._on_run_failed)
        bus.unsubscribe(EventType.RUN_CANCELLED, self._on_run_cancelled)
        self._active = False

    @property
    def is_active(self) -> bool:
        return self._active

    # ── Handlers ──────────────────────────────────────────────────────

    def _on_run_completed(self, event: RunEvent):
        if event.event_id in self._seen:
            return
        with self._lock:
            self._seen.add(event.event_id)
            self._total_runs += 1
            self._completed_runs += 1
            self._accumulate(event)

    def _on_run_failed(self, event: RunEvent):
        if event.event_id in self._seen:
            return
        with self._lock:
            self._seen.add(event.event_id)
            self._total_runs += 1
            self._failed_runs += 1
            self._accumulate(event)

    def _on_run_cancelled(self, event: RunEvent):
        if event.event_id in self._seen:
            return
        with self._lock:
            self._seen.add(event.event_id)
            self._total_runs += 1
            self._cancelled_runs += 1

    def _accumulate(self, event: RunEvent):
        tokens = event.data.get("total_tokens", 0)
        cost = event.data.get("total_cost", 0.0)
        module = event.data.get("module", "unknown")
        agent = event.data.get("agent", "unknown")

        self._total_tokens += tokens
        self._total_cost += cost

        # By module
        if module not in self._by_module:
            self._by_module[module] = {"runs": 0, "completed": 0, "tokens": 0, "cost": 0.0}
        self._by_module[module]["runs"] += 1
        self._by_module[module]["completed"] += 1
        self._by_module[module]["tokens"] += tokens
        self._by_module[module]["cost"] += cost

        # By agent
        if agent not in self._by_agent:
            self._by_agent[agent] = {"runs": 0, "completed": 0, "tokens": 0, "cost": 0.0}
        self._by_agent[agent]["runs"] += 1
        self._by_agent[agent]["completed"] += 1
        self._by_agent[agent]["tokens"] += tokens
        self._by_agent[agent]["cost"] += cost

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

    def flush(self):
        """Write current snapshot to JSONL for trending."""
        snap = self.snapshot()
        self._dir.mkdir(parents=True, exist_ok=True)
        file = self._dir / "metrics.jsonl"
        with open(file, "a", encoding="utf-8") as f:
            f.write(json.dumps(snap, ensure_ascii=False, default=str) + "\n")


# ── Singleton ────────────────────────────────────────────────────────────

_metrics: MetricsConsumer | None = None
_metrics_lock = threading.Lock()


def get_metrics_consumer() -> MetricsConsumer:
    global _metrics
    with _metrics_lock:
        if _metrics is None:
            _metrics = MetricsConsumer()
        return _metrics

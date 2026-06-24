"""
Operational Metrics — 8 runtime KPIs for data-driven platform evolution.

Tracks:
  1. p95 Agent Latency      — histogram per agent
  2. Token Cost / Task       — counter per agent × direction
  3. Workflow Success Rate   — counter per module × status
  4. Plugin Failure Rate     — counter per plugin × status
  5. Memory Hit Rate         — counter per collection × hit/miss
  6. Recovery Success Rate   — counter per agent × recovered/failed
  7. Phase Distribution      — histogram per agent × phase
  8. Cost per Capability     — counter per capability × tokens/duration

Design:
  - Thread-safe in-memory counters + histograms
  - JSONL persistence for long-term trending
  - Prometheus-compatible via metrics.py integration
  - Exposed via /api/kpi/operational endpoint

Usage:
    from aitest.platform.operational_metrics import MetricsCollector, get_collector

    mc = get_collector()
    mc.record_agent_run("automation-agent", duration_s=12.3, tokens_in=500, tokens_out=200, success=True)
    mc.record_workflow("equipment", success=True)
    mc.record_plugin("browser", success=True)
    mc.snapshot()  # → dict with all current values
"""

import json
import time
import threading
from pathlib import Path
from datetime import datetime, timezone
from typing import Optional
from collections import defaultdict


# ── Persistence ────────────────────────────────────────────────────────

_WORKSTUDY = Path(__file__).resolve().parent.parent.parent
_METRICS_DIR = _WORKSTUDY / "governance" / "kpi" / "timeseries"
_METRICS_FILE = _METRICS_DIR / "operational_metrics.jsonl"


def _ensure_dir():
    _METRICS_DIR.mkdir(parents=True, exist_ok=True)


# ── Histogram helper ───────────────────────────────────────────────────

class _Histogram:
    """Simple fixed-bucket histogram for p95 calculation."""

    def __init__(self, buckets: list[float] = None):
        self.buckets = buckets or [1, 5, 10, 30, 60, 120, 300, 600, 1200]
        self.counts = [0] * len(self.buckets)
        self.total = 0
        self.sum_values = 0.0
        self._lock = threading.Lock()

    def observe(self, value: float):
        with self._lock:
            self.total += 1
            self.sum_values += value
            for i, b in enumerate(self.buckets):
                if value <= b:
                    self.counts[i] += 1
                    break

    def p95(self) -> float:
        """Estimate p95 from bucket counts."""
        with self._lock:
            if self.total == 0:
                return 0.0
            target = int(self.total * 0.95)
            cumulative = 0
            for i, c in enumerate(self.counts):
                cumulative += c
                if cumulative >= target:
                    return self.buckets[i]
            return self.buckets[-1]

    def snapshot(self) -> dict:
        with self._lock:
            return {
                "total": self.total,
                "p95": self.p95(),
                "avg": round(self.sum_values / self.total, 2) if self.total > 0 else 0,
                "buckets": dict(zip([str(b) for b in self.buckets], self.counts)),
            }


# ── Metrics Collector ──────────────────────────────────────────────────

class MetricsCollector:
    """Singleton collector for all 8 operational KPIs."""

    def __init__(self):
        self._lock = threading.Lock()

        # 1. Agent latency — histogram per agent
        self._agent_latency: dict[str, _Histogram] = defaultdict(_Histogram)

        # 2. Token cost — counters per agent
        self._token_cost: dict[str, dict] = defaultdict(lambda: {"input": 0, "output": 0, "cost_est": 0.0})

        # 3. Workflow success — counter per module
        self._workflow: dict[str, dict] = defaultdict(lambda: {"success": 0, "failed": 0, "total": 0})

        # 4. Plugin failure — counter per plugin
        self._plugin: dict[str, dict] = defaultdict(lambda: {"success": 0, "failed": 0, "total": 0})

        # 5. Memory hit — counter per collection
        self._memory_hit: dict[str, dict] = defaultdict(lambda: {"hits": 0, "misses": 0, "total": 0})

        # 6. Recovery — counter per agent
        self._recovery: dict[str, dict] = defaultdict(lambda: {"attempted": 0, "recovered": 0, "failed": 0})

        # 7. Phase distribution — histogram per agent per phase
        self._phase_time: dict[str, _Histogram] = defaultdict(_Histogram)

        # 8. Cost per capability
        self._capability_cost: dict[str, dict] = defaultdict(lambda: {"tokens": 0, "duration_ms": 0.0, "calls": 0, "success": 0, "failed": 0})

        self._started_at = time.time()

    # ── Record methods ────────────────────────────────────────────────

    def record_agent_run(self, agent: str, duration_s: float, tokens_in: int, tokens_out: int, success: bool):
        with self._lock:
            self._agent_latency[agent].observe(duration_s)
            tc = self._token_cost[agent]
            tc["input"] += tokens_in
            tc["output"] += tokens_out
            tc["cost_est"] += self._estimate_cost(agent, tokens_in, tokens_out)

    def record_phase(self, agent: str, phase: str, duration_s: float):
        key = f"{agent}:{phase}"
        with self._lock:
            self._phase_time[key].observe(duration_s)

    def record_workflow(self, module: str, success: bool):
        with self._lock:
            wf = self._workflow[module]
            wf["total"] += 1
            if success:
                wf["success"] += 1
            else:
                wf["failed"] += 1

    def record_plugin(self, plugin: str, success: bool):
        with self._lock:
            p = self._plugin[plugin]
            p["total"] += 1
            if success:
                p["success"] += 1
            else:
                p["failed"] += 1

    def record_memory(self, collection: str, hit: bool):
        with self._lock:
            m = self._memory_hit[collection]
            m["total"] += 1
            if hit:
                m["hits"] += 1
            else:
                m["misses"] += 1

    def record_recovery(self, agent: str, recovered: bool):
        with self._lock:
            r = self._recovery[agent]
            r["attempted"] += 1
            if recovered:
                r["recovered"] += 1
            else:
                r["failed"] += 1

    def record_capability(self, capability: str, tokens: int, duration_ms: float, success: bool):
        with self._lock:
            c = self._capability_cost[capability]
            c["tokens"] += tokens
            c["duration_ms"] += duration_ms
            c["calls"] += 1
            if success:
                c["success"] += 1
            else:
                c["failed"] += 1

    # ── Query ──────────────────────────────────────────────────────────

    def snapshot(self) -> dict:
        """Full operational metrics snapshot."""
        with self._lock:
            # 1. Agent latency (p95 per agent)
            agent_latency = {a: h.snapshot() for a, h in self._agent_latency.items()}

            # 2. Token cost
            token_cost = dict(self._token_cost)

            # 3. Workflow success rate
            workflow = {}
            for m, v in self._workflow.items():
                total = v["total"]
                workflow[m] = {
                    "total": total,
                    "success": v["success"],
                    "failed": v["failed"],
                    "rate": round(v["success"] / total, 3) if total > 0 else 0,
                }

            # 4. Plugin failure rate
            plugin = {}
            for p, v in self._plugin.items():
                total = v["total"]
                plugin[p] = {
                    "total": total,
                    "success": v["success"],
                    "failed": v["failed"],
                    "failure_rate": round(v["failed"] / total, 4) if total > 0 else 0,
                }

            # 5. Memory hit rate
            memory = {}
            for c, v in self._memory_hit.items():
                total = v["total"]
                memory[c] = {
                    "total": total,
                    "hits": v["hits"],
                    "misses": v["misses"],
                    "hit_rate": round(v["hits"] / total, 3) if total > 0 else 0,
                }

            # 6. Recovery success rate
            recovery = {}
            for a, v in self._recovery.items():
                attempted = v["attempted"]
                recovery[a] = {
                    "attempted": attempted,
                    "recovered": v["recovered"],
                    "failed": v["failed"],
                    "rate": round(v["recovered"] / attempted, 3) if attempted > 0 else 0,
                }

            # 7. Phase distribution
            phase = {k: h.snapshot() for k, h in self._phase_time.items()}

            # 8. Cost per capability
            capability = {}
            for cap, v in self._capability_cost.items():
                calls = v["calls"]
                capability[cap] = {
                    "calls": calls,
                    "tokens_total": v["tokens"],
                    "tokens_avg": round(v["tokens"] / calls, 0) if calls > 0 else 0,
                    "duration_avg_ms": round(v["duration_ms"] / calls, 1) if calls > 0 else 0,
                    "success": v["success"],
                    "failed": v["failed"],
                    "success_rate": round(v["success"] / calls, 3) if calls > 0 else 0,
                }

            return {
                "ts": datetime.now(timezone.utc).isoformat(),
                "uptime_s": round(time.time() - self._started_at, 0),
                "agent_latency_p95": agent_latency,
                "token_cost": token_cost,
                "workflow": workflow,
                "plugin": plugin,
                "memory": memory,
                "recovery": recovery,
                "phase_distribution": phase,
                "capability_cost": capability,
            }

    def persist(self):
        """Write current snapshot to JSONL for long-term trending."""
        try:
            _ensure_dir()
            snap = self.snapshot()
            with open(_METRICS_FILE, "a", encoding="utf-8") as f:
                f.write(json.dumps(snap, ensure_ascii=False, default=str) + "\n")
        except Exception:
            pass  # metrics persistence is best-effort

    def _estimate_cost(self, agent: str, tokens_in: int, tokens_out: int) -> float:
        """Rough cost estimate. Calibrate with actual provider pricing."""
        # Claude Sonnet pricing (approx): $3/M input, $15/M output
        return (tokens_in / 1_000_000) * 3.0 + (tokens_out / 1_000_000) * 15.0


# ── Singleton ──────────────────────────────────────────────────────────

_collector: Optional[MetricsCollector] = None
_collector_lock = threading.Lock()


def get_collector() -> MetricsCollector:
    global _collector
    with _collector_lock:
        if _collector is None:
            _collector = MetricsCollector()
        return _collector

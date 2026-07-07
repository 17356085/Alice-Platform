"""Tests for platform/operational_metrics.py — 8 runtime KPIs.

Tests: _Histogram (observe, p95, snapshot), MetricsCollector
(record_agent_run, record_workflow, record_plugin, record_memory,
record_recovery, record_capability, snapshot).
Pure in-memory — no external dependencies.
"""
import pytest

from aitest.platform.operational_metrics import (
    _Histogram, MetricsCollector,
)


# ══════════════════════════════════════════════════════════════════════════
#  _Histogram
# ══════════════════════════════════════════════════════════════════════════


class TestHistogram:
    def test_initial_state(self):
        h = _Histogram()
        assert h.total == 0
        assert h.p95() == 0.0

    def test_observe_single(self):
        h = _Histogram()
        h.observe(5.0)
        assert h.total == 1

    def test_observe_multiple(self):
        h = _Histogram()
        for v in [1, 5, 10, 30, 60]:
            h.observe(v)
        assert h.total == 5

    def test_p95_estimation(self):
        h = _Histogram()
        # 100 values, all 1s → p95 should be 1
        for _ in range(100):
            h.observe(1.0)
        assert h.p95() == 1.0

    def test_p95_with_outliers(self):
        h = _Histogram()
        # 95 values at 1s, 5 values at 60s
        for _ in range(95):
            h.observe(1.0)
        for _ in range(5):
            h.observe(60.0)
        assert h.p95() >= 1.0

    def test_snapshot_structure(self):
        h = _Histogram()
        h.observe(5.0)
        snap = h.snapshot()
        assert "total" in snap
        assert "p95" in snap
        assert "avg" in snap
        assert "buckets" in snap
        assert snap["total"] == 1

    def test_snapshot_avg(self):
        h = _Histogram()
        h.observe(10.0)
        h.observe(20.0)
        snap = h.snapshot()
        assert snap["avg"] == 15.0

    def test_custom_buckets(self):
        h = _Histogram(buckets=[0.1, 1.0, 10.0])
        h.observe(0.5)
        h.observe(5.0)
        h.observe(15.0)
        assert h.total == 3


# ══════════════════════════════════════════════════════════════════════════
#  MetricsCollector — record methods
# ══════════════════════════════════════════════════════════════════════════


class TestRecordAgentRun:
    def test_records_latency(self):
        mc = MetricsCollector()
        mc.record_agent_run("test-agent", duration_s=12.3, tokens_in=500, tokens_out=200, success=True)
        snap = mc.snapshot()
        assert "test-agent" in snap["agent_latency_p95"]

    def test_records_tokens(self):
        mc = MetricsCollector()
        mc.record_agent_run("test-agent", duration_s=10.0, tokens_in=1000, tokens_out=500, success=True)
        snap = mc.snapshot()
        tc = snap["token_cost"]["test-agent"]
        assert tc["input"] == 1000
        assert tc["output"] == 500


class TestRecordWorkflow:
    def test_success(self):
        mc = MetricsCollector()
        mc.record_workflow("equipment", success=True)
        snap = mc.snapshot()
        wf = snap["workflow"]["equipment"]
        assert wf["success"] == 1
        assert wf["failed"] == 0
        assert wf["rate"] == 1.0

    def test_failure(self):
        mc = MetricsCollector()
        mc.record_workflow("equipment", success=False)
        snap = mc.snapshot()
        wf = snap["workflow"]["equipment"]
        assert wf["success"] == 0
        assert wf["failed"] == 1

    def test_mixed(self):
        mc = MetricsCollector()
        mc.record_workflow("equipment", success=True)
        mc.record_workflow("equipment", success=False)
        snap = mc.snapshot()
        wf = snap["workflow"]["equipment"]
        assert wf["total"] == 2
        assert wf["rate"] == 0.5


class TestRecordPlugin:
    def test_success(self):
        mc = MetricsCollector()
        mc.record_plugin("browser", success=True)
        snap = mc.snapshot()
        p = snap["plugin"]["browser"]
        assert p["success"] == 1


class TestRecordMemory:
    def test_hit(self):
        mc = MetricsCollector()
        mc.record_memory("page_objects", hit=True)
        snap = mc.snapshot()
        m = snap["memory"]["page_objects"]
        assert m["hits"] == 1
        assert m["hit_rate"] == 1.0

    def test_miss(self):
        mc = MetricsCollector()
        mc.record_memory("page_objects", hit=False)
        snap = mc.snapshot()
        m = snap["memory"]["page_objects"]
        assert m["misses"] == 1


class TestRecordRecovery:
    def test_recovered(self):
        mc = MetricsCollector()
        mc.record_recovery("automation-agent", recovered=True)
        snap = mc.snapshot()
        r = snap["recovery"]["automation-agent"]
        assert r["recovered"] == 1
        assert r["failed"] == 0


class TestRecordCapability:
    def test_records_tokens_and_duration(self):
        mc = MetricsCollector()
        mc.record_capability("browser.navigate", tokens=100, duration_ms=500.0, success=True)
        snap = mc.snapshot()
        c = snap["capability_cost"]["browser.navigate"]
        assert c["tokens"] == 100
        assert c["duration_ms"] == 500.0
        assert c["calls"] == 1
        assert c["success"] == 1


class TestRecordExecution:
    def test_records_execution_rollup(self):
        mc = MetricsCollector()
        mc.record_execution(
            agent="automation-agent",
            module="sales",
            duration_s=12.5,
            total_tokens=300,
            total_cost=0.42,
            success=True,
            retry_count=1,
            max_retries=3,
        )
        snap = mc.snapshot()
        assert "automation-agent" in snap["agent_latency_p95"]
        assert snap["workflow"]["sales"]["success"] == 1
        assert snap["capability_cost"]["automation-agent"]["calls"] == 1


# ══════════════════════════════════════════════════════════════════════════
#  MetricsCollector — snapshot
# ══════════════════════════════════════════════════════════════════════════


class TestSnapshot:
    def test_snapshot_structure(self):
        mc = MetricsCollector()
        snap = mc.snapshot()
        assert "agent_latency_p95" in snap
        assert "token_cost" in snap
        assert "workflow" in snap
        assert "plugin" in snap
        assert "memory" in snap
        assert "recovery" in snap
        assert "phase_distribution" in snap
        assert "capability_cost" in snap
        assert "uptime_s" in snap

    def test_empty_snapshot(self):
        mc = MetricsCollector()
        snap = mc.snapshot()
        assert snap["workflow"] == {}
        assert snap["plugin"] == {}

    def test_multiple_agents(self):
        mc = MetricsCollector()
        mc.record_agent_run("agent-a", 10.0, 100, 50, True)
        mc.record_agent_run("agent-b", 20.0, 200, 100, True)
        snap = mc.snapshot()
        assert "agent-a" in snap["agent_latency_p95"]
        assert "agent-b" in snap["agent_latency_p95"]

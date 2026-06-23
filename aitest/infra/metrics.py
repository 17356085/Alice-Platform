"""
Prometheus Metrics — operational metrics for the AITest Platform.

Exposes a /metrics endpoint on the FastAPI server. Metrics track:
  - LLM calls (count, duration, tokens) by provider
  - Agent executions (count, success/fail) by agent name
  - SOP runs (count, duration) by module
  - Error counts by component
  - Circuit breaker state
  - Active agents (gauge)
  - HTTP requests (count, duration) by endpoint

Usage:
    from aitest.infra.metrics import (
        llm_call_counter, agent_execution_counter, sop_run_histogram
    )
    llm_call_counter.labels(provider="claude", status="success").inc()

Enable: prometheus_client must be installed (optional dependency).
If not installed, all metrics are no-ops.

Endpoint: GET /metrics (Prometheus text format)
"""

import time
from functools import wraps
from typing import Optional

_METRICS_AVAILABLE = False

try:
    from prometheus_client import Counter, Gauge, Histogram, generate_latest, REGISTRY
    _METRICS_AVAILABLE = True
except ImportError:
    pass


# ── No-op fallbacks ────────────────────────────────────────────────────

class _NoopMetric:
    """No-op metric — all methods do nothing."""
    def labels(self, **kwargs): return self
    def inc(self, amount=1): pass
    def dec(self, amount=1): pass
    def set(self, value): pass
    def observe(self, value): pass
    def time(self): return _NoopTimer()


class _NoopTimer:
    def __enter__(self): return self
    def __exit__(self, *args): pass


def _make_counter(name, doc, labels) -> Counter | _NoopMetric:
    if _METRICS_AVAILABLE:
        return Counter(name, doc, labels)
    return _NoopMetric()


def _make_gauge(name, doc, labels) -> Gauge | _NoopMetric:
    if _METRICS_AVAILABLE:
        return Gauge(name, doc, labels)
    return _NoopMetric()


def _make_histogram(name, doc, labels, buckets=None) -> Histogram | _NoopMetric:
    if _METRICS_AVAILABLE:
        return Histogram(name, doc, labels, buckets=buckets or Histogram.DEFAULT_BUCKETS)
    return _NoopMetric()


# ── Metric Definitions ─────────────────────────────────────────────────

# LLM calls
llm_call_total = _make_counter(
    "aitest_llm_calls_total",
    "Total LLM calls by provider and status",
    ["provider", "status"],
)
llm_call_duration = _make_histogram(
    "aitest_llm_call_duration_seconds",
    "LLM call duration in seconds by provider",
    ["provider"],
    buckets=[0.5, 1, 2, 5, 10, 30, 60, 120],
)
llm_token_usage = _make_counter(
    "aitest_llm_tokens_total",
    "Total tokens used by provider and direction",
    ["provider", "direction"],  # input / output
)

# Agent executions
agent_execution_total = _make_counter(
    "aitest_agent_executions_total",
    "Total agent executions by name and status",
    ["agent_name", "status"],
)
agent_active = _make_gauge(
    "aitest_agent_active",
    "Currently running agents",
    ["agent_name"],
)
agent_execution_duration = _make_histogram(
    "aitest_agent_execution_duration_seconds",
    "Agent execution duration in seconds",
    ["agent_name"],
    buckets=[10, 30, 60, 120, 300, 600, 1200],
)

# SOP runs
sop_run_total = _make_counter(
    "aitest_sop_runs_total",
    "Total SOP runs by module and status",
    ["module", "status"],
)
sop_run_duration = _make_histogram(
    "aitest_sop_run_duration_seconds",
    "SOP run duration in seconds",
    ["module"],
    buckets=[30, 60, 120, 300, 600, 1200, 3600],
)

# Errors
error_total = _make_counter(
    "aitest_errors_total",
    "Total errors by component and severity",
    ["component", "severity"],
)

# HTTP
http_request_total = _make_counter(
    "aitest_http_requests_total",
    "Total HTTP requests by method and path",
    ["method", "path", "status"],
)
http_request_duration = _make_histogram(
    "aitest_http_request_duration_seconds",
    "HTTP request duration in seconds",
    ["method", "path"],
)

# Circuit breaker
cb_state = _make_gauge(
    "aitest_circuit_breaker_state",
    "Circuit breaker state (0=closed, 1=half_open, 2=open)",
    ["name"],
)


# ── Helper: timed decorator for histograms ────────────────────────────

def track_llm_call(provider: str):
    """Context manager or decorator: track LLM call duration + count."""
    class _Tracker:
        def __enter__(self):
            self._start = time.time()
            return self

        def __exit__(self, exc_type, exc_val, exc_tb):
            duration = time.time() - self._start
            status = "error" if exc_type else "success"
            llm_call_total.labels(provider=provider, status=status).inc()
            llm_call_duration.labels(provider=provider).observe(duration)

        def record_tokens(self, input_tokens: int, output_tokens: int):
            llm_token_usage.labels(provider=provider, direction="input").inc(input_tokens)
            llm_token_usage.labels(provider=provider, direction="output").inc(output_tokens)

    return _Tracker()


def track_agent_execution(agent_name: str):
    """Context manager: track agent execution duration + status."""
    class _Tracker:
        def __enter__(self):
            self._start = time.monotonic()
            agent_active.labels(agent_name=agent_name).inc()
            return self

        def __exit__(self, exc_type, exc_val, exc_tb):
            duration = time.monotonic() - self._start
            status = "error" if exc_type else "success"
            agent_execution_total.labels(agent_name=agent_name, status=status).inc()
            agent_execution_duration.labels(agent_name=agent_name).observe(duration)
            agent_active.labels(agent_name=agent_name).dec()

    return _Tracker()


def update_cb_metrics():
    """Update circuit breaker gauge from current state."""
    try:
        from aitest.llm.circuit_breaker import get_all_metrics
        for m in get_all_metrics():
            state_map = {"closed": 0, "half_open": 1, "open": 2}
            cb_state.labels(name=m["name"]).set(state_map.get(m["state"], -1))
    except Exception:
        pass


# ── Prometheus endpoint handler ────────────────────────────────────────

def get_metrics_response() -> tuple[str, int, dict]:
    """Return Prometheus metrics in text format. Suitable for FastAPI endpoint."""
    if not _METRICS_AVAILABLE:
        return (
            "# AITest Metrics\n# prometheus_client not installed. pip install prometheus-client\n",
            200,
            {"Content-Type": "text/plain; charset=utf-8"},
        )

    update_cb_metrics()
    return (
        generate_latest(REGISTRY).decode("utf-8"),
        200,
        {"Content-Type": "text/plain; charset=utf-8"},
    )

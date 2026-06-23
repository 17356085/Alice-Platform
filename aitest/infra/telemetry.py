"""
OpenTelemetry integration — distributed tracing for AITest Platform.

Additive to existing trace.py (JSONL local tracing). When enabled, spans
are exported to an OTLP-compatible backend (Jaeger, Tempo, Grafana Cloud).

Enable:   AITEST_OTEL_ENABLED=true
Endpoint: AITEST_OTEL_ENDPOINT=http://localhost:4317  (default)

Usage:
    from aitest.infra.telemetry import tracer, traced, get_tracer

    # Decorator
    @traced("agent_execution")
    def run_agent(module, page):
        ...

    # Manual span
    with tracer.start_as_current_span("llm_call") as span:
        span.set_attribute("provider", "claude")
        result = llm.complete(...)
        span.set_attribute("tokens", result.token_usage.get("total", 0))

Design:
  - Disabled by default (no otel import unless enabled)
  - Graceful degradation: if otel not installed, no-op
  - Bridges existing trace.py events (shared run_id/agent_name context)
"""

import os
import functools
from contextlib import contextmanager
from typing import Optional, Callable

_ENABLED = os.environ.get("AITEST_OTEL_ENABLED", "").lower() in ("1", "true", "yes")
_OTEL_AVAILABLE = False

_tracer = None


def _init_otel():
    """Lazy-init OpenTelemetry SDK. Called on first use if enabled."""
    global _OTEL_AVAILABLE, _tracer

    if _tracer is not None:
        return

    if not _ENABLED:
        _tracer = _NoopTracer()
        return

    try:
        from opentelemetry import trace
        from opentelemetry.sdk.trace import TracerProvider
        from opentelemetry.sdk.resources import Resource, SERVICE_NAME
        from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
        from opentelemetry.sdk.trace.export import BatchSpanProcessor

        endpoint = os.environ.get("AITEST_OTEL_ENDPOINT", "http://localhost:4317")
        resource = Resource(attributes={
            SERVICE_NAME: "aitest-platform",
            "service.version": "0.2.0",
        })

        provider = TracerProvider(resource=resource)
        exporter = OTLPSpanExporter(endpoint=endpoint, insecure=True)
        provider.add_span_processor(BatchSpanProcessor(exporter))
        trace.set_tracer_provider(provider)

        _tracer = trace.get_tracer("aitest")
        _OTEL_AVAILABLE = True

    except ImportError:
        _tracer = _NoopTracer()
    except Exception:
        _tracer = _NoopTracer()


# ── No-op tracer (when otel disabled or unavailable) ──────────────────

class _NoopSpan:
    """No-op span — supports context manager protocol."""
    def __enter__(self): return self
    def __exit__(self, *args): pass
    async def __aenter__(self): return self
    async def __aexit__(self, *args): pass
    def set_attribute(self, key, value): pass
    def set_status(self, status): pass
    def record_exception(self, exception): pass
    def add_event(self, name, attributes=None): pass
    def end(self): pass


class _NoopTracer:
    """No-op tracer — all methods return no-op spans."""
    def start_as_current_span(self, name, **kwargs):
        return _NoopSpan()
    def start_span(self, name, **kwargs):
        return _NoopSpan()

    @contextmanager
    def start_as_current_span_ctx(self, name, **kwargs):
        yield _NoopSpan()


# ── Public API ────────────────────────────────────────────────────────

def get_tracer():
    """Get the (possibly no-op) OpenTelemetry tracer."""
    _init_otel()
    return _tracer


# Singleton tracer instance (lazy-init)
class _LazyTracer:
    def __getattr__(self, name):
        _init_otel()
        return getattr(_tracer, name)


tracer = _LazyTracer()


def traced(name: str = None, attrs: dict = None):
    """Decorator: wrap function in an OpenTelemetry span.

    Usage:
        @traced("sop_phase_execution")
        def execute_phase(state, phase):
            ...

        @traced  # uses __name__
        def process_page(page):
            ...
    """
    def decorator(fn: Callable):
        span_name = name or fn.__qualname__

        @functools.wraps(fn)
        def wrapper(*args, **kwargs):
            with get_tracer().start_as_current_span(span_name) as span:
                if attrs:
                    for k, v in attrs.items():
                        span.set_attribute(k, v)
                try:
                    return fn(*args, **kwargs)
                except Exception as e:
                    span.record_exception(e)
                    span.set_status({"status": "error"})
                    raise

        @functools.wraps(fn)
        async def async_wrapper(*args, **kwargs):
            with get_tracer().start_as_current_span(span_name) as span:
                if attrs:
                    for k, v in attrs.items():
                        span.set_attribute(k, v)
                try:
                    return await fn(*args, **kwargs)
                except Exception as e:
                    span.record_exception(e)
                    span.set_status({"status": "error"})
                    raise

        import asyncio
        if asyncio.iscoroutinefunction(fn):
            return async_wrapper
        return wrapper

    # Called as @traced without parentheses
    if callable(name):
        fn, name = name, None
        return decorator(fn)

    return decorator


def trace_span(name: str, **attrs):
    """Context manager: create a span for a block of code.

    Usage:
        with trace_span("rag_search", collection="known_issues") as span:
            results = chroma.query(...)
            span.set_attribute("results_count", len(results))
    """
    span = get_tracer().start_span(name)
    for k, v in attrs.items():
        span.set_attribute(k, v)
    return span


def set_run_context(run_id: str, agent_name: str = "", module: str = ""):
    """Set trace context attributes for the current span."""
    span = getattr(_tracer, 'current_span', None)
    if span and hasattr(span, 'set_attribute'):
        try:
            current = _tracer.current_span  # property access via lazy
        except Exception:
            return
    # Context propagated via trace.py TraceContext, not OTEL attributes for now
    pass

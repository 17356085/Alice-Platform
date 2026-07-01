"""Tests for infra/trace.py — structured trace logging.

Tests: TraceContext (set/get/reset), TraceEvent (create, calculate_cost, to_dict),
MODEL_PRICING, write_trace_event, query_trace_events, cleanup_old_traces.
Uses temp directory for JSONL output.
"""
import json
import threading
import pytest
from pathlib import Path
from datetime import datetime, timedelta

from aitest.infra.trace import (
    TraceContext, TraceEvent, MODEL_PRICING,
    write_trace_event, query_trace_events, get_trace_summary,
    cleanup_old_traces, TRACE_DIR, TRACE_LOG,
)


# ══════════════════════════════════════════════════════════════════════════
#  TraceContext
# ══════════════════════════════════════════════════════════════════════════


class TestTraceContext:
    def test_set_and_get(self):
        TraceContext.set(run_id="r1", agent_name="test-agent", skill_version="1.0")
        assert TraceContext.get_run_id() == "r1"
        assert TraceContext.get_agent_name() == "test-agent"
        assert TraceContext.get_skill_version() == "1.0"
        TraceContext.reset()

    def test_reset_clears(self):
        TraceContext.set(run_id="r1", agent_name="a1")
        TraceContext.reset()
        assert TraceContext.get_run_id() == ""
        assert TraceContext.get_agent_name() == ""

    def test_defaults_empty(self):
        TraceContext.reset()
        assert TraceContext.get_run_id() == ""
        assert TraceContext.get_agent_name() == ""
        assert TraceContext.get_skill_version() == ""

    def test_thread_local(self):
        """Each thread has its own context."""
        TraceContext.set(run_id="main-thread")
        results = {}

        def worker():
            results["thread"] = TraceContext.get_run_id()

        t = threading.Thread(target=worker)
        t.start()
        t.join()

        assert results["thread"] == ""  # Different thread, different context
        assert TraceContext.get_run_id() == "main-thread"
        TraceContext.reset()


# ══════════════════════════════════════════════════════════════════════════
#  TraceEvent
# ══════════════════════════════════════════════════════════════════════════


class TestTraceEvent:
    def test_create_fills_fields(self):
        ev = TraceEvent.create(
            event_type="skill_execution",
            run_id="r1", agent_name="test-agent",
            skill_id="automation/tech-analysis",
            provider="claude", model="claude-sonnet-4-6",
            latency_ms=1234, token_input=500, token_output=200,
            status="success",
        )
        assert ev.event_type == "skill_execution"
        assert ev.run_id == "r1"
        assert ev.latency_ms == 1234
        assert ev.token_input == 500
        assert ev.token_cost_estimate > 0

    def test_create_auto_generates_id(self):
        ev = TraceEvent.create(event_type="test")
        assert ev.event_id.startswith("test-")
        assert len(ev.event_id) > 5

    def test_create_auto_generates_timestamp(self):
        ev = TraceEvent.create(event_type="test")
        assert ev.timestamp != ""

    def test_create_truncates_preview(self):
        long_prompt = "x" * 500
        long_response = "y" * 1000
        ev = TraceEvent.create(
            event_type="test",
            prompt_preview=long_prompt,
            response_preview=long_response,
        )
        assert len(ev.prompt_preview) <= 200
        assert len(ev.response_preview) <= 500

    def test_to_dict(self):
        ev = TraceEvent.create(event_type="test", run_id="r1")
        d = ev.to_dict()
        assert d["event_type"] == "test"
        assert d["run_id"] == "r1"
        assert "event_id" in d
        assert "timestamp" in d

    def test_calculate_cost_known_model(self):
        cost = TraceEvent.calculate_cost("claude-sonnet-4-6", 1000, 500)
        assert cost > 0

    def test_calculate_cost_unknown_model(self):
        cost = TraceEvent.calculate_cost("unknown-model", 1000, 500)
        assert cost == 0.0

    def test_calculate_cost_zero_tokens(self):
        cost = TraceEvent.calculate_cost("claude-sonnet-4-6", 0, 0)
        assert cost == 0.0

    def test_calculate_cost_empty_model(self):
        cost = TraceEvent.calculate_cost("", 1000, 500)
        assert cost == 0.0

    def test_calculate_cost_substring_match(self):
        cost = TraceEvent.calculate_cost("claude-sonnet-4-6-20250514", 1000, 500)
        assert cost > 0


# ══════════════════════════════════════════════════════════════════════════
#  MODEL_PRICING
# ══════════════════════════════════════════════════════════════════════════


class TestModelPricing:
    def test_claude_models_priced(self):
        assert "claude-sonnet-4-6" in MODEL_PRICING
        assert "claude-opus-4-8" in MODEL_PRICING

    def test_openai_models_priced(self):
        assert "gpt-4o" in MODEL_PRICING
        assert "gpt-4o-mini" in MODEL_PRICING

    def test_deepseek_models_priced(self):
        assert "deepseek-chat" in MODEL_PRICING
        assert "deepseek-reasoner" in MODEL_PRICING

    def test_local_models_free(self):
        assert MODEL_PRICING["qwen3"] == (0.0, 0.0)
        assert MODEL_PRICING["llama3"] == (0.0, 0.0)

    def test_pricing_format(self):
        for model, (inp, out) in MODEL_PRICING.items():
            assert isinstance(inp, (int, float))
            assert isinstance(out, (int, float))
            assert inp >= 0
            assert out >= 0


# ══════════════════════════════════════════════════════════════════════════
#  write_trace_event + query_trace_events
# ══════════════════════════════════════════════════════════════════════════


class TestWriteAndQuery:
    def test_write_and_query(self, temp_dir, monkeypatch):
        monkeypatch.setattr("aitest.infra.trace.TRACE_DIR", temp_dir)
        monkeypatch.setattr("aitest.infra.trace.TRACE_LOG", temp_dir / "trace.jsonl")

        ev = TraceEvent.create(event_type="test", run_id="r1", agent_name="a1")
        write_trace_event(ev)

        events = query_trace_events(run_id="r1")
        assert len(events) == 1
        assert events[0]["run_id"] == "r1"

    def test_query_filters_by_type(self, temp_dir, monkeypatch):
        monkeypatch.setattr("aitest.infra.trace.TRACE_DIR", temp_dir)
        monkeypatch.setattr("aitest.infra.trace.TRACE_LOG", temp_dir / "trace.jsonl")

        write_trace_event(TraceEvent.create(event_type="llm_call", run_id="r1"))
        write_trace_event(TraceEvent.create(event_type="skill_execution", run_id="r1"))

        events = query_trace_events(event_type="llm_call")
        assert len(events) == 1
        assert events[0]["event_type"] == "llm_call"

    def test_query_empty(self, temp_dir, monkeypatch):
        monkeypatch.setattr("aitest.infra.trace.TRACE_DIR", temp_dir)
        monkeypatch.setattr("aitest.infra.trace.TRACE_LOG", temp_dir / "trace.jsonl")

        assert query_trace_events(run_id="nonexistent") == []

    def test_query_limit(self, temp_dir, monkeypatch):
        monkeypatch.setattr("aitest.infra.trace.TRACE_DIR", temp_dir)
        monkeypatch.setattr("aitest.infra.trace.TRACE_LOG", temp_dir / "trace.jsonl")

        for i in range(10):
            write_trace_event(TraceEvent.create(event_type="test", run_id=f"r{i}"))

        events = query_trace_events(limit=5)
        assert len(events) == 5


# ══════════════════════════════════════════════════════════════════════════
#  get_trace_summary
# ══════════════════════════════════════════════════════════════════════════


class TestGetTraceSummary:
    def test_empty_summary(self, temp_dir, monkeypatch):
        monkeypatch.setattr("aitest.infra.trace.TRACE_DIR", temp_dir)
        monkeypatch.setattr("aitest.infra.trace.TRACE_LOG", temp_dir / "trace.jsonl")

        summary = get_trace_summary()
        assert summary["total_events"] == 0
        assert summary["by_type"] == {}

    def test_summary_with_events(self, temp_dir, monkeypatch):
        monkeypatch.setattr("aitest.infra.trace.TRACE_DIR", temp_dir)
        monkeypatch.setattr("aitest.infra.trace.TRACE_LOG", temp_dir / "trace.jsonl")

        write_trace_event(TraceEvent.create(event_type="llm_call", run_id="r1",
                                            token_input=100, token_output=50))
        write_trace_event(TraceEvent.create(event_type="skill_execution", run_id="r1"))

        summary = get_trace_summary(run_id="r1")
        assert summary["total_events"] == 2
        assert "llm_call" in summary["by_type"]
        assert summary["total_tokens_input"] == 100


# ══════════════════════════════════════════════════════════════════════════
#  cleanup_old_traces
# ══════════════════════════════════════════════════════════════════════════


class TestCleanupOldTraces:
    def test_cleanup_empty(self, temp_dir, monkeypatch):
        monkeypatch.setattr("aitest.infra.trace.TRACE_DIR", temp_dir)
        monkeypatch.setattr("aitest.infra.trace.TRACE_LOG", temp_dir / "trace.jsonl")
        assert cleanup_old_traces() == 0

    def test_cleanup_keeps_recent(self, temp_dir, monkeypatch):
        monkeypatch.setattr("aitest.infra.trace.TRACE_DIR", temp_dir)
        monkeypatch.setattr("aitest.infra.trace.TRACE_LOG", temp_dir / "trace.jsonl")

        write_trace_event(TraceEvent.create(event_type="test"))
        assert cleanup_old_traces(days=7) == 0  # Recent, not cleaned

    def test_cleanup_removes_old(self, temp_dir, monkeypatch):
        monkeypatch.setattr("aitest.infra.trace.TRACE_DIR", temp_dir)
        monkeypatch.setattr("aitest.infra.trace.TRACE_LOG", temp_dir / "trace.jsonl")

        # Write an event with old timestamp
        ev = TraceEvent.create(event_type="test")
        ev.timestamp = (datetime.now() - timedelta(days=30)).isoformat()
        write_trace_event(ev)

        deleted = cleanup_old_traces(days=7)
        assert deleted == 1


# ══════════════════════════════════════════════════════════════════════════
#  Thread safety
# ══════════════════════════════════════════════════════════════════════════


class TestThreadSafety:
    def test_concurrent_writes(self, temp_dir, monkeypatch):
        monkeypatch.setattr("aitest.infra.trace.TRACE_DIR", temp_dir)
        monkeypatch.setattr("aitest.infra.trace.TRACE_LOG", temp_dir / "trace.jsonl")

        errors = []

        def write_events(n):
            try:
                for i in range(n):
                    ev = TraceEvent.create(event_type="test", run_id=f"r{i}")
                    write_trace_event(ev)
            except Exception as e:
                errors.append(e)

        threads = [threading.Thread(target=write_events, args=(10,)) for _ in range(5)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        assert len(errors) == 0
        events = query_trace_events(limit=100)
        assert len(events) == 50

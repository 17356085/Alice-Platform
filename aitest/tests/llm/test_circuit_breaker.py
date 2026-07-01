"""Tests for llm/circuit_breaker.py — LLM provider circuit breaker.

Tests: CircuitState, CircuitBreaker (CLOSED→OPEN→HALF_OPEN→CLOSED),
call(), acall(), metrics, reset, get_circuit_breaker, get_all_metrics.
Thread-safe — tests concurrent access.
"""
import time
import threading
import pytest

from aitest.llm.circuit_breaker import (
    CircuitBreaker, CircuitState, CircuitOpenError,
    get_circuit_breaker, get_all_metrics,
)


# ══════════════════════════════════════════════════════════════════════════
#  CircuitState
# ══════════════════════════════════════════════════════════════════════════


class TestCircuitState:
    def test_three_states(self):
        assert CircuitState.CLOSED.value == "closed"
        assert CircuitState.OPEN.value == "open"
        assert CircuitState.HALF_OPEN.value == "half_open"


# ══════════════════════════════════════════════════════════════════════════
#  CircuitOpenError
# ══════════════════════════════════════════════════════════════════════════


class TestCircuitOpenError:
    def test_has_name(self):
        err = CircuitOpenError("test-breaker", time.monotonic(), 60.0)
        assert err.name == "test-breaker"

    def test_has_remaining(self):
        err = CircuitOpenError("test", time.monotonic(), 60.0)
        assert err.remaining_seconds > 0

    def test_message_contains_retry(self):
        err = CircuitOpenError("test", time.monotonic(), 60.0)
        assert "Retry" in str(err) or "retry" in str(err)


# ══════════════════════════════════════════════════════════════════════════
#  CircuitBreaker — state transitions
# ══════════════════════════════════════════════════════════════════════════


class TestCircuitBreakerStates:
    def test_initial_state_closed(self):
        cb = CircuitBreaker("test")
        assert cb.state == CircuitState.CLOSED

    def test_stays_closed_below_threshold(self):
        cb = CircuitBreaker("test", failure_threshold=3)
        for _ in range(2):
            try:
                cb.call(lambda: (_ for _ in ()).throw(RuntimeError("fail")))
            except RuntimeError:
                pass
        assert cb.state == CircuitState.CLOSED

    def test_opens_at_threshold(self):
        cb = CircuitBreaker("test", failure_threshold=3)
        for _ in range(3):
            try:
                cb.call(lambda: (_ for _ in ()).throw(RuntimeError("fail")))
            except RuntimeError:
                pass
        assert cb.state == CircuitState.OPEN

    def test_open_fast_fails(self):
        cb = CircuitBreaker("test", failure_threshold=1)
        try:
            cb.call(lambda: (_ for _ in ()).throw(RuntimeError("fail")))
        except RuntimeError:
            pass
        assert cb.state == CircuitState.OPEN
        with pytest.raises(CircuitOpenError):
            cb.call(lambda: "should not run")

    def test_half_open_after_cooldown(self):
        cb = CircuitBreaker("test", failure_threshold=1, cooldown_seconds=0.1)
        try:
            cb.call(lambda: (_ for _ in ()).throw(RuntimeError("fail")))
        except RuntimeError:
            pass
        assert cb.state == CircuitState.OPEN
        time.sleep(0.15)
        assert cb.state == CircuitState.HALF_OPEN

    def test_half_open_closes_on_success(self):
        cb = CircuitBreaker("test", failure_threshold=1, cooldown_seconds=0.1)
        try:
            cb.call(lambda: (_ for _ in ()).throw(RuntimeError("fail")))
        except RuntimeError:
            pass
        time.sleep(0.15)
        result = cb.call(lambda: "recovered")
        assert result == "recovered"
        assert cb.state == CircuitState.CLOSED

    def test_half_open_reopens_on_failure(self):
        cb = CircuitBreaker("test", failure_threshold=1, cooldown_seconds=0.1)
        try:
            cb.call(lambda: (_ for _ in ()).throw(RuntimeError("fail")))
        except RuntimeError:
            pass
        time.sleep(0.15)
        assert cb.state == CircuitState.HALF_OPEN
        try:
            cb.call(lambda: (_ for _ in ()).throw(RuntimeError("fail again")))
        except RuntimeError:
            pass
        assert cb.state == CircuitState.OPEN


# ══════════════════════════════════════════════════════════════════════════
#  CircuitBreaker — call()
# ══════════════════════════════════════════════════════════════════════════


class TestCall:
    def test_returns_result(self):
        cb = CircuitBreaker("test")
        result = cb.call(lambda: 42)
        assert result == 42

    def test_passes_args(self):
        cb = CircuitBreaker("test")
        result = cb.call(lambda x, y: x + y, 3, 4)
        assert result == 7

    def test_passes_kwargs(self):
        cb = CircuitBreaker("test")
        result = cb.call(lambda x=0: x * 2, x=5)
        assert result == 10

    def test_re_raises_original_exception(self):
        cb = CircuitBreaker("test")
        with pytest.raises(ValueError, match="bad input"):
            cb.call(lambda: (_ for _ in ()).throw(ValueError("bad input")))


# ══════════════════════════════════════════════════════════════════════════
#  CircuitBreaker — metrics
# ══════════════════════════════════════════════════════════════════════════


class TestMetrics:
    def test_metrics_structure(self):
        cb = CircuitBreaker("test")
        m = cb.metrics
        assert "name" in m
        assert "state" in m
        assert "failure_count" in m
        assert "success_count" in m

    def test_metrics_track_success(self):
        cb = CircuitBreaker("test")
        cb.call(lambda: "ok")
        assert cb.metrics["success_count"] == 1

    def test_metrics_track_failure(self):
        cb = CircuitBreaker("test", failure_threshold=10)
        try:
            cb.call(lambda: (_ for _ in ()).throw(RuntimeError("fail")))
        except RuntimeError:
            pass
        assert cb.metrics["failure_count"] == 1


# ══════════════════════════════════════════════════════════════════════════
#  CircuitBreaker — reset
# ══════════════════════════════════════════════════════════════════════════


class TestReset:
    def test_reset_closes_circuit(self):
        cb = CircuitBreaker("test", failure_threshold=1)
        try:
            cb.call(lambda: (_ for _ in ()).throw(RuntimeError("fail")))
        except RuntimeError:
            pass
        assert cb.state == CircuitState.OPEN
        cb.reset()
        assert cb.state == CircuitState.CLOSED

    def test_reset_clears_failure_count(self):
        cb = CircuitBreaker("test", failure_threshold=1)
        try:
            cb.call(lambda: (_ for _ in ()).throw(RuntimeError("fail")))
        except RuntimeError:
            pass
        cb.reset()
        assert cb.metrics["failure_count"] == 0


# ══════════════════════════════════════════════════════════════════════════
#  Global registry
# ══════════════════════════════════════════════════════════════════════════


class TestGlobalRegistry:
    def test_get_circuit_breaker_returns_singleton(self):
        cb1 = get_circuit_breaker("test-singleton")
        cb2 = get_circuit_breaker("test-singleton")
        assert cb1 is cb2

    def test_get_circuit_breaker_different_names(self):
        cb1 = get_circuit_breaker("breaker-a")
        cb2 = get_circuit_breaker("breaker-b")
        assert cb1 is not cb2

    def test_get_all_metrics(self):
        metrics = get_all_metrics()
        assert isinstance(metrics, list)
        # Should contain metrics from all registered breakers
        names = [m["name"] for m in metrics]
        assert len(names) > 0


# ══════════════════════════════════════════════════════════════════════════
#  Thread safety
# ══════════════════════════════════════════════════════════════════════════


class TestThreadSafety:
    def test_concurrent_calls(self):
        cb = CircuitBreaker("thread-test", failure_threshold=100)
        results = []
        errors = []

        def call_cb():
            try:
                for _ in range(10):
                    r = cb.call(lambda: "ok")
                    results.append(r)
            except Exception as e:
                errors.append(e)

        threads = [threading.Thread(target=call_cb) for _ in range(5)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        assert len(errors) == 0
        assert len(results) == 50

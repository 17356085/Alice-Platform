"""Unit tests for circuit_breaker.py — state machine transitions."""
import time
import pytest
from aitest.llm.circuit_breaker import (
    CircuitBreaker, CircuitOpenError, CircuitState,
    get_circuit_breaker, get_all_metrics,
)


class TestCircuitBreakerStateMachine:
    """Test the CLOSED → OPEN → HALF_OPEN → CLOSED lifecycle."""

    def test_initial_state_closed(self):
        cb = CircuitBreaker("test", failure_threshold=3, cooldown_seconds=0.1)
        assert cb.state == CircuitState.CLOSED

    def test_success_keeps_closed(self):
        cb = CircuitBreaker("test", failure_threshold=3)
        for _ in range(5):
            cb.call(lambda: "ok")
        assert cb.state == CircuitState.CLOSED

    def test_failures_open_circuit(self):
        cb = CircuitBreaker("test", failure_threshold=2, cooldown_seconds=60)

        def fail(): raise RuntimeError("boom")

        for _ in range(2):
            with pytest.raises(RuntimeError):
                cb.call(fail)

        assert cb.state == CircuitState.OPEN

    def test_open_circuit_fast_fails(self):
        cb = CircuitBreaker("test", failure_threshold=1, cooldown_seconds=60)
        try: cb.call(lambda: 1/0)
        except: pass

        with pytest.raises(CircuitOpenError):
            cb.call(lambda: "should not be called")

    def test_half_open_after_cooldown(self):
        cb = CircuitBreaker("test", failure_threshold=1, cooldown_seconds=0.01)
        try: cb.call(lambda: 1/0)
        except: pass

        assert cb.state == CircuitState.OPEN
        time.sleep(0.02)  # wait past cooldown

        # Next state check should be HALF_OPEN
        # (state property re-evaluates on access)
        assert cb.state == CircuitState.HALF_OPEN

    def test_half_open_success_closes(self):
        cb = CircuitBreaker("test", failure_threshold=1, cooldown_seconds=0.01)
        try: cb.call(lambda: 1/0)
        except: pass

        time.sleep(0.02)
        assert cb.state == CircuitState.HALF_OPEN

        cb.call(lambda: "ok")
        assert cb.state == CircuitState.CLOSED

    def test_half_open_failure_reopens(self):
        cb = CircuitBreaker("test", failure_threshold=1, cooldown_seconds=0.01)
        try: cb.call(lambda: 1/0)
        except: pass

        time.sleep(0.02)
        assert cb.state == CircuitState.HALF_OPEN

        with pytest.raises(ZeroDivisionError):
            cb.call(lambda: 1/0)

        assert cb.state == CircuitState.OPEN

    def test_reset_clears_state(self):
        cb = CircuitBreaker("test", failure_threshold=1, cooldown_seconds=60)
        try: cb.call(lambda: 1/0)
        except: pass

        assert cb.state == CircuitState.OPEN
        cb.reset()
        assert cb.state == CircuitState.CLOSED

    def test_metrics_reflect_state(self):
        cb = CircuitBreaker("test", failure_threshold=2, cooldown_seconds=60)
        cb.call(lambda: "ok")
        cb.call(lambda: "ok")

        m = cb.metrics
        assert m["name"] == "test"
        assert m["state"] == "closed"
        assert m["success_count"] == 2
        assert m["failure_count"] == 0

    def test_global_registry_singleton(self):
        cb1 = get_circuit_breaker("registry_test")
        cb2 = get_circuit_breaker("registry_test")
        assert cb1 is cb2

    def test_get_all_metrics(self):
        get_circuit_breaker("metrics_test_1", failure_threshold=2)
        get_circuit_breaker("metrics_test_2", failure_threshold=3)
        metrics = get_all_metrics()
        names = {m["name"] for m in metrics}
        assert "metrics_test_1" in names
        assert "metrics_test_2" in names

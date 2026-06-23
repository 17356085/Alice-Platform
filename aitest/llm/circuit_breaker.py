"""
Circuit Breaker — protect LLM calls from cascading failures.

States:
  CLOSED    → normal operation, count failures
  OPEN      → fast-fail, no calls attempted (cooldown period)
  HALF_OPEN → allow one probe call to test recovery

Usage:
    from aitest.llm.circuit_breaker import CircuitBreaker, CircuitOpenError

    cb = CircuitBreaker("claude", failure_threshold=5, cooldown_seconds=60)

    try:
        result = cb.call(lambda: provider.complete(system, user))
    except CircuitOpenError:
        # Circuit is open — use fallback or return cached
        result = fallback_provider.complete(system, user)
"""

import time
import threading
from enum import Enum
from dataclasses import dataclass, field
from typing import Callable, Optional


class CircuitState(Enum):
    CLOSED = "closed"
    OPEN = "open"
    HALF_OPEN = "half_open"


class CircuitOpenError(Exception):
    """Raised when a call is attempted while circuit is OPEN."""
    def __init__(self, name: str, opened_at: float, cooldown: float):
        remaining = max(0, cooldown - (time.monotonic() - opened_at))
        super().__init__(
            f"Circuit '{name}' is OPEN. "
            f"Retry in {remaining:.0f}s."
        )
        self.name = name
        self.remaining_seconds = remaining


@dataclass
class CircuitBreaker:
    """Thread-safe circuit breaker for LLM provider calls."""

    name: str
    failure_threshold: int = 5          # consecutive failures to open
    cooldown_seconds: float = 60.0      # time before half-open probe
    half_open_max_requests: int = 1     # max probe requests in half-open

    _state: CircuitState = CircuitState.CLOSED
    _failure_count: int = 0
    _last_failure_time: float = 0.0
    _opened_at: float = 0.0
    _half_open_requests: int = 0
    _success_count: int = 0
    _lock: threading.Lock = field(default_factory=threading.Lock)

    # ── Public API ──────────────────────────────────────────────────

    def call(self, fn: Callable, *args, **kwargs):
        """Execute fn() with circuit breaker protection.

        Returns fn() result on success.
        Raises CircuitOpenError if circuit is OPEN.
        Re-raises original exception on failure (and counts it).
        """
        self._pre_call()
        try:
            result = fn(*args, **kwargs)
            self._on_success()
            return result
        except Exception as e:
            self._on_failure()
            raise

    async def acall(self, async_fn: Callable, *args, **kwargs):
        """Async version of call()."""
        self._pre_call()
        try:
            result = await async_fn(*args, **kwargs)
            self._on_success()
            return result
        except Exception as e:
            self._on_failure()
            raise

    @property
    def state(self) -> CircuitState:
        with self._lock:
            return self._current_state()

    @property
    def metrics(self) -> dict:
        with self._lock:
            return {
                "name": self.name,
                "state": self._current_state().value,
                "failure_count": self._failure_count,
                "success_count": self._success_count,
                "opened_at": self._opened_at if self._current_state() == CircuitState.OPEN else None,
                "cooldown_remaining": max(0, self.cooldown_seconds - (time.monotonic() - self._opened_at))
                if self._current_state() == CircuitState.OPEN else 0,
            }

    def reset(self):
        """Force-reset to CLOSED (e.g., after manual intervention)."""
        with self._lock:
            self._state = CircuitState.CLOSED
            self._failure_count = 0
            self._half_open_requests = 0

    # ── Internal ────────────────────────────────────────────────────

    def _current_state(self) -> CircuitState:
        """Determine effective state (handles cooldown expiry). Caller must hold lock."""
        if self._state == CircuitState.OPEN:
            elapsed = time.monotonic() - self._opened_at
            if elapsed >= self.cooldown_seconds:
                self._state = CircuitState.HALF_OPEN
                self._half_open_requests = 0
        return self._state

    def _pre_call(self):
        """Check if call is allowed. Raises CircuitOpenError if not."""
        with self._lock:
            state = self._current_state()
            if state == CircuitState.OPEN:
                raise CircuitOpenError(self.name, self._opened_at, self.cooldown_seconds)
            if state == CircuitState.HALF_OPEN:
                if self._half_open_requests >= self.half_open_max_requests:
                    raise CircuitOpenError(self.name, self._opened_at, self.cooldown_seconds)
                self._half_open_requests += 1

    def _on_success(self):
        with self._lock:
            self._failure_count = 0
            self._success_count += 1
            if self._state == CircuitState.HALF_OPEN:
                self._state = CircuitState.CLOSED
                self._half_open_requests = 0

    def _on_failure(self):
        with self._lock:
            self._failure_count += 1
            self._last_failure_time = time.monotonic()
            if (self._state == CircuitState.CLOSED and
                    self._failure_count >= self.failure_threshold):
                self._state = CircuitState.OPEN
                self._opened_at = time.monotonic()
            elif self._state == CircuitState.HALF_OPEN:
                self._state = CircuitState.OPEN
                self._opened_at = time.monotonic()


# ── Global registry ──────────────────────────────────────────────────

_breakers: dict[str, CircuitBreaker] = {}
_breakers_lock = threading.Lock()


def get_circuit_breaker(name: str, **kwargs) -> CircuitBreaker:
    """Get or create a named circuit breaker (singleton per name)."""
    with _breakers_lock:
        if name not in _breakers:
            _breakers[name] = CircuitBreaker(name=name, **kwargs)
        return _breakers[name]


def get_all_metrics() -> list[dict]:
    """Get metrics for all registered circuit breakers."""
    with _breakers_lock:
        return [cb.metrics for cb in _breakers.values()]

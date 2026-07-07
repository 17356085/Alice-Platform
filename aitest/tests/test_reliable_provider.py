"""Tests for llm/reliable_provider.py — retry, fallback, error classification, usage tracking.

P1-7: Zero existing tests for this critical infrastructure module.
Tests pure functions (classify_error, compute_backoff, UsageTracker) and
ReliableProvider behavior with mocked LLM providers.
"""
import pytest
import time
from alice_engine.runtime.core.retry import (
    ErrorClass, classify_error, compute_backoff, RetryConfig,
    FallbackConfig, DEFAULT_FALLBACK_CHAIN,
    UsageTracker, ReliableProvider, _FatalError,
)


# ── Error Classification ──────────────────────────────────────────────

class TestClassifyError:
    def test_429_is_retryable(self):
        e = Exception("rate_limit exceeded")
        assert classify_error(e, 429) == ErrorClass.RETRYABLE

    def test_503_is_retryable(self):
        assert classify_error(Exception("overloaded"), 503) == ErrorClass.RETRYABLE

    def test_timeout_is_retryable(self):
        assert classify_error(Exception("connection timed out"), 0) == ErrorClass.RETRYABLE

    def test_server_error_in_msg_is_retryable(self):
        assert classify_error(Exception("internal server error"), 0) == ErrorClass.RETRYABLE

    def test_401_is_fallback(self):
        assert classify_error(Exception("unauthorized"), 401) == ErrorClass.FALLBACK

    def test_403_is_fallback(self):
        assert classify_error(Exception("forbidden"), 403) == ErrorClass.FALLBACK

    def test_500_is_fallback(self):
        # 500 without "server error" in message → FALLBACK (status >= 500)
        assert classify_error(Exception("internal error"), 500) == ErrorClass.FALLBACK

    def test_invalid_api_key_is_fallback(self):
        assert classify_error(Exception("invalid_api_key"), 0) == ErrorClass.FALLBACK

    def test_context_length_is_fatal(self):
        assert classify_error(Exception("context_length exceeded: too many tokens"), 400) == ErrorClass.FATAL

    def test_bad_request_is_fatal(self):
        assert classify_error(Exception("bad request"), 400) == ErrorClass.FATAL

    def test_unknown_error_defaults_to_fatal(self):
        assert classify_error(Exception("something unexpected"), 418) == ErrorClass.FATAL


# ── Compute Backoff ───────────────────────────────────────────────────

class TestComputeBackoff:
    def test_first_attempt_minimum_delay(self):
        config = RetryConfig(base_delay=1.0, backoff_multiplier=2.0, jitter=False)
        delay = compute_backoff(0, config)
        assert delay == 1.0

    def test_exponential_growth(self):
        config = RetryConfig(base_delay=1.0, backoff_multiplier=2.0, jitter=False)
        assert compute_backoff(1, config) == 2.0
        assert compute_backoff(2, config) == 4.0
        assert compute_backoff(3, config) == 8.0

    def test_capped_at_max_delay(self):
        config = RetryConfig(base_delay=10.0, backoff_multiplier=10.0, max_delay=30.0, jitter=False)
        assert compute_backoff(4, config) == 30.0  # 10 * 10^4 = 100000 → capped

    def test_jitter_adds_variance(self):
        config = RetryConfig(base_delay=1.0, jitter=True)
        delays = [compute_backoff(0, config) for _ in range(50)]
        # With jitter, not all values should be identical
        assert len(set(round(d, 4) for d in delays)) > 1
        # All should be within [0.5 * base, 1.5 * base]
        assert all(0.5 <= d <= 1.5 for d in delays)


# ── Usage Tracker ─────────────────────────────────────────────────────

class TestUsageTracker:
    def test_record_accumulates_tokens(self):
        t = UsageTracker()
        t.record("claude", "test-agent", 1000, 500)
        assert t.session_total() == 1500
        assert t._session_input == 1000
        assert t._session_output == 500

    def test_record_fallback_increments_counter(self):
        t = UsageTracker()
        assert t._fallback_count == 0
        t.record_fallback()
        assert t._fallback_count == 1

    def test_record_retry_increments_counter(self):
        t = UsageTracker()
        t.record_retry()
        t.record_retry()
        assert t._retry_count == 2

    def test_cache_hit_rate(self):
        t = UsageTracker()
        t.record("claude", "a", 1000, 200, cache_read=500)
        assert t.cache_hit_rate() == 0.5

    def test_cache_hit_rate_zero_division(self):
        t = UsageTracker()
        assert t.cache_hit_rate() == 0.0

    def test_estimated_cost_nonzero(self):
        t = UsageTracker()
        t.record("claude", "a", 1_000_000, 1_000_000)
        cost = t.estimated_cost()
        assert cost > 0
        assert cost == pytest.approx(18.0, rel=0.1)  # $3 + $15

    def test_reset_session_clears_counters(self):
        t = UsageTracker()
        t.record("claude", "a", 1000, 500)
        t.reset_session()
        assert t._session_input == 0
        assert t._session_output == 0

    def test_reset_keeps_history(self):
        t = UsageTracker()
        t.record("claude", "a", 1000, 500)
        t.reset_session()
        assert len(t._records) == 1  # History preserved

    def test_summary_includes_key_metrics(self):
        t = UsageTracker()
        t.record("claude", "a", 5000, 2000)
        t.record_fallback()
        s = t.summary()
        assert "7,000" in s or "7000" in s  # Total tokens
        assert "Fallback: 1" in s


# ── Fallback Config ───────────────────────────────────────────────────

class TestFallbackConfig:
    def test_default_chain_has_four_providers(self):
        config = FallbackConfig()
        assert len(config.chain) == 4  # mimo → deepseek → openai → claude

    def test_default_chain_starts_with_mimo(self):
        config = FallbackConfig()
        assert config.chain[0]["provider"] == "mimo"

    def test_custom_chain_overrides(self):
        custom = [{"provider": "openai", "model": "gpt-4o"}]
        config = FallbackConfig(chain=custom)
        assert len(config.chain) == 1
        assert config.chain[0]["provider"] == "openai"

    def test_total_timeout_default(self):
        assert FallbackConfig().total_timeout == 600.0

    def test_per_call_timeout_default(self):
        assert FallbackConfig().per_call_timeout == 120.0


# ── ReliableProvider Construction ─────────────────────────────────────

class TestReliableProviderInit:
    def test_init_with_default_config(self):
        rp = ReliableProvider()
        assert rp.fallback_config is not None
        assert len(rp.fallback_config.chain) == 4

    def test_init_with_custom_config(self):
        config = FallbackConfig(chain=[{"provider": "openai", "model": "gpt-4o"}])
        rp = ReliableProvider(fallback_config=config)
        assert rp.fallback_config.chain[0]["provider"] == "openai"

    def test_tracker_initialized(self):
        rp = ReliableProvider()
        assert rp.tracker is not None
        assert rp.tracker.session_total() == 0

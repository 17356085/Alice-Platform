"""Tests for llm/context_window.py — context window monitoring + continuation.

Tests: token estimation, ContextWindowMonitor, SessionCompactor,
build_continuation_prompt, ContinuationResult.
No real LLM calls — compaction LLM is mocked.
"""
import pytest
from unittest.mock import MagicMock, patch

from alice_engine.runtime.core.context_window import (
    ContextWindowMonitor, SessionCompactor, WindowStatus, WindowState,
    build_continuation_prompt, ContinuationResult,
    ContextWindowExceededError,
    MODEL_CONTEXT_LIMITS, DEFAULT_CONTEXT_LIMIT,
)


# ══════════════════════════════════════════════════════════════════════════
#  Token estimation
# ══════════════════════════════════════════════════════════════════════════


class TestEstimateTokens:
    def test_empty_string_zero(self):
        assert ContextWindowMonitor.estimate_tokens("") == 0
        assert ContextWindowMonitor.estimate_tokens(None) == 0

    def test_english_text(self):
        n = ContextWindowMonitor.estimate_tokens("hello world")
        # "hello world" = 11 chars, 11/4 = 2.75 → 2 (int)
        assert n == 2

    def test_chinese_text(self):
        n = ContextWindowMonitor.estimate_tokens("你好世界")
        # 4 Chinese chars * 1.5 = 6
        assert n == 6

    def test_mixed_text(self):
        n = ContextWindowMonitor.estimate_tokens("hello 你好 world 世界")
        # Chinese: 你好(2 chars) + 世界(2 chars) = 4 → 4 * 1.5 = 6
        # Other: "hello " (6) + " world " (7) + "" (0) = 13 → 13/4 = 3
        # Total: 6 + 3 = 9
        assert n == 9

    def test_large_english_approximate(self):
        text = "hello world " * 100  # 1200 chars
        n = ContextWindowMonitor.estimate_tokens(text)
        assert 250 < n < 350  # ~300 tokens expected


# ══════════════════════════════════════════════════════════════════════════
#  Model context limits
# ══════════════════════════════════════════════════════════════════════════


class TestModelLimits:
    def test_known_model_returns_limit(self):
        from alice_engine.runtime.core.context_window import MODEL_CONTEXT_LIMITS
        assert MODEL_CONTEXT_LIMITS["claude-sonnet-4-6"] == 200_000
        assert MODEL_CONTEXT_LIMITS["deepseek-chat"] == 64_000
        assert MODEL_CONTEXT_LIMITS["gpt-4o"] == 128_000

    def test_unknown_model_defaults(self):
        m = ContextWindowMonitor(model="unknown-model-xyz")
        assert m.limit == DEFAULT_CONTEXT_LIMIT

    def test_explicit_limit_override(self):
        m = ContextWindowMonitor(model="claude-sonnet-4-6", model_limit=50_000)
        assert m.limit == 50_000  # Override wins


# ══════════════════════════════════════════════════════════════════════════
#  ContextWindowMonitor — state transitions
# ══════════════════════════════════════════════════════════════════════════


class TestContextWindowMonitor:
    def test_init_state(self):
        m = ContextWindowMonitor(model_limit=100_000)
        assert m.current_tokens == 0
        assert m.usage_ratio == 0.0
        assert m.check() == WindowStatus.OK
        assert m.remaining_tokens() == 100_000

    def test_check_ok(self):
        m = ContextWindowMonitor(model_limit=100_000)
        m.add_usage(50_000, 10_000)
        assert m.check() == WindowStatus.OK
        assert 0.59 < m.usage_ratio < 0.61

    def test_check_warn_at_85_percent(self):
        m = ContextWindowMonitor(model_limit=100_000)
        m.add_usage(85_000, 0)
        assert m.check() == WindowStatus.WARN
        assert m.should_continue() is False  # WARN is not HARD

    def test_check_hard_at_90_percent(self):
        m = ContextWindowMonitor(model_limit=100_000)
        m.add_usage(90_000, 0)
        assert m.check() == WindowStatus.HARD
        assert m.should_continue() is True

    def test_add_message_estimates_tokens(self):
        m = ContextWindowMonitor(model_limit=100_000)
        m.add_message("user", "hello world " * 50)  # ~600 chars, ~150 tokens
        assert m.current_tokens > 0

    def test_add_usage_accumulates(self):
        m = ContextWindowMonitor(model_limit=100_000)
        m.add_usage(10_000, 2_000)
        m.add_usage(5_000, 1_000)
        assert m.current_tokens == 18_000

    def test_remaining_tokens_at_limit(self):
        m = ContextWindowMonitor(model_limit=100_000)
        m.add_usage(100_000, 0)
        assert m.remaining_tokens() == 0

    def test_remaining_tokens_over_limit_returns_zero(self):
        m = ContextWindowMonitor(model_limit=100_000)
        m.add_usage(150_000, 0)
        assert m.remaining_tokens() == 0

    def test_status_summary(self):
        m = ContextWindowMonitor(model_limit=100_000)
        m.add_usage(50_000, 10_000)
        summary = m.status_summary()
        assert "60,000" in summary
        assert "100,000" in summary

    def test_should_continue_false_below_threshold(self):
        m = ContextWindowMonitor(model_limit=100_000)
        m.add_usage(80_000, 0)  # 80% — below 85%
        assert m.should_continue() is False


# ══════════════════════════════════════════════════════════════════════════
#  ContinuationResult
# ══════════════════════════════════════════════════════════════════════════


class TestContinuationResult:
    def test_defaults(self):
        cr = ContinuationResult()
        assert cr.continuation_count == 0
        assert cr.was_continued is False
        assert "one pass" in cr.summary()

    def test_with_continuations(self):
        cr = ContinuationResult(
            continuation_count=2,
            cumulative_input_tokens=500_000,
            cumulative_output_tokens=100_000,
        )
        cr.total_tokens = 600_000
        assert cr.was_continued is True
        assert "2 continuation" in cr.summary()
        assert "600,000" in cr.summary()


# ══════════════════════════════════════════════════════════════════════════
#  SessionCompactor
# ══════════════════════════════════════════════════════════════════════════


class TestSessionCompactor:
    def test_serialize_formats_messages(self):
        compactor = SessionCompactor()
        messages = [
            {"role": "user", "content": "Write a test for login"},
            {"role": "assistant", "content": "Here is the test: ..."},
        ]
        result = compactor._serialize(messages)
        assert "[USER]" in result
        assert "[ASSISTANT]" in result
        assert "Write a test for login" in result

    def test_serialize_truncates_per_message(self):
        compactor = SessionCompactor()
        long_msg = "x" * 600  # > 500 char limit
        messages = [{"role": "user", "content": long_msg}]
        result = compactor._serialize(messages)
        assert len("x" * 500) in [len(part) for part in result.split("\n")] or len(result) <= 550

    def test_serialize_last_50_only(self):
        compactor = SessionCompactor()
        messages = [{"role": "user", "content": f"msg_{i}"} for i in range(100)]
        result = compactor._serialize(messages)
        # Should contain msg_50 to msg_99, not msg_0
        assert "msg_99" in result
        # 50 messages × separator pattern
        assert result.count("[USER]") == 50

    def test_format_memory(self):
        compactor = SessionCompactor()
        memory = {
            "completed_skills": ["skill_a", "skill_b"],
            "failed_skills": ["skill_c"],
            "prev_output": "Some output preview...",
        }
        result = compactor._format_memory(memory)
        assert "skill_a" in result
        assert "skill_c" in result
        assert "Some output preview" in result

    def test_format_memory_empty(self):
        compactor = SessionCompactor()
        assert compactor._format_memory({}) == ""

    def test_raw_truncation(self):
        compactor = SessionCompactor()
        messages = [{"role": "user", "content": f"msg_{i}"} for i in range(20)]
        result = compactor._raw_truncation(messages)
        # Should use last 5 messages only
        assert "msg_15" in result
        assert result.count("[USER]") <= 5

    def test_compact_fallback_on_llm_error(self, fake_llm):
        """When LLM summarization fails, falls back to raw truncation."""
        compactor = SessionCompactor(summarizer_provider="deepseek")
        messages = [{"role": "user", "content": "Write a test"}] * 10

        fake_llm.set_error(RuntimeError("API down"))

        with patch("aitest.llm.provider.get_provider", return_value=fake_llm):
            result = compactor.compact(messages)
            # Should return raw truncation
            assert len(result) > 0
            assert "[USER]" in result

    def test_compact_abort_check(self):
        """Abort callback triggers immediate raw truncation."""
        compactor = SessionCompactor()
        messages = [{"role": "user", "content": "test"}] * 10

        result = compactor.compact(messages, abort_check=lambda: True)
        assert "[USER]" in result  # raw truncation used

    def test_compact_with_memory_context(self, fake_llm):
        """Memory context is injected before conversation."""
        compactor = SessionCompactor(summarizer_provider="deepseek")

        fake_llm.set_response("Summary: completed 3 skills, 2 remaining.")

        messages = [{"role": "user", "content": "do task"}]
        memory = {"completed_skills": ["a", "b", "c"]}

        with patch("alice_engine.providers.get_provider", return_value=fake_llm):
            result = compactor.compact(messages, agent_memory=memory)
            assert result == "Summary: completed 3 skills, 2 remaining."


# ══════════════════════════════════════════════════════════════════════════
#  build_continuation_prompt
# ══════════════════════════════════════════════════════════════════════════


class TestBuildContinuationPrompt:
    def test_includes_summary(self):
        prompt = build_continuation_prompt("Did task A, B. Remaining: C.", 1)
        assert "Session Continuation (1)" in prompt
        assert "Did task A, B" in prompt
        assert "Remaining: C" in prompt

    def test_includes_continuation_number(self):
        for n in [1, 3, 5]:
            prompt = build_continuation_prompt("summary", n)
            assert f"({n})" in prompt


# ══════════════════════════════════════════════════════════════════════════
#  ContextWindowExceededError
# ══════════════════════════════════════════════════════════════════════════


class TestContextWindowExceededError:
    def test_carries_token_info(self):
        e = ContextWindowExceededError("Window full", current_tokens=180_000, limit=200_000)
        assert e.current_tokens == 180_000
        assert e.limit == 200_000
        assert "Window full" in str(e)

    def test_is_exception(self):
        e = ContextWindowExceededError("test")
        assert isinstance(e, Exception)


# ══════════════════════════════════════════════════════════════════════════
#  WindowState dataclass
# ══════════════════════════════════════════════════════════════════════════


class TestWindowState:
    def test_defaults(self):
        ws = WindowState()
        assert ws.estimated_tokens == 0
        assert ws.status == WindowStatus.OK
        assert ws.warn_count == 0
        assert ws.continuation_count == 0
        assert ws.max_continuations == 5

"""Tests for ClaudeProvider — SDK layer unit tests.

PH8-PR-8.6: Verify complete() + stream() + tool calling + Prompt Caching + error handling.
"""
import pytest
from unittest.mock import MagicMock, patch


class TestClaudeProviderComplete:
    """Test ClaudeProvider.complete() method."""

    def test_complete_basic_response(self):
        """complete() returns LLMResponse with content from API."""
        from alice_engine.providers.claude import ClaudeProvider

        mock_response = MagicMock()
        mock_response.content = [MagicMock(type="text", text="Hello from Claude")]
        mock_response.usage = MagicMock(input_tokens=10, output_tokens=5)
        mock_response.model = "claude-sonnet-4-6"
        mock_response.stop_reason = "end_turn"

        with patch("alice_engine.providers.claude.Anthropic") as MockAnthropic:
            mock_client = MagicMock()
            mock_client.messages.create.return_value = mock_response
            MockAnthropic.return_value = mock_client

            provider = ClaudeProvider(api_key="sk-test")
            result = provider.complete("system", "user")

        assert result.content == "Hello from Claude"
        assert result.model == "claude-sonnet-4-6"
        assert result.finish_reason == "end_turn"
        assert result.usage["input"] == 10
        assert result.usage["output"] == 5

    def test_complete_with_prompt_caching_enabled(self):
        """complete() adds cache_control when cache_system=True and prompt ≥1024 chars."""
        from alice_engine.providers.claude import ClaudeProvider

        long_system = "x" * 1024  # exactly 1024 chars
        mock_response = MagicMock()
        mock_response.content = [MagicMock(type="text", text="ok")]
        mock_response.usage = MagicMock(input_tokens=10, output_tokens=5, cache_read_input_tokens=0, cache_creation_input_tokens=1000)
        mock_response.model = "claude-sonnet-4-6"
        mock_response.stop_reason = "end_turn"

        with patch("alice_engine.providers.claude.Anthropic") as MockAnthropic:
            mock_client = MagicMock()
            mock_client.messages.create.return_value = mock_response
            MockAnthropic.return_value = mock_client

            provider = ClaudeProvider(api_key="sk-test")
            result = provider.complete(long_system, "user", cache_system=True)

            # Verify cache_control was added to system block
            call_kwargs = mock_client.messages.create.call_args[1]
            system_block = call_kwargs["system"]
            assert isinstance(system_block, list)
            assert system_block[0]["type"] == "text"
            assert system_block[0]["text"] == long_system
            assert system_block[0]["cache_control"] == {"type": "ephemeral"}

        assert result.usage["cache_creation_input_tokens"] == 1000

    def test_complete_with_tool_calling(self):
        """complete() handles tool_use blocks correctly."""
        from alice_engine.providers.claude import ClaudeProvider

        mock_text_block = MagicMock(type="text", text="Let me check that.")
        mock_tool_block = MagicMock(type="tool_use", id="toolu_123", name="get_weather", input={"city": "NYC"})
        mock_response = MagicMock()
        mock_response.content = [mock_text_block, mock_tool_block]
        mock_response.usage = MagicMock(input_tokens=20, output_tokens=15)
        mock_response.model = "claude-sonnet-4-6"
        mock_response.stop_reason = "tool_use"

        with patch("alice_engine.providers.claude.Anthropic") as MockAnthropic:
            mock_client = MagicMock()
            mock_client.messages.create.return_value = mock_response
            MockAnthropic.return_value = mock_client

            provider = ClaudeProvider(api_key="sk-test")
            tools = [{"function": {"name": "get_weather", "description": "Get weather", "parameters": {"type": "object"}}}]
            result = provider.complete("system", "user", tools=tools)

        assert result.content == "Let me check that."
        assert len(result.tool_calls) == 1
        assert result.tool_calls[0]["id"] == "toolu_123"
        assert result.tool_calls[0]["name"] == "get_weather"
        assert result.tool_calls[0]["input"] == {"city": "NYC"}
        assert result.finish_reason == "tool_use"

    def test_complete_api_key_missing_returns_error_response(self):
        """complete() returns error LLMResponse when API key is missing (no exception)."""
        from alice_engine.providers.claude import ClaudeProvider

        provider = ClaudeProvider(api_key="")  # empty key
        result = provider.complete("system", "user")

        assert result.finish_reason == "error"
        assert "ANTHROPIC_API_KEY" in result.content
        assert result.model == "claude-sonnet-4-6"  # default model preserved

    def test_complete_api_error_returns_error_response(self):
        """complete() returns error LLMResponse when API raises exception."""
        from alice_engine.providers.claude import ClaudeProvider

        with patch("alice_engine.providers.claude.Anthropic") as MockAnthropic:
            mock_client = MagicMock()
            mock_client.messages.create.side_effect = Exception("API timeout")
            MockAnthropic.return_value = mock_client

            provider = ClaudeProvider(api_key="sk-test")
            result = provider.complete("system", "user")

        assert result.finish_reason == "error"
        assert "API timeout" in result.content


class TestClaudeProviderStream:
    """Test ClaudeProvider.stream() method."""

    def test_stream_basic_text(self):
        """stream() yields content_start, content_chunk*, content_end, done."""
        from alice_engine.providers.claude import ClaudeProvider

        # Mock streaming events
        mock_message_start = MagicMock(type="message_start")
        mock_message_start.message = MagicMock(model="claude-sonnet-4-6", usage=MagicMock(input_tokens=10))

        mock_block_start = MagicMock(type="content_block_start")
        mock_block_start.content_block = MagicMock(type="text")

        mock_delta1 = MagicMock(type="content_block_delta")
        mock_delta1.delta = MagicMock(type="text_delta", text="Hello")

        mock_delta2 = MagicMock(type="content_block_delta")
        mock_delta2.delta = MagicMock(type="text_delta", text=" world")

        mock_block_stop = MagicMock(type="content_block_stop")

        mock_message_delta = MagicMock(type="message_delta")
        mock_message_delta.delta = MagicMock(stop_reason="end_turn")
        mock_message_delta.usage = MagicMock(output_tokens=5)

        mock_stream = [mock_message_start, mock_block_start, mock_delta1, mock_delta2, mock_block_stop, mock_message_delta]

        with patch("alice_engine.providers.claude.Anthropic") as MockAnthropic:
            mock_client = MagicMock()
            mock_client.messages.create.return_value = iter(mock_stream)
            MockAnthropic.return_value = mock_client

            provider = ClaudeProvider(api_key="sk-test")
            events = list(provider.stream("system", "user"))

        # Verify event sequence
        assert events[0].type == "content_start"
        assert events[1].type == "content_chunk"
        assert events[1].content == "Hello"
        assert events[2].type == "content_chunk"
        assert events[2].content == " world"
        assert events[3].type == "content_end"
        assert events[4].type == "done"
        assert events[4].finish_reason == "end_turn"
        assert events[4].token_usage["input"] == 10
        assert events[4].token_usage["output"] == 5

    def test_stream_api_key_missing_yields_error(self):
        """stream() yields error event when API key is missing."""
        from alice_engine.providers.claude import ClaudeProvider

        provider = ClaudeProvider(api_key="")
        events = list(provider.stream("system", "user"))

        assert len(events) == 1
        assert events[0].type == "error"
        assert "ANTHROPIC_API_KEY" in events[0].error_message


class TestClaudeProviderMisc:
    """Miscellaneous ClaudeProvider tests."""

    def test_supports_tools_returns_true(self):
        """supports_tools() always returns True."""
        from alice_engine.providers.claude import ClaudeProvider

        provider = ClaudeProvider(api_key="sk-test")
        assert provider.supports_tools() is True

    def test_provider_metadata(self):
        """Provider has correct metadata."""
        from alice_engine.providers.claude import ClaudeProvider

        assert ClaudeProvider.provider_name == "claude"
        assert ClaudeProvider.provider_supports_tools is True
        assert ClaudeProvider.provider_supports_streaming is True

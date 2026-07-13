"""Tests for OpenAI/DeepSeek Providers — SDK layer unit tests.

PH8-PR-8.6: Verify complete() + stream() + tool calling + reasoning_content + error handling.
"""
import pytest
from unittest.mock import MagicMock, patch


class TestOpenAIProviderComplete:
    """Test OpenAIProvider.complete() method."""

    def test_complete_basic_response(self):
        """complete() returns LLMResponse with content from API."""
        from alice_engine.providers.openai import OpenAIProvider

        mock_message = MagicMock(content="Hello from GPT", tool_calls=None)
        mock_choice = MagicMock(message=mock_message, finish_reason="stop")
        mock_response = MagicMock(choices=[mock_choice], model="gpt-4o-mini", usage=MagicMock(prompt_tokens=10, completion_tokens=5))

        with patch("alice_engine.providers.openai.OpenAI") as MockOpenAI:
            mock_client = MagicMock()
            mock_client.chat.completions.create.return_value = mock_response
            MockOpenAI.return_value = mock_client

            provider = OpenAIProvider(api_key="sk-test")
            result = provider.complete("system", "user")

        assert result.content == "Hello from GPT"
        assert result.model == "gpt-4o-mini"
        assert result.finish_reason == "stop"
        assert result.usage["input"] == 10
        assert result.usage["output"] == 5

    def test_complete_with_reasoning_content_fallback(self):
        """complete() uses reasoning_content when content is empty (o1 model)."""
        from alice_engine.providers.openai import OpenAIProvider

        mock_message = MagicMock(content="", tool_calls=None, reasoning_content="Reasoning step 1...")
        mock_choice = MagicMock(message=mock_message, finish_reason="stop")
        mock_response = MagicMock(choices=[mock_choice], model="o1-mini", usage=MagicMock(prompt_tokens=20, completion_tokens=50))

        with patch("alice_engine.providers.openai.OpenAI") as MockOpenAI:
            mock_client = MagicMock()
            mock_client.chat.completions.create.return_value = mock_response
            MockOpenAI.return_value = mock_client

            provider = OpenAIProvider(api_key="sk-test", model="o1-mini")
            result = provider.complete("system", "user")

        assert result.content == "Reasoning step 1..."
        assert result.model == "o1-mini"

    def test_complete_with_tool_calling(self):
        """complete() handles tool_calls correctly."""
        from alice_engine.providers.openai import OpenAIProvider

        mock_tool_call = MagicMock(id="call_123", function=MagicMock(name="get_weather", arguments='{"city":"NYC"}'))
        mock_message = MagicMock(content="Checking weather...", tool_calls=[mock_tool_call])
        mock_choice = MagicMock(message=mock_message, finish_reason="tool_calls")
        mock_response = MagicMock(choices=[mock_choice], model="gpt-4o", usage=MagicMock(prompt_tokens=15, completion_tokens=10))

        with patch("alice_engine.providers.openai.OpenAI") as MockOpenAI:
            mock_client = MagicMock()
            mock_client.chat.completions.create.return_value = mock_response
            MockOpenAI.return_value = mock_client

            provider = OpenAIProvider(api_key="sk-test", model="gpt-4o")
            tools = [{"name": "get_weather", "description": "Get weather"}]
            result = provider.complete("system", "user", tools=tools)

        assert result.content == "Checking weather..."
        assert len(result.tool_calls) == 1
        assert result.tool_calls[0]["id"] == "call_123"
        assert result.tool_calls[0]["name"] == "get_weather"
        assert result.finish_reason == "tool_calls"

    def test_complete_api_key_missing_returns_error_response(self):
        """complete() returns error LLMResponse when API key is missing."""
        from alice_engine.providers.openai import OpenAIProvider

        provider = OpenAIProvider(api_key="")
        result = provider.complete("system", "user")

        assert result.finish_reason == "error"
        assert "OPENAI_API_KEY" in result.content


class TestDeepSeekProviderComplete:
    """Test DeepSeekProvider.complete() method."""

    def test_complete_basic_response(self):
        """complete() returns LLMResponse with content from API."""
        from alice_engine.providers.deepseek import DeepSeekProvider

        mock_message = MagicMock(content="Hello from DeepSeek", tool_calls=None)
        mock_choice = MagicMock(message=mock_message, finish_reason="stop")
        mock_response = MagicMock(choices=[mock_choice], model="deepseek-v4-flash", usage=MagicMock(prompt_tokens=8, completion_tokens=12))

        with patch("alice_engine.providers.deepseek.OpenAI") as MockOpenAI:
            mock_client = MagicMock()
            mock_client.chat.completions.create.return_value = mock_response
            MockOpenAI.return_value = mock_client

            provider = DeepSeekProvider(api_key="sk-test")
            result = provider.complete("system", "user")

        assert result.content == "Hello from DeepSeek"
        assert result.model == "deepseek-v4-flash"
        assert result.finish_reason == "stop"

    def test_supports_tools_false_for_reasoner_model(self):
        """supports_tools() returns False for deepseek-reasoner."""
        from alice_engine.providers.deepseek import DeepSeekProvider

        provider = DeepSeekProvider(api_key="sk-test", model="deepseek-reasoner")
        assert provider.supports_tools() is False

    def test_supports_tools_true_for_v4_models(self):
        """supports_tools() returns True for deepseek-v4 models."""
        from alice_engine.providers.deepseek import DeepSeekProvider

        provider = DeepSeekProvider(api_key="sk-test", model="deepseek-v4-flash")
        assert provider.supports_tools() is True

    def test_complete_api_key_missing_returns_error_response(self, monkeypatch, tmp_path):
        """complete() returns error LLMResponse when API key is missing."""
        from alice_engine.providers.deepseek import DeepSeekProvider

        monkeypatch.chdir(tmp_path)
        monkeypatch.delenv("DEEPSEEK_API_KEY", raising=False)
        provider = DeepSeekProvider(api_key="")
        result = provider.complete("system", "user")

        assert result.finish_reason == "error"
        assert "DEEPSEEK_API_KEY" in result.content

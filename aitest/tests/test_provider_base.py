"""Unit tests for llm/provider_base.py and provider factory."""
import pytest
from aitest.llm.provider_base import LLMResponse, StreamEvent, LLMProvider, _get_config


class TestLLMResponse:
    def test_defaults(self):
        r = LLMResponse(content="hello")
        assert r.content == "hello"
        assert r.tool_calls == []
        assert r.token_usage == {}
        assert r.model == ""
        assert r.finish_reason == ""

    def test_full(self):
        r = LLMResponse(
            content="ok", tool_calls=[{"name": "test"}],
            token_usage={"input": 10, "output": 5},
            model="claude-fable-5", finish_reason="stop",
        )
        assert r.model == "claude-fable-5"
        assert r.finish_reason == "stop"
        assert r.token_usage["input"] == 10
        assert len(r.tool_calls) == 1


class TestStreamEvent:
    def test_content_chunk(self):
        e = StreamEvent(type="content_chunk", content="hello")
        assert e.type == "content_chunk"
        assert e.content == "hello"

    def test_tool_use(self):
        e = StreamEvent(type="tool_use_start", tool_name="search", tool_id="abc")
        assert e.tool_name == "search"

    def test_done(self):
        e = StreamEvent(type="done", finish_reason="stop", token_usage={"input": 5})
        assert e.finish_reason == "stop"


class TestLLMProviderABC:
    def test_cannot_instantiate_abstract(self):
        with pytest.raises(TypeError):
            LLMProvider()  # abstract — missing complete/stream_complete/supports_tools


class TestProviderFactory:
    def test_list_providers(self):
        from aitest.llm.provider import list_providers
        providers = list_providers()
        assert "claude" in providers
        assert "openai" in providers
        assert "ollama" in providers
        assert "deepseek" in providers

    def test_get_provider_claude(self):
        from aitest.llm.provider import get_provider
        llm = get_provider("claude")
        from alice_engine.providers.claude import ClaudeProvider
        assert isinstance(llm, ClaudeProvider)

    def test_get_provider_deepseek(self):
        from aitest.llm.provider import get_provider
        llm = get_provider("deepseek")
        from alice_engine.providers.deepseek import DeepSeekProvider
        assert isinstance(llm, DeepSeekProvider)

    def test_get_provider_unknown_raises(self):
        from aitest.llm.provider import get_provider
        from alice_engine.exceptions import LLMProviderError
        with pytest.raises(LLMProviderError, match="未知 Provider"):
            get_provider("nonexistent")

    def test_backward_compat_import(self):
        # Verify old import paths still work
        from aitest.llm.provider import LLMResponse, ClaudeProvider, get_provider
        assert LLMResponse is not None
        assert ClaudeProvider is not None
        assert get_provider is not None

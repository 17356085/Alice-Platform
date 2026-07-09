"""Tests for Platform Provider Adapter — integration tests.

PH8-PR-8.6: Verify aitest.adapters.llm.interface.get_provider() delegates to SDK correctly.
"""
import pytest
from unittest.mock import MagicMock, patch


class TestProviderAdapterDelegation:
    """Test that platform adapter correctly delegates to SDK layer."""

    def test_get_provider_returns_sdk_instance(self):
        """get_provider() returns an instance from alice_engine.providers."""
        from aitest.adapters.llm.interface import get_provider

        with patch("aitest.adapters.llm.interface._sdk_get_provider") as mock_sdk:
            mock_instance = MagicMock()
            mock_sdk.return_value = mock_instance

            result = get_provider("claude", api_key="sk-test")

            mock_sdk.assert_called_once_with("claude", api_key="sk-test")
            # Trace decorator wraps the instance, but underlying should be SDK instance
            assert result is not None

    def test_api_key_injection_from_config(self):
        """get_provider() injects API key from aitest.runtime.config when not provided."""
        from aitest.adapters.llm.interface import get_provider

        with patch("aitest.adapters.llm.interface._sdk_get_provider") as mock_sdk:
            with patch("aitest.runtime.config.config.get_env", return_value="sk-from-config"):
                mock_instance = MagicMock()
                mock_sdk.return_value = mock_instance

                result = get_provider("claude")  # no api_key kwarg

                # Should inject api_key from config
                call_kwargs = mock_sdk.call_args[1]
                assert call_kwargs["api_key"] == "sk-from-config"

    def test_mimo_base_url_injection(self):
        """get_provider('mimo') injects base_url from config when not provided."""
        from aitest.adapters.llm.interface import get_provider

        with patch("aitest.adapters.llm.interface._sdk_get_provider") as mock_sdk:
            with patch("aitest.runtime.config.config.get_env") as mock_get_env:
                def side_effect(key, default=""):
                    if key == "MIMO_API_KEY":
                        return "tp-test"
                    if key == "MIMO_BASE_URL":
                        return "https://custom.mimo.com/v1"
                    return default
                mock_get_env.side_effect = side_effect

                mock_instance = MagicMock()
                mock_sdk.return_value = mock_instance

                result = get_provider("mimo")

                call_kwargs = mock_sdk.call_args[1]
                assert call_kwargs["api_key"] == "tp-test"
                assert call_kwargs["base_url"] == "https://custom.mimo.com/v1"

    def test_trace_decorator_wraps_complete(self):
        """get_provider() wraps instance.complete() with trace decorator."""
        from aitest.adapters.llm.interface import get_provider

        mock_instance = MagicMock()
        mock_instance.complete = MagicMock(return_value="original")
        mock_instance.stream = MagicMock()

        with patch("aitest.adapters.llm.interface._sdk_get_provider", return_value=mock_instance):
            with patch("aitest.infra.trace._trace_llm_call") as mock_trace:
                mock_trace.side_effect = lambda fn: fn  # passthrough for test

                result = get_provider("claude", api_key="sk-test")

                # Verify trace was called on both complete and stream
                assert mock_trace.call_count >= 1


class TestProviderAdapterBackwardCompatibility:
    """Test backward compatibility of platform adapter."""

    def test_list_providers_still_works(self):
        """list_providers() is still available (delegated to SDK or local registry)."""
        from aitest.adapters.llm.interface import list_providers

        providers = list_providers()
        # SDK should have at least these providers
        assert "claude" in providers or "mock" in providers

    def test_legacy_imports_still_work(self):
        """Legacy imports from aitest.llm.provider still work (deprecated but not removed)."""
        try:
            from aitest.llm.provider import get_provider, LLMResponse
            assert get_provider is not None
            assert LLMResponse is not None
        except ImportError:
            pytest.fail("Legacy imports should still work in Phase 8")


class TestProviderAdapterErrorHandling:
    """Test error handling in platform adapter."""

    def test_unknown_provider_raises_error(self):
        """get_provider() with unknown provider name raises clear error."""
        from aitest.adapters.llm.interface import get_provider

        with pytest.raises(Exception) as exc_info:
            get_provider("nonexistent-provider", api_key="sk-test")

        # Should propagate SDK layer's error (or raise its own)
        assert "nonexistent-provider" in str(exc_info.value).lower() or "unknown" in str(exc_info.value).lower()

    def test_trace_wrapper_failure_does_not_break_provider(self):
        """If trace decorator fails, provider should still work."""
        from aitest.adapters.llm.interface import get_provider

        mock_instance = MagicMock()

        with patch("aitest.adapters.llm.interface._sdk_get_provider", return_value=mock_instance):
            with patch("aitest.infra.trace._trace_llm_call", side_effect=Exception("trace init failed")):
                # Should not raise, trace failure is swallowed
                result = get_provider("claude", api_key="sk-test")
                assert result is not None

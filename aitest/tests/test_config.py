"""Unit tests for config.py — unified configuration."""
import os
import pytest
from aitest.config import Config, _env, _env_int


class TestConfigDefaults:
    """Test that config properties return sensible defaults when env vars are unset."""

    def setup_method(self):
        # Save and clear relevant env vars
        self._saved = {}
        for k in ("AITEST_PROVIDER", "AITEST_PROJECT", "BU_LLM_PROVIDER",
                   "ANTHROPIC_API_KEY", "OPENAI_API_KEY", "DEEPSEEK_API_KEY",
                   "MIMO_API_KEY", "GOOGLE_API_KEY", "BROWSER_WS_URL",
                   "DEFAULT_PASSWORD", "DEFAULT_USERNAME", "BASE_URL"):
            self._saved[k] = os.environ.pop(k, None)

    def teardown_method(self):
        for k, v in self._saved.items():
            if v is not None:
                os.environ[k] = v

    def test_audit_interval_default(self):
        c = Config()
        assert c.audit_interval == 86400

    def test_base_url_default(self):
        c = Config()
        assert "localhost" in c.base_url

    def test_default_username(self):
        c = Config()
        assert c.default_username == "admin"

    def test_default_password_empty(self):
        c = Config()
        assert c.default_password == ""

    def test_bu_llm_provider_default(self):
        c = Config()
        assert c.bu_llm_provider == "claude"

    def test_ollama_base_url_default(self):
        c = Config()
        assert "11434" in c.ollama_base_url

    def test_database_url_default(self):
        c = Config()
        assert "sqlite" in c.database_url

    def test_get_provider_config_claude(self):
        c = Config()
        cfg = c.get_provider_config("claude")
        assert cfg["model"] == "claude-sonnet-4-6"

    def test_get_provider_config_unknown(self):
        c = Config()
        cfg = c.get_provider_config("nonexistent")
        assert cfg["model"] == "claude-sonnet-4-6"  # falls back to claude

    def test_langchain_tracing_default(self):
        c = Config()
        assert c.langchain_tracing is False

    def test_github_token_default(self):
        c = Config()
        assert c.github_token == ""

    def test_browser_ws_url_default(self):
        c = Config()
        assert c.browser_ws_url == ""

    def test_resolve_llm_provider_no_keys(self):
        c = Config()
        # With all API keys cleared, should fall back to deepseek
        provider = c.resolve_llm_provider()
        assert provider == "deepseek"

    def test_resolve_llm_provider_explicit(self):
        os.environ["AITEST_PROVIDER"] = "claude"
        c = Config()
        assert c.resolve_llm_provider() == "claude"


class TestEnvHelpers:
    """Test the _env and _env_int helpers."""

    def test_env_with_default(self):
        assert _env("NONEXISTENT_VAR_12345", "fallback") == "fallback"

    def test_env_reads_real(self):
        os.environ["_TEST_CONFIG_VAR"] = "hello"
        assert _env("_TEST_CONFIG_VAR", "") == "hello"
        del os.environ["_TEST_CONFIG_VAR"]

    def test_env_int_with_string(self):
        os.environ["_TEST_INT_VAR"] = "42"
        assert _env_int("_TEST_INT_VAR", 0) == 42
        del os.environ["_TEST_INT_VAR"]

    def test_env_int_with_default(self):
        assert _env_int("NONEXISTENT_INT_VAR", 99) == 99

    def test_env_int_with_invalid(self):
        os.environ["_TEST_BAD_INT"] = "not_a_number"
        assert _env_int("_TEST_BAD_INT", 10) == 10
        del os.environ["_TEST_BAD_INT"]

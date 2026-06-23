"""
Unified configuration — single entry point for all ENV vars and runtime settings.

Usage:
    from aitest.config import config

    provider = config.aitest_provider          # "claude"
    key = config.anthropic_api_key             # from .env
    interval = config.audit_interval           # 86400
    llm = config.resolve_llm_provider()        # first available provider

Replaces scattered os.environ/os.getenv calls across 10+ files.
All keys documented with defaults and purpose.
"""

import os
from pathlib import Path
from typing import Optional


# ── Bootstrap: load .env once ──────────────────────────────────────────
_PROJECT_ROOT = Path(__file__).resolve().parent.parent
_ENV_FILE = _PROJECT_ROOT / ".env"
if _ENV_FILE.exists():
    try:
        from dotenv import load_dotenv
        load_dotenv(_ENV_FILE)
    except ImportError:
        pass


def _env(key: str, default: str = "") -> str:
    """Read env var with default."""
    return os.environ.get(key, default)


def _env_int(key: str, default: int = 0) -> int:
    """Read env var as int with default."""
    try:
        return int(_env(key, str(default)))
    except ValueError:
        return default


class Config:
    """Unified configuration accessor."""

    # ── Platform ────────────────────────────────────────────────────
    @property
    def aitest_project(self) -> str:
        """Active project ID. Set via `aitest project set` or AITEST_PROJECT env."""
        return _env("AITEST_PROJECT", "")

    @property
    def aitest_provider(self) -> str:
        """Explicit LLM provider override for chat/agent."""
        return _env("AITEST_PROVIDER", "")

    @property
    def audit_interval(self) -> int:
        """Scheduled audit interval in seconds (default: 24h)."""
        return _env_int("AITEST_AUDIT_INTERVAL", 86400)

    # ── LLM API Keys ────────────────────────────────────────────────
    @property
    def anthropic_api_key(self) -> str:
        return _env("ANTHROPIC_API_KEY", "")

    @property
    def openai_api_key(self) -> str:
        return _env("OPENAI_API_KEY", "")

    @property
    def deepseek_api_key(self) -> str:
        return _env("DEEPSEEK_API_KEY", "")

    @property
    def mimo_api_key(self) -> str:
        return _env("MIMO_API_KEY", "")

    @property
    def mimo_base_url(self) -> str:
        return _env("MIMO_BASE_URL", "")

    @property
    def mimo_model(self) -> str:
        return _env("MIMO_MODEL", "mimo-v2.5-pro")

    @property
    def mimo_vision_model(self) -> str:
        return _env("MIMO_VISION_MODEL", "mimo-v2.5")

    @property
    def google_api_key(self) -> str:
        return _env("GOOGLE_API_KEY", "")

    @property
    def ollama_base_url(self) -> str:
        return _env("OLLAMA_BASE_URL", "http://localhost:11434")

    # ── Provider chain ───────────────────────────────────────────────
    def resolve_llm_provider(self) -> str:
        """Resolve which LLM provider to use.

        Priority: AITEST_PROVIDER > first available API key > deepseek.
        """
        explicit = self.aitest_provider
        if explicit:
            return explicit
        providers = [
            ("claude", "ANTHROPIC_API_KEY"),
            ("openai", "OPENAI_API_KEY"),
            ("deepseek", "DEEPSEEK_API_KEY"),
            ("mimo", "MIMO_API_KEY"),
            ("gemini", "GOOGLE_API_KEY"),
        ]
        for name, env_key in providers:
            if _env(env_key):
                return name
        return "deepseek"  # ultimate fallback (uses free tier)

    # ── Browser Use ─────────────────────────────────────────────────
    @property
    def bu_llm_provider(self) -> str:
        """BrowserUse LLM provider (mimo | claude | gemini)."""
        return _env("BU_LLM_PROVIDER", "claude")

    @property
    def base_url(self) -> str:
        """SUT base URL for browser automation."""
        return _env("BASE_URL", "http://localhost:8081/")

    @property
    def default_username(self) -> str:
        return _env("DEFAULT_USERNAME", "admin")

    @property
    def default_password(self) -> str:
        return _env("DEFAULT_PASSWORD", "")

    # ── Remote Browser ─────────────────────────────────────────────
    @property
    def browser_ws_url(self) -> str:
        """CDP WebSocket URL for remote browser (chrome-devtools://, ws://, wss://)."""
        return _env("BROWSER_WS_URL", "")

    @property
    def browser_api_key(self) -> str:
        """API key for cloud browser services (Browserbase, etc.)."""
        return _env("BROWSER_API_KEY", "")

    # ── Integrations ────────────────────────────────────────────────
    @property
    def github_token(self) -> str:
        return _env("GITHUB_TOKEN", "")

    @property
    def github_repository(self) -> str:
        return _env("GITHUB_REPOSITORY", "")

    # ── Database ────────────────────────────────────────────────────
    @property
    def database_url(self) -> str:
        return _env("DATABASE_URL", f"sqlite:///{_PROJECT_ROOT / 'chat_sessions.db'}")

    # ── LangChain / LangGraph ───────────────────────────────────────
    @property
    def langchain_tracing(self) -> bool:
        return _env("LANGCHAIN_TRACING_V2", "false").lower() == "true"

    # ── Provider-specific defaults ──────────────────────────────────
    def get_provider_config(self, provider: str) -> dict:
        """Get (api_key, base_url, model) for a named provider."""
        defaults = {
            "claude": {"api_key": self.anthropic_api_key, "base_url": "", "model": "claude-sonnet-4-6"},
            "openai": {"api_key": self.openai_api_key, "base_url": "", "model": "gpt-4o"},
            "deepseek": {"api_key": self.deepseek_api_key, "base_url": "", "model": "deepseek-v4-pro"},
            "mimo": {"api_key": self.mimo_api_key, "base_url": self.mimo_base_url, "model": self.mimo_model},
            "gemini": {"api_key": self.google_api_key, "base_url": "", "model": "gemini-2.5-flash"},
            "ollama": {"api_key": "", "base_url": self.ollama_base_url, "model": "llama3"},
        }
        return defaults.get(provider, defaults["claude"])


# Singleton
config = Config()

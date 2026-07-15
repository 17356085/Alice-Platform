"""Application configuration with no dependency on runtime or platform layers."""

import os
from pathlib import Path


_PROJECT_ROOT = Path(__file__).resolve().parents[1]


def _load_project_env() -> None:
    """Load the project .env without replacing explicit process variables."""
    env_path = _PROJECT_ROOT / ".env"
    try:
        from dotenv import load_dotenv
    except ImportError:
        load_dotenv = None

    if load_dotenv is not None:
        load_dotenv(env_path, override=False)
        return
    if not env_path.is_file():
        return

    for raw_line in env_path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip()
        if not key or key in os.environ:
            continue
        if len(value) >= 2 and value[0] == value[-1] and value[0] in {"'", '"'}:
            value = value[1:-1]
        os.environ[key] = value


_load_project_env()


def _env(key: str, default: str = "") -> str:
    return os.environ.get(key, default)


def _env_int(key: str, default: int = 0) -> int:
    try:
        return int(os.environ.get(key, str(default)))
    except (ValueError, TypeError):
        return default


class RuntimeConfig:
    """Runtime configuration shared by CLI, server, and provider adapters."""

    @property
    def aitest_project(self) -> str:
        return _env("AITEST_PROJECT", "default")

    @property
    def aitest_provider(self) -> str:
        return _env("AITEST_PROVIDER", "anthropic")

    @property
    def audit_interval(self) -> int:
        return _env_int("AUDIT_INTERVAL", 86400)

    @property
    def base_url(self) -> str:
        return _env("BASE_URL", "http://localhost:8000")

    @property
    def default_username(self) -> str:
        return _env("DEFAULT_USERNAME", "admin")

    @property
    def default_password(self) -> str:
        return _env("DEFAULT_PASSWORD", "")

    @property
    def bu_llm_provider(self) -> str:
        return _env("BU_LLM_PROVIDER", "claude")

    @property
    def ollama_base_url(self) -> str:
        return _env("OLLAMA_BASE_URL", "http://localhost:11434")

    @property
    def mimo_base_url(self) -> str:
        return _env("MIMO_BASE_URL", "")

    @property
    def database_url(self) -> str:
        return _env("DATABASE_URL", "sqlite:///governance/.data/aitest.db")

    @property
    def langchain_tracing(self) -> bool:
        return _env("LANGCHAIN_TRACING_V2", "").lower() == "true"

    @property
    def github_token(self) -> str:
        return _env("GITHUB_TOKEN", "")

    @property
    def browser_ws_url(self) -> str:
        return _env("BROWSER_WS_URL", "")

    def resolve_llm_provider(self) -> str:
        if os.environ.get("MOCK_LLM") == "1":
            return "mock"
        return os.environ.get("LLM_PROVIDER", self.aitest_provider)

    def resolve_model_for_tier(self, tier: str, provider: str) -> dict:
        return {"model": "claude-sonnet-4-6", "provider": provider}

    def get_provider_config(self, provider: str) -> dict:
        configs = {
            "claude": {
                "model": self.get_env("ANTHROPIC_MODEL", "claude-sonnet-4-6"),
                "provider": "claude",
                "api_key": self.get_env("ANTHROPIC_API_KEY"),
            },
            "anthropic": {
                "model": self.get_env("ANTHROPIC_MODEL", "claude-sonnet-4-6"),
                "provider": "claude",
                "api_key": self.get_env("ANTHROPIC_API_KEY"),
            },
            "deepseek": {
                "model": self.get_env("DEEPSEEK_MODEL", "deepseek-chat"),
                "provider": "deepseek",
                "api_key": self.get_env("DEEPSEEK_API_KEY"),
            },
            "openai": {
                "model": self.get_env("OPENAI_MODEL", "gpt-4o"),
                "provider": "openai",
                "api_key": self.get_env("OPENAI_API_KEY"),
            },
            "mimo": {
                "model": self.get_env("MIMO_MODEL", "mimo-latest"),
                "provider": "mimo",
                "api_key": self.get_env("MIMO_API_KEY"),
                "base_url": self.get_env("MIMO_BASE_URL"),
            },
            "gemini": {
                "model": self.get_env("GOOGLE_MODEL", "gemini-2.5-flash"),
                "provider": "gemini",
                "api_key": self.get_env("GOOGLE_API_KEY"),
            },
        }
        return configs.get(provider, configs["claude"])

    def get_env(self, key: str, default: str = "") -> str:
        return _env(key, default)


Config = RuntimeConfig
config = RuntimeConfig()

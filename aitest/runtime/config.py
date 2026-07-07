"""Runtime Config — 统一配置入口。"""

import os
from pathlib import Path


def _env(key: str, default: str = "") -> str:
    """读取环境变量，不存在返回默认值。"""
    return os.environ.get(key, default)


def _env_int(key: str, default: int = 0) -> int:
    """读取环境变量并转为整数，失败返回默认值。"""
    try:
        return int(os.environ.get(key, str(default)))
    except (ValueError, TypeError):
        return default


class RuntimeConfig:
    """运行时配置。"""

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
        """获取 Provider 配置。"""
        configs = {
            "claude": {"model": "claude-sonnet-4-6", "provider": "claude"},
            "deepseek": {"model": "deepseek-chat", "provider": "deepseek"},
            "openai": {"model": "gpt-4o", "provider": "openai"},
            "mimo": {"model": "mimo-latest", "provider": "mimo"},
        }
        return configs.get(provider, configs["claude"])

    def get_env(self, key: str, default: str = "") -> str:
        """读取环境变量。"""
        return _env(key, default)


# 向后兼容别名
Config = RuntimeConfig

config = RuntimeConfig()

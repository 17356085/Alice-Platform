"""Runtime Config — 统一配置入口。"""

import os
from pathlib import Path


class RuntimeConfig:
    """运行时配置。"""

    @property
    def aitest_project(self) -> str:
        return os.environ.get("AITEST_PROJECT", "default")

    @property
    def aitest_provider(self) -> str:
        return os.environ.get("AITEST_PROVIDER", "anthropic")

    def resolve_llm_provider(self) -> str:
        if os.environ.get("MOCK_LLM") == "1":
            return "mock"
        return os.environ.get("LLM_PROVIDER", self.aitest_provider)

    def resolve_model_for_tier(self, tier: str, provider: str) -> dict:
        return {"model": "claude-sonnet-4-6", "provider": provider}


config = RuntimeConfig()

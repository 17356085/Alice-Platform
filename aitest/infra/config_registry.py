"""
Config Registry — centralized configuration for all hardcoded values. v3.2

Replaces scattered hardcoded paths, timeouts, thresholds, and names
with a single source of truth. All modules read from here.

Usage:
    from aitest.infra.config_registry import cfg

    path = cfg.billing_dir
    timeout = cfg.task_stale_timeout_s
    agent = cfg.default_agent
"""

import os
from pathlib import Path
from dataclasses import dataclass, field


@dataclass
class PlatformConfig:
    """All configurable platform values.

    Each value can be overridden via environment variable.
    Defaults match the previous hardcoded values.
    """

    # ── Paths ──────────────────────────────────────────────────────────
    @property
    def base_dir(self) -> Path:
        """Root data directory. Default: governance/.data"""
        env = os.environ.get("AITEST_DATA_DIR", "")
        if env:
            return Path(env)
        from aitest.infra.paths import get_workstudy
        return get_workstudy() / "governance" / ".data"

    @property
    def billing_dir(self) -> Path:
        return self.base_dir / "billing"

    @property
    def metrics_dir(self) -> Path:
        return self.base_dir / "metrics"

    @property
    def usage_dir(self) -> Path:
        return self.base_dir / "usage"

    @property
    def reports_dir(self) -> Path:
        return self.base_dir / "reports"

    @property
    def dead_ends_dir(self) -> Path:
        return self.base_dir / "dead_ends"

    @property
    def counters_path(self) -> Path:
        return self.dead_ends_dir / "counters.json"

    @property
    def chromadb_path(self) -> str:
        """ChromaDB persist directory for TestingMemoryStore."""
        return os.environ.get("AITEST_CHROMADB_PATH", ".chroma_testing")

    @property
    def pause_base_dir(self) -> Path:
        """Pause/resume sentinel files directory."""
        return self.base_dir

    # ── Redis ──────────────────────────────────────────────────────────
    @property
    def redis_host(self) -> str:
        return os.environ.get("REDIS_HOST", "localhost")

    @property
    def redis_port(self) -> int:
        return int(os.environ.get("REDIS_PORT", "6379"))

    @property
    def redis_connect_timeout(self) -> int:
        return int(os.environ.get("REDIS_CONNECT_TIMEOUT", "1"))

    # ── Timeouts ───────────────────────────────────────────────────────
    @property
    def task_stale_timeout_s(self) -> int:
        """Task queue stale task timeout. Default: 30 minutes."""
        return int(os.environ.get("AITEST_TASK_STALE_TIMEOUT", "1800"))

    @property
    def parallel_run_timeout_s(self) -> int:
        """Parallel runner per-module timeout. Default: 30 minutes."""
        return int(os.environ.get("AITEST_PARALLEL_TIMEOUT", "1800"))

    @property
    def webhook_timeout_s(self) -> int:
        """Webhook HTTP POST timeout. Default: 10 seconds."""
        return int(os.environ.get("AITEST_WEBHOOK_TIMEOUT", "10"))

    @property
    def pause_resume_timeout_s(self) -> int:
        """Pause handler wait_for_resume timeout. Default: 2 hours."""
        return int(os.environ.get("AITEST_PAUSE_TIMEOUT", "7200"))

    # ── Thresholds ─────────────────────────────────────────────────────
    @property
    def dead_end_consecutive_failures(self) -> int:
        """Failures needed to trigger dead-end detection. Default: 3."""
        return int(os.environ.get("AITEST_DEAD_END_THRESHOLD", "3"))

    @property
    def dead_end_window_minutes(self) -> int:
        """Window for failure counting. Default: 30 minutes."""
        return int(os.environ.get("AITEST_DEAD_END_WINDOW", "30"))

    @property
    def dead_end_max_age_minutes(self) -> int:
        """Stale counters cleaned after. Default: 2 hours."""
        return int(os.environ.get("AITEST_DEAD_END_MAX_AGE", "120"))

    @property
    def ws_idle_timeout_s(self) -> int:
        """WebSocket idle timeout. Default: 5 minutes."""
        return int(os.environ.get("AITEST_WS_IDLE_TIMEOUT", "300"))

    # ── Agent defaults ─────────────────────────────────────────────────
    @property
    def default_agent(self) -> str:
        """Default agent for execution. Default: automation-agent."""
        return os.environ.get("AITEST_DEFAULT_AGENT", "automation-agent")

    @property
    def default_chat_agent(self) -> str:
        """Default agent for chat fallback. Default: test-design-agent."""
        return os.environ.get("AITEST_DEFAULT_CHAT_AGENT", "test-design-agent")

    # ── Tenant limits ──────────────────────────────────────────────────
    @property
    def tenant_max_concurrent_agents(self) -> int:
        return int(os.environ.get("AITEST_TENANT_MAX_AGENTS", "3"))

    @property
    def tenant_max_token_budget(self) -> int:
        return int(os.environ.get("AITEST_TENANT_MAX_TOKENS", "100000"))

    @property
    def tenant_max_sessions(self) -> int:
        return int(os.environ.get("AITEST_TENANT_MAX_SESSIONS", "100"))


# Singleton
cfg = PlatformConfig()

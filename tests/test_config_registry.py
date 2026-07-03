"""Test: Config Registry — verify hardcoded values migrated to centralized config.

Batch 5 of coupling fix plan. Verifies:
  1. config_registry.py exists and exports cfg
  2. All config values are accessible
  3. Modules import from config_registry instead of hardcoding
"""

import pytest
import os
import inspect


# ── 1. config_registry exists ──────────────────────────────────────────

def test_config_registry_exists():
    from aitest.platform.config_registry import cfg
    assert cfg is not None


def test_config_registry_has_all_properties():
    from aitest.platform.config_registry import cfg
    expected = [
        "base_dir", "billing_dir", "metrics_dir", "usage_dir", "reports_dir",
        "dead_ends_dir", "counters_path", "chromadb_path", "pause_base_dir",
        "redis_host", "redis_port", "redis_connect_timeout",
        "task_stale_timeout_s", "parallel_run_timeout_s", "webhook_timeout_s",
        "pause_resume_timeout_s",
        "dead_end_consecutive_failures", "dead_end_window_minutes", "dead_end_max_age_minutes",
        "ws_idle_timeout_s",
        "default_agent", "default_chat_agent",
        "tenant_max_concurrent_agents", "tenant_max_token_budget", "tenant_max_sessions",
    ]
    for prop in expected:
        assert hasattr(cfg, prop), f"cfg missing property: {prop}"


def test_config_registry_env_override():
    """Config values should be overridable via environment variables."""
    from aitest.platform.config_registry import PlatformConfig
    os.environ["AITEST_DEFAULT_AGENT"] = "custom-agent"
    try:
        custom_cfg = PlatformConfig()
        assert custom_cfg.default_agent == "custom-agent"
    finally:
        del os.environ["AITEST_DEFAULT_AGENT"]


# ── 2. Modules use config_registry ─────────────────────────────────────

MODULES_TO_CHECK = [
    ("aitest/platform/hooks/billing_hook.py", "cfg.billing_dir"),
    ("aitest/platform/hooks/metrics_consumer.py", "cfg.metrics_dir"),
    ("aitest/platform/hooks/quota_usage.py", "cfg.usage_dir"),
    ("aitest/platform/hooks/report_consumer.py", "cfg.reports_dir"),
    ("aitest/platform/memory_observer.py", "cfg.dead_end_consecutive_failures"),
    ("aitest/platform/testing_memory_store.py", "cfg.chromadb_path"),
    ("aitest/infra/task_queue.py", "cfg.task_stale_timeout_s"),
    ("aitest/infra/pause_handler.py", "cfg.pause_base_dir"),
    ("aitest/infra/redis_cache.py", "cfg.redis_host"),
    ("aitest/infra/redis_pubsub.py", "cfg.redis_host"),
]


@pytest.mark.parametrize("file_path,expected_import", MODULES_TO_CHECK)
def test_module_uses_config_registry(file_path, expected_import):
    """Verify module imports from config_registry instead of hardcoding."""
    full_path = os.path.join(os.path.dirname(__file__), "..", file_path)
    with open(full_path, encoding="utf-8") as f:
        content = f.read()
    assert "config_registry" in content, (
        f"{file_path} does not import config_registry"
    )

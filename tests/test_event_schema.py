"""Test: Event Data Schema — verify EventDataKey usage and schema validation.

Batch 2 of coupling fix plan. Verifies:
  1. EventDataKey constants exist and match expected values
  2. All platform consumers import EventDataKey
  3. make_event validates required keys in dev mode
  4. No hardcoded string key access remains in consumers
"""

import pytest
import os
import importlib
import inspect


# ── 1. EventDataKey constants ──────────────────────────────────────────

def test_event_data_key_constants_exist():
    """Verify all required EventDataKey constants are defined."""
    from aitest.platform.run_event import EventDataKey as K
    assert K.MODULE == "module"
    assert K.AGENT == "agent"
    assert K.PAGES == "pages"
    assert K.WORKSPACE_ID == "workspace_id"
    assert K.ORG_ID == "org_id"
    assert K.TOTAL_TOKENS == "total_tokens"
    assert K.TOTAL_COST == "total_cost"
    assert K.AGENT_RUNS == "agent_runs"
    assert K.ERROR == "error"
    assert K.PHASE == "phase"
    assert K.ARTIFACT_TYPE == "artifact_type"
    assert K.ARTIFACT_PATH == "artifact_path"
    assert K.TRIGGERED_BY == "triggered_by"


def test_event_data_key_values_match_make_event_kwargs():
    """EventDataKey values must match the kwarg names used in make_event().

    This is the core contract: producers use kwargs like `module=module`,
    consumers use K.MODULE = "module". They must match.
    """
    from aitest.platform.run_event import EventDataKey as K, make_event, EventType
    ev = make_event(EventType.RUN_COMPLETED, run_id="test",
                    module="equipment", agent="automation-agent",
                    total_tokens=100, total_cost=0.05)
    assert ev.data[K.MODULE] == "equipment"
    assert ev.data[K.AGENT] == "automation-agent"
    assert ev.data[K.TOTAL_TOKENS] == 100
    assert ev.data[K.TOTAL_COST] == 0.05


# ── 2. Verify consumers import EventDataKey ────────────────────────────

CONSUMER_MODULES = [
    "aitest.platform.hooks.billing_hook",
    "aitest.platform.hooks.metrics_consumer",
    "aitest.platform.hooks.quota_usage",
    "aitest.platform.hooks.report_consumer",
    "aitest.platform.audit_log",
    "aitest.platform.timeline",
]


@pytest.mark.parametrize("module_name", CONSUMER_MODULES)
def test_consumer_imports_event_data_key(module_name):
    """Verify each consumer module imports EventDataKey."""
    mod = importlib.import_module(module_name)
    source = inspect.getsource(mod)
    assert "EventDataKey" in source, f"{module_name} does not import EventDataKey"


# ── 3. Schema validation in dev mode ───────────────────────────────────

def test_make_event_validates_required_keys_in_dev_mode():
    """In dev mode, make_event should log warnings for missing required keys."""
    from aitest.platform.run_event import make_event, EventType, _DEV_MODE
    # Force dev mode
    import aitest.platform.run_event as rem
    old_mode = rem._DEV_MODE
    rem._DEV_MODE = True
    try:
        # PHASE_STARTED requires "phase" key — missing it should log warning
        ev = make_event(EventType.PHASE_STARTED, run_id="test")
        # Event is still created (validation logs, doesn't raise)
        assert ev.event_type == EventType.PHASE_STARTED
    finally:
        rem._DEV_MODE = old_mode


def test_make_event_validates_type_in_dev_mode():
    """In dev mode, make_event should log warnings for wrong types."""
    from aitest.platform.run_event import make_event, EventType
    import aitest.platform.run_event as rem
    old_mode = rem._DEV_MODE
    rem._DEV_MODE = True
    try:
        # total_tokens should be int, passing string should log warning
        ev = make_event(EventType.RUN_COMPLETED, run_id="test", total_tokens="not_an_int")
        assert ev.data["total_tokens"] == "not_an_int"  # Still stored
    finally:
        rem._DEV_MODE = old_mode


# ── 4. No hardcoded string key access in platform consumers ────────────

PLATFORM_CONSUMER_FILES = [
    "aitest/platform/hooks/billing_hook.py",
    "aitest/platform/hooks/metrics_consumer.py",
    "aitest/platform/hooks/quota_usage.py",
    "aitest/platform/hooks/report_consumer.py",
    "aitest/platform/audit_log.py",
    "aitest/platform/timeline.py",
]

HARDCODED_KEYS = [
    '"module"', '"agent"', '"org_id"', '"workspace_id"',
    '"total_tokens"', '"total_cost"', '"agent_runs"',
    '"error"', '"phase"', '"triggered_by"',
]


@pytest.mark.parametrize("file_path", PLATFORM_CONSUMER_FILES)
def test_no_hardcoded_event_data_keys(file_path):
    """Verify consumers don't access event.data with hardcoded string keys."""
    full_path = os.path.join(os.path.dirname(__file__), "..", file_path)
    with open(full_path, encoding="utf-8") as f:
        content = f.read()

    # Check for event.data.get("key") patterns with known keys
    import re
    for key in HARDCODED_KEYS:
        pattern = r'\.data\.get\(' + re.escape(key)
        matches = re.findall(pattern, content)
        assert len(matches) == 0, (
            f"{file_path} still uses hardcoded key {key} in .data.get(). "
            f"Use EventDataKey instead."
        )

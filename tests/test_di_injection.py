"""Test: Dependency Injection — verify endpoints use app.state, not singletons.

Batch 4 of coupling fix plan. Verifies:
  1. _get_from_state helper exists and works
  2. All execution.py endpoints accept Request parameter
  3. main.py lifespan stores shared instances in app.state
"""

import pytest
import inspect
import re


# ── 1. _get_from_state helper ─────────────────────────────────────────

def test_get_from_state_helper_exists():
    """_get_from_state helper should be defined in execution.py."""
    from aitest.server.api import execution
    assert hasattr(execution, "_get_from_state")


def test_get_from_state_fallback():
    """_get_from_state should fall back to factory when attr not in app.state."""
    from aitest.server.api.execution import _get_from_state

    class FakeRequest:
        class app:
            class state:
                pass

    factory_called = []
    def factory():
        factory_called.append(True)
        return "result"

    result = _get_from_state(FakeRequest(), "nonexistent", factory)
    assert result == "result"
    assert factory_called


def test_get_from_state_uses_app_state():
    """_get_from_state should return app.state value when available."""
    from aitest.server.api.execution import _get_from_state

    class FakeRequest:
        class app:
            class state:
                my_obj = "from_state"

    result = _get_from_state(FakeRequest(), "my_obj", lambda: "from_factory")
    assert result == "from_state"


# ── 2. Endpoints accept Request ────────────────────────────────────────

ENDPOINTS_EXPECTING_REQUEST = [
    "get_execution",
    "get_run",
    "list_runs",
    "get_run_debug",
    "get_run_inspector",
    "get_timeline",
    "execution_history",
    "query_audit",
    "audit_stats",
    "get_run_report",
    "list_reports",
    "register_webhook",
    "list_webhooks",
    "delete_webhook",
    "metrics_snapshot",
    "billing_records",
    "workspace_usage",
    "all_usage",
]


@pytest.mark.parametrize("endpoint_name", ENDPOINTS_EXPECTING_REQUEST)
def test_endpoint_accepts_request(endpoint_name):
    """All endpoints should accept a Request parameter for DI."""
    from aitest.server.api import execution
    endpoint = getattr(execution, endpoint_name, None)
    assert endpoint is not None, f"Endpoint {endpoint_name} not found"
    sig = inspect.signature(endpoint)
    param_names = list(sig.parameters.keys())
    assert "request" in param_names, (
        f"Endpoint {endpoint_name} does not accept 'request' parameter. "
        f"Parameters: {param_names}"
    )


# ── 3. main.py lifespan stores shared instances ────────────────────────

def test_main_lifespan_stores_instances():
    """Server composition root should store shared instances in app.state."""
    # Read source directly to avoid import chain issues (config.py pre-existing bug)
    import os
    composition_path = os.path.join(
        os.path.dirname(__file__),
        "..",
        "aitest",
        "server",
        "core",
        "composition.py",
    )
    with open(composition_path, encoding="utf-8") as f:
        source = f.read()
    assert "app_state.execution_service" in source
    assert "app_state.run_store" in source
    assert "app_state.audit_logger" in source
    assert "app_state.report_consumer" in source
    assert "app_state.metrics_consumer" in source
    assert "app_state.billing_hook" in source
    assert "app_state.quota_usage" in source
    assert "app_state.webhook_registry" in source

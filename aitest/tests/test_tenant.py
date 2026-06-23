"""Unit tests for tenant.py — multi-tenant resource governance."""
import pytest
from aitest.platform.tenant import (
    Tenant, TenantManager, TenantCapacityError, TenantLimits,
    get_tenant_manager,
)


class TestTenantCapacity:
    """Test per-tenant resource limits."""

    def test_check_capacity_allows_within_limit(self):
        t = Tenant("test-1", TenantLimits(max_concurrent_agents=2))
        t.check_capacity("agent_execution")  # 1
        t.check_capacity("agent_execution")  # 2 — ok

    def test_check_capacity_blocks_over_limit(self):
        t = Tenant("test-2", TenantLimits(max_concurrent_agents=1))
        t.check_capacity("agent_execution")  # takes the slot

        with pytest.raises(TenantCapacityError) as exc:
            t.check_capacity("agent_execution")
        assert exc.value.tenant_id == "test-2"
        assert "concurrent_agents" in exc.value.resource

    def test_release_frees_capacity(self):
        t = Tenant("test-3", TenantLimits(max_concurrent_agents=1))
        t.check_capacity("agent_execution")
        t.release("agent_execution")
        # Should succeed now
        t.check_capacity("agent_execution")

    def test_record_tokens_accumulates(self):
        t = Tenant("test-4")
        t.record_tokens(5000)
        t.record_tokens(3000)
        assert t.usage_summary()["token_usage_today"] == 8000

    def test_usage_summary_structure(self):
        t = Tenant("test-5")
        s = t.usage_summary()
        assert s["tenant_id"] == "test-5"
        assert "limits" in s
        assert "active_agents" in s


class TestTenantManager:
    """Test global tenant manager."""

    def test_get_creates_tenant(self):
        tm = TenantManager()
        t = tm.get("project-a")
        assert t.tenant_id == "project-a"

    def test_get_returns_same_instance(self):
        tm = TenantManager()
        t1 = tm.get("project-b")
        t2 = tm.get("project-b")
        assert t1 is t2

    def test_all_usage(self):
        tm = TenantManager()
        tm.get("proj-1").record_tokens(100)
        tm.get("proj-2").record_tokens(200)
        usage = tm.all_usage()
        assert "proj-1" in usage
        assert usage["proj-1"]["token_usage_today"] == 100

    def test_singleton(self):
        tm1 = get_tenant_manager()
        tm2 = get_tenant_manager()
        assert tm1 is tm2

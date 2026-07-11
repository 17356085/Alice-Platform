"""P3-6 Billing REST API 测试

覆盖:
1. GET /api/v1/billing/usage/:workspace_id — 单 workspace 用量
2. GET /api/v1/billing/usage — 所有 workspace 用量（管理视图）
3. GET /api/v1/billing/events — Billing events 查询
4. 过滤参数（org_id, workspace_id, run_id, event_type, limit）
"""

import json
import pytest
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch


# ─────────────────────────────────────────────────────────────────────────────
# Fixtures
# ─────────────────────────────────────────────────────────────────────────────

@pytest.fixture
def mock_quota():
    """Mock QuotaUsageConsumer"""
    quota = MagicMock()
    quota.get_usage.side_effect = lambda ws_id: {
        "workspace_id": ws_id,
        "org_id": "org-test",
        "run_count": 42,
        "token_usage": 150000,
        "cost_total": 3.14,
        "storage_bytes": 1024,
        "last_updated": "2026-07-11T10:00:00+00:00",
    }
    quota.list_all.return_value = [
        {
            "workspace_id": "ws-1",
            "org_id": "org-a",
            "run_count": 10,
            "token_usage": 50000,
            "cost_total": 1.50,
            "storage_bytes": 512,
            "last_updated": "2026-07-11T09:00:00+00:00",
        },
        {
            "workspace_id": "ws-2",
            "org_id": "org-b",
            "run_count": 5,
            "token_usage": 20000,
            "cost_total": 0.75,
            "storage_bytes": 256,
            "last_updated": "2026-07-11T08:00:00+00:00",
        },
        {
            "workspace_id": "ws-3",
            "org_id": "org-a",
            "run_count": 0,
            "token_usage": 0,
            "cost_total": 0.0,
            "storage_bytes": 0,
            "last_updated": "",
        },
    ]
    return quota


@pytest.fixture
def sample_billing_events():
    """Sample billing events list"""
    return [
        {
            "version": 1,
            "event": "billing.usage_recorded",
            "run_id": "run-001",
            "request_id": "req-001",
            "org_id": "org-a",
            "workspace_id": "ws-1",
            "timestamp": "2026-07-11T10:00:00+00:00",
            "usage": {
                "total_tokens": 5000,
                "agent_runs": 3,
                "module": "module-a",
                "capability": "browser",
            },
        },
        {
            "version": 1,
            "event": "billing.cost_recorded",
            "run_id": "run-001",
            "request_id": "req-001",
            "org_id": "org-a",
            "workspace_id": "ws-1",
            "timestamp": "2026-07-11T10:00:01+00:00",
            "cost": {
                "amount": 0.15,
                "currency": "USD",
                "tokens": 5000,
            },
        },
        {
            "version": 1,
            "event": "billing.usage_recorded",
            "run_id": "run-002",
            "request_id": "req-002",
            "org_id": "org-b",
            "workspace_id": "ws-2",
            "timestamp": "2026-07-11T11:00:00+00:00",
            "usage": {
                "total_tokens": 2000,
                "agent_runs": 1,
                "module": "module-b",
                "capability": "browser",
            },
        },
    ]


@pytest.fixture
def mock_billing_hook(sample_billing_events):
    """Mock BillingHookConsumer"""
    hook = MagicMock()
    hook.query.return_value = sample_billing_events
    return hook


@pytest.fixture
def test_client(mock_quota, mock_billing_hook):
    """FastAPI TestClient with mocked backend"""
    from fastapi import FastAPI
    from fastapi.testclient import TestClient
    from aitest.server.api.billing_v1 import billing_router

    app = FastAPI()
    app.include_router(billing_router)

    client = TestClient(app)

    # 注入 mock
    with patch("aitest.server.api.billing_v1.get_quota_usage", return_value=mock_quota), \
         patch("aitest.server.api.billing_v1.get_billing_hook", return_value=mock_billing_hook):
        yield client


# ─────────────────────────────────────────────────────────────────────────────
# Test 1: GET /api/v1/billing/usage/:workspace_id
# ─────────────────────────────────────────────────────────────────────────────

def test_get_workspace_usage(mock_quota, mock_billing_hook):
    """GET /usage/:workspace_id 应返回该 workspace 的用量"""
    from fastapi import FastAPI
    from fastapi.testclient import TestClient
    from aitest.server.api.billing_v1 import billing_router

    app = FastAPI()
    app.include_router(billing_router)
    client = TestClient(app)

    with patch("aitest.server.api.billing_v1.get_quota_usage", return_value=mock_quota):
        resp = client.get("/api/v1/billing/usage/ws-test")

    assert resp.status_code == 200
    data = resp.json()
    assert data["workspace_id"] == "ws-test"
    assert data["run_count"] == 42
    assert data["token_usage"] == 150000
    assert data["cost_total"] == pytest.approx(3.14)


def test_get_workspace_usage_returns_empty_for_unknown(mock_quota):
    """未知 workspace 应返回全零的用量（不是 404）"""
    from fastapi import FastAPI
    from fastapi.testclient import TestClient
    from aitest.server.api.billing_v1 import billing_router

    # 覆盖：未知 workspace 返回空用量
    mock_quota.get_usage.side_effect = lambda ws_id: {
        "workspace_id": ws_id,
        "org_id": "",
        "run_count": 0,
        "token_usage": 0,
        "cost_total": 0.0,
        "storage_bytes": 0,
        "last_updated": "",
    }

    app = FastAPI()
    app.include_router(billing_router)
    client = TestClient(app)

    with patch("aitest.server.api.billing_v1.get_quota_usage", return_value=mock_quota):
        resp = client.get("/api/v1/billing/usage/nonexistent-ws")

    assert resp.status_code == 200
    data = resp.json()
    assert data["run_count"] == 0
    assert data["cost_total"] == 0.0


# ─────────────────────────────────────────────────────────────────────────────
# Test 2: GET /api/v1/billing/usage （列表视图）
# ─────────────────────────────────────────────────────────────────────────────

def test_list_all_usage(mock_quota):
    """GET /usage 应返回所有 workspace 的用量"""
    from fastapi import FastAPI
    from fastapi.testclient import TestClient
    from aitest.server.api.billing_v1 import billing_router

    app = FastAPI()
    app.include_router(billing_router)
    client = TestClient(app)

    with patch("aitest.server.api.billing_v1.get_quota_usage", return_value=mock_quota):
        resp = client.get("/api/v1/billing/usage")

    assert resp.status_code == 200
    data = resp.json()
    assert data["total"] == 3
    assert len(data["workspaces"]) == 3


def test_list_usage_filter_by_org(mock_quota):
    """GET /usage?org_id=org-a 应只返回该 org 的 workspace"""
    from fastapi import FastAPI
    from fastapi.testclient import TestClient
    from aitest.server.api.billing_v1 import billing_router

    app = FastAPI()
    app.include_router(billing_router)
    client = TestClient(app)

    with patch("aitest.server.api.billing_v1.get_quota_usage", return_value=mock_quota):
        resp = client.get("/api/v1/billing/usage?org_id=org-a")

    assert resp.status_code == 200
    data = resp.json()
    assert data["total"] == 2  # ws-1 和 ws-3 都属于 org-a
    for ws in data["workspaces"]:
        assert ws["org_id"] == "org-a"


def test_list_usage_filter_by_min_run_count(mock_quota):
    """GET /usage?min_run_count=1 应排除 run_count=0 的 workspace"""
    from fastapi import FastAPI
    from fastapi.testclient import TestClient
    from aitest.server.api.billing_v1 import billing_router

    app = FastAPI()
    app.include_router(billing_router)
    client = TestClient(app)

    with patch("aitest.server.api.billing_v1.get_quota_usage", return_value=mock_quota):
        resp = client.get("/api/v1/billing/usage?min_run_count=1")

    assert resp.status_code == 200
    data = resp.json()
    # ws-3 有 run_count=0，应被过滤掉
    assert data["total"] == 2
    ws_ids = [w["workspace_id"] for w in data["workspaces"]]
    assert "ws-3" not in ws_ids


# ─────────────────────────────────────────────────────────────────────────────
# Test 3: GET /api/v1/billing/events
# ─────────────────────────────────────────────────────────────────────────────

def test_list_billing_events_all(mock_billing_hook):
    """GET /events 应返回所有 billing events"""
    from fastapi import FastAPI
    from fastapi.testclient import TestClient
    from aitest.server.api.billing_v1 import billing_router

    app = FastAPI()
    app.include_router(billing_router)
    client = TestClient(app)

    with patch("aitest.server.api.billing_v1.get_billing_hook", return_value=mock_billing_hook):
        resp = client.get("/api/v1/billing/events")

    assert resp.status_code == 200
    data = resp.json()
    assert data["total"] == 3
    assert len(data["events"]) == 3


def test_list_billing_events_filter_by_run_id(mock_billing_hook):
    """GET /events?run_id=run-001 应只返回该 run 的 events"""
    from fastapi import FastAPI
    from fastapi.testclient import TestClient
    from aitest.server.api.billing_v1 import billing_router

    app = FastAPI()
    app.include_router(billing_router)
    client = TestClient(app)

    with patch("aitest.server.api.billing_v1.get_billing_hook", return_value=mock_billing_hook):
        resp = client.get("/api/v1/billing/events?run_id=run-001")

    assert resp.status_code == 200
    data = resp.json()
    assert data["total"] == 2  # run-001 有 usage_recorded + cost_recorded
    for event in data["events"]:
        assert event["run_id"] == "run-001"


def test_list_billing_events_filter_by_workspace(mock_billing_hook):
    """GET /events?workspace_id=ws-2 应只返回该 workspace 的 events"""
    from fastapi import FastAPI
    from fastapi.testclient import TestClient
    from aitest.server.api.billing_v1 import billing_router

    app = FastAPI()
    app.include_router(billing_router)
    client = TestClient(app)

    with patch("aitest.server.api.billing_v1.get_billing_hook", return_value=mock_billing_hook):
        resp = client.get("/api/v1/billing/events?workspace_id=ws-2")

    assert resp.status_code == 200
    data = resp.json()
    assert data["total"] == 1
    assert data["events"][0]["workspace_id"] == "ws-2"


def test_list_billing_events_filter_by_event_type(mock_billing_hook):
    """GET /events?event_type=billing.cost_recorded 应只返回 cost 事件"""
    from fastapi import FastAPI
    from fastapi.testclient import TestClient
    from aitest.server.api.billing_v1 import billing_router

    app = FastAPI()
    app.include_router(billing_router)
    client = TestClient(app)

    with patch("aitest.server.api.billing_v1.get_billing_hook", return_value=mock_billing_hook):
        resp = client.get("/api/v1/billing/events?event_type=billing.cost_recorded")

    assert resp.status_code == 200
    data = resp.json()
    assert data["total"] == 1
    assert data["events"][0]["event"] == "billing.cost_recorded"
    assert data["events"][0]["cost"] is not None
    assert data["events"][0]["usage"] is None


def test_list_billing_events_usage_event_structure(mock_billing_hook):
    """usage_recorded 事件应包含 usage 字段"""
    from fastapi import FastAPI
    from fastapi.testclient import TestClient
    from aitest.server.api.billing_v1 import billing_router

    app = FastAPI()
    app.include_router(billing_router)
    client = TestClient(app)

    with patch("aitest.server.api.billing_v1.get_billing_hook", return_value=mock_billing_hook):
        resp = client.get("/api/v1/billing/events?event_type=billing.usage_recorded")

    assert resp.status_code == 200
    data = resp.json()
    assert data["total"] == 2
    for event in data["events"]:
        assert event["usage"] is not None
        assert "total_tokens" in event["usage"]
        assert "agent_runs" in event["usage"]


def test_list_billing_events_limit(mock_billing_hook):
    """GET /events?limit=1 应最多返回 1 条"""
    from fastapi import FastAPI
    from fastapi.testclient import TestClient
    from aitest.server.api.billing_v1 import billing_router

    app = FastAPI()
    app.include_router(billing_router)
    client = TestClient(app)

    with patch("aitest.server.api.billing_v1.get_billing_hook", return_value=mock_billing_hook):
        resp = client.get("/api/v1/billing/events?limit=1")

    assert resp.status_code == 200
    data = resp.json()
    assert len(data["events"]) == 1
    assert data["total"] == 1


def test_list_billing_events_empty(mock_billing_hook):
    """没有 billing events 时应返回空列表"""
    from fastapi import FastAPI
    from fastapi.testclient import TestClient
    from aitest.server.api.billing_v1 import billing_router

    mock_billing_hook.query.return_value = []

    app = FastAPI()
    app.include_router(billing_router)
    client = TestClient(app)

    with patch("aitest.server.api.billing_v1.get_billing_hook", return_value=mock_billing_hook):
        resp = client.get("/api/v1/billing/events")

    assert resp.status_code == 200
    data = resp.json()
    assert data["total"] == 0
    assert data["events"] == []


# ─────────────────────────────────────────────────────────────────────────────
# Test 4: BillingHookConsumer.query() 集成（真实文件读写）
# ─────────────────────────────────────────────────────────────────────────────

def test_billing_hook_query_reads_jsonl():
    """BillingHookConsumer.query() 应从 billing.jsonl 读取事件"""
    with tempfile.TemporaryDirectory() as tmpdir:
        billing_dir = Path(tmpdir)

        # 写入测试数据
        billing_file = billing_dir / "billing.jsonl"
        records = [
            {"version": 1, "event": "billing.usage_recorded", "run_id": "r1", "request_id": "q1",
             "org_id": "org-x", "workspace_id": "ws-x", "timestamp": "2026-07-11T00:00:00+00:00",
             "usage": {"total_tokens": 100}},
            {"version": 1, "event": "billing.cost_recorded", "run_id": "r1", "request_id": "q1",
             "org_id": "org-x", "workspace_id": "ws-x", "timestamp": "2026-07-11T00:00:01+00:00",
             "cost": {"amount": 0.01, "currency": "USD", "tokens": 100}},
        ]
        with open(billing_file, "w", encoding="utf-8") as f:
            for r in records:
                f.write(json.dumps(r) + "\n")

        from aitest.platform.hooks.billing_hook import BillingHookConsumer
        hook = BillingHookConsumer.__new__(BillingHookConsumer)
        hook._dir = billing_dir
        hook._lock = __import__("threading").Lock()

        result = hook.query()
        assert len(result) == 2
        assert result[0]["event"] == "billing.usage_recorded"
        assert result[1]["event"] == "billing.cost_recorded"


def test_billing_hook_query_filters_by_org():
    """BillingHookConsumer.query(org_id=...) 应过滤 org"""
    with tempfile.TemporaryDirectory() as tmpdir:
        billing_dir = Path(tmpdir)
        billing_file = billing_dir / "billing.jsonl"

        records = [
            {"version": 1, "event": "billing.usage_recorded", "run_id": "r1", "request_id": "q1",
             "org_id": "org-a", "workspace_id": "ws-1", "timestamp": "2026-07-11T00:00:00+00:00"},
            {"version": 1, "event": "billing.usage_recorded", "run_id": "r2", "request_id": "q2",
             "org_id": "org-b", "workspace_id": "ws-2", "timestamp": "2026-07-11T00:00:01+00:00"},
        ]
        with open(billing_file, "w", encoding="utf-8") as f:
            for r in records:
                f.write(json.dumps(r) + "\n")

        from aitest.platform.hooks.billing_hook import BillingHookConsumer
        hook = BillingHookConsumer.__new__(BillingHookConsumer)
        hook._dir = billing_dir
        hook._lock = __import__("threading").Lock()

        result = hook.query(org_id="org-a")
        assert len(result) == 1
        assert result[0]["org_id"] == "org-a"

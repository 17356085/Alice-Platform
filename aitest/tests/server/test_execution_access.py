from types import SimpleNamespace

import pytest
from fastapi import HTTPException

from aitest.platform.run import Run
from aitest.platform.workspace import WorkspaceManager
from aitest.server.api.execution import (
    StartExecutionRequest,
    get_run_debug,
    get_run,
    query_audit,
    register_webhook,
    start_execution,
)


class _FakeService:
    def __init__(self):
        self.calls = []

    def execute(self, **kwargs):
        self.calls.append(kwargs)
        return SimpleNamespace(
            to_dict=lambda: {
                "request_id": "req-1",
                "run_id": "run-1",
                "status": "completed",
            }
        )


class _FakeStore:
    def __init__(self, run):
        self._run = run

    def load_run(self, run_id):
        return self._run if self._run and self._run.run_id == run_id else None

    def list_events(self, run_id=None, limit=100):
        return []


class _FakeAuditLogger:
    def __init__(self):
        self.last_kwargs = None

    def query(self, **kwargs):
        self.last_kwargs = kwargs
        return [{"event_id": "evt-1"}]

    def count(self, **kwargs):
        return 1


class _FakeWebhookRegistry:
    def register(self, **kwargs):
        return SimpleNamespace(**kwargs, id="wh-1")


def _request(*, user_id="alice", org_id="org-1", scopes=None, app_state=None):
    return SimpleNamespace(
        state=SimpleNamespace(
            user_id=user_id,
            org_id=org_id,
            scopes=scopes or ["read", "execute"],
        ),
        headers={},
        app=SimpleNamespace(state=SimpleNamespace(**(app_state or {}))),
    )


@pytest.mark.asyncio
async def test_start_execution_rejects_cross_org_access(monkeypatch, tmp_path):
    wm = WorkspaceManager(data_dir=tmp_path / "workspaces")
    wm.create("org-1", "ws-1", name="WS")

    monkeypatch.setattr("aitest.platform.workspace.get_ws_manager", lambda: wm)

    request = _request(org_id="org-2", app_state={"execution_service": _FakeService()})

    with pytest.raises(HTTPException) as exc:
        await start_execution(
            "ws-1",
            StartExecutionRequest(module="equipment"),
            request,
        )

    assert exc.value.status_code == 403


@pytest.mark.asyncio
async def test_start_execution_allows_workspace_member(monkeypatch, tmp_path):
    wm = WorkspaceManager(data_dir=tmp_path / "workspaces")
    wm.create("org-1", "ws-1", name="WS")
    wm.add_member("org-1", "ws-1", "alice", "member")

    monkeypatch.setattr("aitest.platform.workspace.get_ws_manager", lambda: wm)

    service = _FakeService()
    request = _request(org_id="org-1", app_state={"execution_service": service})
    result = await start_execution(
        "ws-1",
        StartExecutionRequest(module="equipment"),
        request,
    )

    assert result["run_id"] == "run-1"
    assert len(service.calls) == 1
    assert service.calls[0]["ctx"].workspace_id == "ws-1"


@pytest.mark.asyncio
async def test_get_run_rejects_non_member(monkeypatch, tmp_path):
    wm = WorkspaceManager(data_dir=tmp_path / "workspaces")
    wm.create("org-1", "ws-1", name="WS")
    wm.add_member("org-1", "ws-1", "alice", "member")

    monkeypatch.setattr("aitest.platform.workspace.get_ws_manager", lambda: wm)

    run = Run(
        run_id="run-1",
        request_id="req-1",
        workspace_id="ws-1",
        org_id="org-1",
        triggered_by="alice",
    )
    request = _request(user_id="bob", org_id="org-1", app_state={"run_store": _FakeStore(run)})

    with pytest.raises(HTTPException) as exc:
        await get_run("run-1", request)

    assert exc.value.status_code == 403


@pytest.mark.asyncio
async def test_get_run_debug_rejects_non_member(monkeypatch, tmp_path):
    wm = WorkspaceManager(data_dir=tmp_path / "workspaces")
    wm.create("org-1", "ws-1", name="WS")
    wm.add_member("org-1", "ws-1", "alice", "member")

    monkeypatch.setattr("aitest.platform.workspace.get_ws_manager", lambda: wm)

    run = Run(
        run_id="run-1",
        request_id="req-1",
        workspace_id="ws-1",
        org_id="org-1",
        triggered_by="alice",
    )
    request = _request(user_id="bob", org_id="org-1", app_state={"run_store": _FakeStore(run)})

    with pytest.raises(HTTPException) as exc:
        await get_run_debug("run-1", request)

    assert exc.value.status_code == 403


@pytest.mark.asyncio
async def test_query_audit_defaults_to_request_org(monkeypatch):
    logger = _FakeAuditLogger()
    request = _request(org_id="org-1", app_state={"audit_logger": logger})

    result = await query_audit(request)

    assert result["total"] == 1
    assert logger.last_kwargs["org_id"] == "org-1"


@pytest.mark.asyncio
async def test_register_webhook_rejects_cross_org_access(monkeypatch, tmp_path):
    wm = WorkspaceManager(data_dir=tmp_path / "workspaces")
    wm.create("org-1", "ws-1", name="WS")
    wm.add_member("org-1", "ws-1", "alice", "member")

    monkeypatch.setattr("aitest.platform.workspace.get_ws_manager", lambda: wm)

    request = _request(
        user_id="alice",
        org_id="org-2",
        app_state={"webhook_registry": _FakeWebhookRegistry()},
    )

    with pytest.raises(HTTPException) as exc:
        await register_webhook(
            "ws-1",
            SimpleNamespace(url="https://example.com/hook", events=["run.completed"], secret=""),
            request,
        )

    assert exc.value.status_code == 403

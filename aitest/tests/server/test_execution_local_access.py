from pathlib import Path
from types import SimpleNamespace

import pytest

from aitest.platform.run import Run
from aitest.server.api.execution import _require_request_run_access, download_run_artifact


def test_local_unauthenticated_read_allows_historical_run(monkeypatch):
    monkeypatch.delenv("AITEST_API_KEY", raising=False)
    monkeypatch.setattr("aitest.server.auth._rbac_required", lambda: False)
    request = SimpleNamespace(
        state=SimpleNamespace(user_id=None, org_id="", scopes=[]),
        headers={},
    )
    run = Run(
        run_id="historical",
        request_id="request-1",
        triggered_by="anonymous",
        workspace_id="ws_test",
        org_id="org_test",
    )

    user_id, scopes = _require_request_run_access(request, run, required_scope="read")

    assert user_id == "anonymous"
    assert scopes == []


@pytest.mark.asyncio
async def test_run_artifact_download_resolves_event_path_inside_workstudy(monkeypatch, tmp_path):
    monkeypatch.setattr("aitest.server.auth._rbac_required", lambda: False)
    artifact = tmp_path / "report.md"
    artifact.write_text("# report", encoding="utf-8")
    run = Run(
        run_id="run-artifact",
        request_id="request-1",
        triggered_by="anonymous",
        workspace_id="ws_test",
        org_id="org_test",
    )
    event = SimpleNamespace(
        event_id="evt-artifact",
        event_type="artifact.created",
        data={"artifact_path": "report.md", "mime_type": "text/markdown"},
    )
    store = SimpleNamespace(load_run=lambda _: run, list_events=lambda *_args, **_kwargs: [event])
    monkeypatch.setattr("aitest.platform.paths.get_workstudy", lambda: tmp_path)
    request = SimpleNamespace(
        state=SimpleNamespace(user_id=None, org_id="", scopes=[], run_store=store),
        headers={},
        app=SimpleNamespace(state=SimpleNamespace(run_store=store)),
    )

    response = await download_run_artifact("run-artifact", "evt-artifact", request)

    assert Path(response.path) == artifact.resolve()
    assert response.filename == "report.md"


@pytest.mark.asyncio
async def test_run_artifact_download_rejects_path_traversal(monkeypatch, tmp_path):
    monkeypatch.setattr("aitest.server.auth._rbac_required", lambda: False)
    run = Run(
        run_id="run-artifact",
        request_id="request-1",
        triggered_by="anonymous",
        workspace_id="ws_test",
        org_id="org_test",
    )
    event = SimpleNamespace(
        event_id="evt-artifact",
        event_type="artifact.created",
        data={"artifact_path": "../secret.txt"},
    )
    store = SimpleNamespace(load_run=lambda _: run, list_events=lambda *_args, **_kwargs: [event])
    monkeypatch.setattr("aitest.platform.paths.get_workstudy", lambda: tmp_path)
    request = SimpleNamespace(
        state=SimpleNamespace(user_id=None, org_id="", scopes=[], run_store=store),
        headers={},
        app=SimpleNamespace(state=SimpleNamespace(run_store=store)),
    )

    with pytest.raises(Exception) as exc:
        await download_run_artifact("run-artifact", "evt-artifact", request)

    assert getattr(exc.value, "status_code", None) == 404

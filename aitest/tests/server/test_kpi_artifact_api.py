import pytest

from aitest.server.api import kpi


@pytest.mark.asyncio
async def test_artifact_download_requires_a_name():
    result = await kpi.artifact_download("project-1")

    assert result == {"error": "name parameter required"}


@pytest.mark.asyncio
async def test_artifact_download_returns_attachment_with_mime_type(monkeypatch):
    monkeypatch.setattr(kpi, "get_project_dir", lambda project_id: f"/tmp/{project_id}", raising=False)
    monkeypatch.setattr(
        kpi,
        "_read_artifact_file",
        lambda project_dir, module, page, name: b'{"ok": true}',
    )

    response = await kpi.artifact_download(
        "project-1", module="auth", page="login", name="result.json"
    )

    assert response.media_type == "application/json"
    assert response.body == b'{"ok": true}'
    assert response.headers["content-disposition"] == 'attachment; filename="result.json"'


@pytest.mark.asyncio
async def test_artifact_download_returns_frontend_safe_error_for_missing_file(monkeypatch):
    monkeypatch.setattr(kpi, "get_project_dir", lambda project_id: "/tmp/project-1", raising=False)
    monkeypatch.setattr(kpi, "_read_artifact_file", lambda *args: None)

    result = await kpi.artifact_download("project-1", name="missing.json")

    assert result == {"error": "Artifact 'missing.json' not found"}

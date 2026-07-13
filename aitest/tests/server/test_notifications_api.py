from types import SimpleNamespace

import pytest

from aitest.server.api.notifications_v1 import list_notifications


@pytest.mark.asyncio
async def test_notifications_aggregate_open_bugs_and_failed_runs(monkeypatch):
    monkeypatch.setattr(
        "aitest.testing.bug_history.list_bugs",
        lambda **kwargs: [{"id": "BUG-1", "module": "auth", "severity": "high", "error_type": "missing assertion", "created_at": 10}],
    )
    monkeypatch.setattr(
        "aitest.platform.run_store.get_run_store",
        lambda: SimpleNamespace(list_runs=lambda **kwargs: [SimpleNamespace(
            run_id="run-1", status="failed", module="auth", error_message="provider failed",
            completed_at="2026-07-13T10:00:00Z", created_at="",
        )]),
    )

    result = await list_notifications(limit=10)

    assert result["total"] == 2
    assert result["unread"] == 2
    assert {item["kind"] for item in result["notifications"]} == {"bug", "run"}


@pytest.mark.asyncio
async def test_notifications_tolerate_optional_sources(monkeypatch):
    monkeypatch.setattr("aitest.testing.bug_history.list_bugs", lambda **kwargs: (_ for _ in ()).throw(RuntimeError("no bugs table")))
    monkeypatch.setattr("aitest.platform.run_store.get_run_store", lambda: (_ for _ in ()).throw(RuntimeError("no run store")))

    assert await list_notifications() == {"notifications": [], "total": 0, "unread": 0}


@pytest.mark.asyncio
async def test_notification_read_state_persists(monkeypatch, tmp_path):
    import aitest.infra.db as database

    monkeypatch.setenv("AITEST_SQLALCHEMY_URL", f"sqlite:///{(tmp_path / 'notifications.db').as_posix()}")
    monkeypatch.setattr(database, "_engine", None)
    monkeypatch.setattr(database, "_session_factory", None)
    monkeypatch.delenv("AITEST_NOTIFICATION_STATE_FILE", raising=False)
    monkeypatch.setattr(
        "aitest.testing.bug_history.list_bugs",
        lambda **kwargs: [{"id": "BUG-READ", "module": "auth", "severity": "low", "error_type": "review", "created_at": 10}],
    )
    monkeypatch.setattr(
        "aitest.platform.run_store.get_run_store",
        lambda: (_ for _ in ()).throw(RuntimeError("no run store")),
    )

    before = await list_notifications(scope="project-a")
    assert before["unread"] == 1

    from aitest.server.api.notifications_v1 import mark_notification_read

    marked = await mark_notification_read("bug:BUG-READ", scope="project-a")
    assert marked["status"] == "read"

    after = await list_notifications(scope="project-a")
    assert after["notifications"][0]["read"] is True
    assert after["unread"] == 0
    assert (await list_notifications(scope="project-a", unread_only=True))["notifications"] == []

    from aitest.infra.db import get_db_session
    from aitest.infra.models import NotificationReadModel

    with get_db_session() as session:
        assert session.get(NotificationReadModel, ("project-a", "bug:BUG-READ")) is not None


@pytest.mark.asyncio
async def test_notification_read_state_imports_legacy_json(monkeypatch, tmp_path):
    import json
    import aitest.infra.db as database

    monkeypatch.setenv("AITEST_SQLALCHEMY_URL", f"sqlite:///{(tmp_path / 'notifications.db').as_posix()}")
    monkeypatch.setenv("AITEST_NOTIFICATION_STATE_FILE", str(tmp_path / "legacy-state.json"))
    monkeypatch.setattr(database, "_engine", None)
    monkeypatch.setattr(database, "_session_factory", None)
    (tmp_path / "legacy-state.json").write_text(
        json.dumps({"scopes": {"project-a": ["bug:LEGACY"]}}),
        encoding="utf-8",
    )

    from aitest.platform.notification_state import read_ids

    assert read_ids("project-a") == {"bug:LEGACY"}

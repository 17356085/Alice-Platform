"""Database auto-selection tests."""

from types import SimpleNamespace


def test_auto_backend_falls_back_when_postgres_authentication_fails(monkeypatch):
    import aitest.infra.database as database

    class FakeSocket:
        def __enter__(self):
            return self

        def __exit__(self, *_):
            return False

    monkeypatch.setenv("AITEST_DB_BACKEND", "auto")
    monkeypatch.setattr(database.socket, "create_connection", lambda *_args, **_kwargs: FakeSocket())
    monkeypatch.setattr(
        "aitest.infra.database_pg._get_conn",
        lambda: (_ for _ in ()).throw(RuntimeError("authentication failed")),
    )

    assert database._detect_backend() == "sqlite"


def test_explicit_postgres_is_not_silently_changed(monkeypatch):
    import aitest.infra.database as database

    monkeypatch.setenv("AITEST_DB_BACKEND", "postgres")
    assert database._detect_backend() == "postgres"


def test_sqlite_recomputes_removed_cached_path(tmp_path, monkeypatch):
    import aitest.infra.database_sqlite as database_sqlite

    stale_path = tmp_path / "removed" / "aitest.db"
    monkeypatch.setattr(database_sqlite, "_DB_PATH", stale_path)

    resolved = database_sqlite._get_db_path()

    assert resolved != stale_path
    assert resolved.parent.exists()

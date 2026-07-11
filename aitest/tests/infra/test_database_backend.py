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

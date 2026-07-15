from aitest.infra.db import _pool_options


def test_sqlalchemy_pool_defaults_are_explicit_for_postgres(monkeypatch):
    monkeypatch.delenv("AITEST_DB_POOL_SIZE", raising=False)
    monkeypatch.delenv("AITEST_DB_MAX_OVERFLOW", raising=False)
    options = _pool_options("postgresql+psycopg://user:password@host/db")
    assert options == {
        "pool_pre_ping": True,
        "pool_size": 5,
        "max_overflow": 10,
        "pool_timeout": 30,
        "pool_recycle": 1800,
    }


def test_sqlalchemy_pool_settings_are_env_configurable(monkeypatch):
    monkeypatch.setenv("AITEST_DB_POOL_SIZE", "8")
    monkeypatch.setenv("AITEST_DB_MAX_OVERFLOW", "2")
    monkeypatch.setenv("AITEST_DB_POOL_TIMEOUT", "12")
    monkeypatch.setenv("AITEST_DB_POOL_RECYCLE", "600")
    options = _pool_options("postgresql+psycopg://user:password@host/db")
    assert options["pool_size"] == 8
    assert options["max_overflow"] == 2
    assert options["pool_timeout"] == 12
    assert options["pool_recycle"] == 600


def test_sqlite_does_not_receive_postgres_pool_options():
    assert _pool_options("sqlite:///tmp/test.db") == {}

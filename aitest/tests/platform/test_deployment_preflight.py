"""Deployment preflight and readiness checks."""


def test_production_preflight_blocks_sqlite_and_missing_auth(monkeypatch, tmp_path):
    import aitest.infra.database as database
    import aitest.platform.deployment_preflight as preflight

    monkeypatch.setenv("AITEST_PRODUCTION", "1")
    monkeypatch.delenv("AITEST_API_KEY", raising=False)
    monkeypatch.setattr(database, "get_backend", lambda: "sqlite")
    monkeypatch.setattr(preflight, "get_workstudy", lambda: tmp_path)

    result = preflight.run_deployment_preflight()
    assert result.status == "blocked"
    assert result.checks["database_backend"]["status"] == "error"
    assert result.checks["api_auth"]["status"] == "error"


def test_local_preflight_allows_sqlite(monkeypatch, tmp_path):
    import aitest.infra.database as database
    import aitest.platform.deployment_preflight as preflight

    monkeypatch.delenv("AITEST_PRODUCTION", raising=False)
    monkeypatch.setattr(database, "get_backend", lambda: "sqlite")
    monkeypatch.setattr(preflight, "get_workstudy", lambda: tmp_path)

    result = preflight.run_deployment_preflight(production=False)
    assert result.status == "ready"
    assert result.checks["database_backend"]["status"] == "ok"

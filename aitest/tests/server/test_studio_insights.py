"""Contract tests for the read-only Studio insight adapters."""

from fastapi import FastAPI
from fastapi.testclient import TestClient


def test_memory_stats_adapts_existing_store(monkeypatch):
    import aitest.platform.testing_memory_store as memory_store
    from aitest.server.api.insights import insights_router

    monkeypatch.setattr(memory_store, "TestingMemoryStore", lambda: type(
        "Store", (), {"available": lambda self: True, "stats": lambda self: {"total": 4}}
    )())
    app = FastAPI(); app.include_router(insights_router)

    response = TestClient(app).get("/api/v1/memory/stats")

    assert response.status_code == 200
    assert response.json() == {"available": True, "collections": {"total": 4}}


def test_knowledge_search_is_empty_without_query(monkeypatch):
    from aitest.server.api.insights import insights_router

    app = FastAPI(); app.include_router(insights_router)
    response = TestClient(app).get("/api/v1/knowledge/search")

    assert response.status_code == 200
    assert response.json()["results"] == []

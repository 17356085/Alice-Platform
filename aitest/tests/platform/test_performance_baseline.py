from aitest.platform.performance_baseline import PerformanceBaselineService


def test_performance_baseline_detects_hotspots(monkeypatch):
    svc = PerformanceBaselineService()

    monkeypatch.setattr(
        svc,
        "_capture_runtime",
        lambda: {
            "agent_latency_p95": {"automation-agent": {"p95": 45, "total": 8, "avg": 12}},
            "workflow": {"equipment": {"total": 10, "success": 6, "failed": 4, "rate": 0.6}},
        },
    )
    monkeypatch.setattr(
        svc,
        "_capture_provider",
        lambda run_id: {"total_latency_ms": 40000, "models_seen": ["claude-sonnet-4-6"]},
    )
    monkeypatch.setattr(
        svc,
        "_capture_knowledge",
        lambda namespace: {"available": True, "collections": {"known_issues": 0, "page_context": 12}},
    )
    monkeypatch.setattr(
        svc,
        "_capture_memory",
        lambda: {"available": True, "collections": {"total": 3, "ui_patterns": 1}},
    )
    monkeypatch.setattr(
        svc,
        "_capture_worker",
        lambda: {"worker_id": "worker-1", "retried": 2, "throttled": 1},
    )
    monkeypatch.setattr(svc, "_persist", lambda snapshot: None)

    snapshot = svc.capture(namespace="web-automation", run_id="run-1", persist=True)

    hotspots = snapshot.to_dict()["hotspots"]
    categories = {item["category"] for item in hotspots}
    names = {item["name"] for item in hotspots}

    assert "runtime" in categories
    assert "provider" in categories
    assert "knowledge" in categories
    assert "memory" in categories
    assert "automation-agent" in names
    assert "equipment" in names


def test_performance_baseline_snapshot_shape(monkeypatch):
    svc = PerformanceBaselineService()
    monkeypatch.setattr(svc, "_capture_runtime", lambda: {"agent_latency_p95": {}, "workflow": {}})
    monkeypatch.setattr(svc, "_capture_provider", lambda run_id: {"total_events": 0, "models_seen": []})
    monkeypatch.setattr(svc, "_capture_knowledge", lambda namespace: {"available": True, "collections": {}})
    monkeypatch.setattr(svc, "_capture_memory", lambda: {"available": True, "collections": {"total": 0}})
    monkeypatch.setattr(svc, "_capture_worker", lambda: {"worker_id": "worker-1"})
    monkeypatch.setattr(svc, "_persist", lambda snapshot: None)

    snapshot = svc.capture()
    data = snapshot.to_dict()

    assert "ts" in data
    assert "runtime" in data
    assert "provider" in data
    assert "knowledge" in data
    assert "memory" in data
    assert "worker" in data
    assert "hotspots" in data

from aitest.platform import execution_service


def test_static_execution_service_is_process_local(monkeypatch):
    monkeypatch.setattr(execution_service, "_STATIC_SERVICE", None)
    first = execution_service.get_execution_service_static()
    second = execution_service.get_execution_service_static()
    assert first is second
    assert type(first).__name__ == "ExecutionService"

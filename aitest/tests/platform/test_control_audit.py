"""Control-plane audit record tests."""


def test_record_action_writes_structured_control_event(monkeypatch):
    import aitest.platform.audit_log as audit_log

    calls = []
    monkeypatch.setattr(audit_log, "safe_exec", lambda sql, params: calls.append((sql, params)))
    audit_log.AuditLogger().record_action(
        action="http.put", actor="user-1", org_id="org-a",
        resource_type="workspace", resource_id="ws-1",
        request_id="req-1", metadata={"status_code": 200},
    )
    assert len(calls) == 1
    params = calls[0][1]
    assert params[1] == "control.action"
    assert params[2:5] == ["req-1", "org-a", "user-1"]

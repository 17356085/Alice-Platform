from aitest.platform.audit_log import AuditLogger
from aitest.platform.event_query import EventQueryService
from aitest.platform.replay import ReplayRecorder, StepType
from aitest.platform.run_event import EventType, make_event
from aitest.platform.run_store import RunStore


def test_event_query_includes_replay_and_audit(monkeypatch, tmp_path):
    monkeypatch.setenv("AITEST_GOVERNANCE_POLICY_VERSION", "2026.07")
    monkeypatch.setenv("AITEST_DB_BACKEND", "sqlite")
    import aitest.infra.database as database
    import aitest.infra.database_sqlite as database_sqlite

    database._backend = None
    database_sqlite._DB_PATH = tmp_path / "event_query_phase3.db"

    store = RunStore()
    audit = AuditLogger()

    recorder = ReplayRecorder(run_id="run-evt-1", module="equipment", page="alarm", agent="automation-agent")
    step = recorder.begin_step(
        StepType.SKILL,
        "automation/demo",
        input_data={"module": "equipment"},
    )
    recorder.record_llm_call(
        step.id,
        model="mock",
        provider="mock",
        messages=[{"role": "user", "content": "run"}],
        response="done",
        usage={"input": 1, "output": 2},
    )
    recorder.end_step(
        step.id,
        output_data={"finish_reason": "stop"},
        status="success",
    )
    recorder.finish()

    event = make_event(
        EventType.RUN_COMPLETED,
        run_id="run-evt-1",
        request_id="req-evt-1",
        module="equipment",
        agent="automation-agent",
        workspace_id="ws-1",
        org_id="org-1",
        replay_session_id=recorder.session_id,
        policy_version="2026.07",
        governance_version="2026.07",
        config_version="2026.07",
    )
    store.save_event(event)
    audit._on_event(event)

    result = EventQueryService(store=store, audit=audit).query_by_run("run-evt-1")

    assert result["counts"]["run_events"] == 1
    assert result["counts"]["audit_entries"] == 1
    assert result["counts"]["replay_sessions"] == 1
    assert result["counts"]["replay_steps"] == 1
    assert result["counts"]["llm_traces"] == 1
    assert result["versioning"]["policy_version"] == "2026.07"
    assert result["replay_sessions"][0]["id"] == recorder.session_id
    assert result["replay_details"][0]["audit_entries"][0]["data"]["replay_session_id"] == recorder.session_id


def test_event_query_includes_trace_events(monkeypatch, tmp_path):
    monkeypatch.setenv("AITEST_GOVERNANCE_POLICY_VERSION", "2026.07")
    monkeypatch.setenv("AITEST_DB_BACKEND", "sqlite")
    import aitest.infra.database as database
    import aitest.infra.database_sqlite as database_sqlite

    database._backend = None
    database_sqlite._DB_PATH = tmp_path / "event_query_trace.db"

    store = RunStore()
    audit = AuditLogger()

    monkeypatch.setattr(
        "aitest.infra.trace.query_trace_events",
        lambda run_id=None, limit=100: [{"event_id": "trace-1", "run_id": run_id, "event_type": "llm_call"}],
    )
    monkeypatch.setattr(
        "aitest.infra.trace.get_trace_summary",
        lambda run_id=None: {"total_events": 1, "models_seen": ["mock"]},
    )

    event = make_event(
        EventType.RUN_COMPLETED,
        run_id="run-trace-1",
        request_id="req-trace-1",
        module="equipment",
        agent="automation-agent",
        workspace_id="ws-1",
        org_id="org-1",
        policy_version="2026.07",
        governance_version="2026.07",
        config_version="2026.07",
    )
    store.save_event(event)
    audit._on_event(event)

    result = EventQueryService(store=store, audit=audit).query_by_run("run-trace-1")

    assert result["counts"]["trace_events"] == 1
    assert result["trace_summary"]["total_events"] == 1
    assert result["trace_events"][0]["event_id"] == "trace-1"

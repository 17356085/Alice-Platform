from aitest.platform.replay import ReplayPlayer, ReplayRecorder, StepType
from aitest.platform.audit_log import AuditLogger
from aitest.platform.run_event import EventType, make_event


def test_replay_recorder_and_player_roundtrip(monkeypatch, tmp_path):
    monkeypatch.setenv("AITEST_DB_BACKEND", "sqlite")
    import aitest.infra.database as database
    import aitest.infra.database_sqlite as database_sqlite
    database._backend = None
    database_sqlite._DB_PATH = tmp_path / "replay.db"

    recorder = ReplayRecorder(run_id="run-1", module="equipment", page="alarm", agent="automation-agent")
    step = recorder.begin_step(
        StepType.SKILL,
        "automation/demo",
        input_data={"module": "equipment"},
        metadata={"skill_index": 1},
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
        output_data={"finish_reason": "stop", "tool_results": [{"success": True}]},
        status="success",
    )
    recorder.finish()

    player = ReplayPlayer(recorder.session_id)
    loaded_steps = player.steps()

    assert player.session.run_id == "run-1"
    assert len(loaded_steps) == 1
    assert loaded_steps[0].name == "automation/demo"
    trace = player.get_llm_trace(step.id)
    assert trace is not None
    assert trace.response == "done"


def test_replay_compare_reports_match_and_mismatch(monkeypatch, tmp_path):
    monkeypatch.setenv("AITEST_DB_BACKEND", "sqlite")
    import aitest.infra.database as database
    import aitest.infra.database_sqlite as database_sqlite
    database._backend = None
    database_sqlite._DB_PATH = tmp_path / "replay_compare.db"

    recorder = ReplayRecorder(run_id="run-2", module="equipment")
    step = recorder.begin_step(StepType.SKILL, "automation/demo")
    recorder.end_step(step.id, output_data={"finish_reason": "stop", "count": 1}, status="success")
    recorder.finish()

    player = ReplayPlayer(recorder.session_id)
    comparison = player.compare({
        step.id: {"finish_reason": "stop", "count": 1},
        "other": {"ignored": True},
    })
    assert comparison[step.id]["match"] is True

    mismatch = player.compare({
        step.id: {"finish_reason": "error"},
    })
    assert mismatch[step.id]["match"] is False


def test_replay_player_can_load_related_audit_entries(monkeypatch, tmp_path):
    monkeypatch.setenv("AITEST_DB_BACKEND", "sqlite")
    import aitest.infra.database as database
    import aitest.infra.database_sqlite as database_sqlite
    database._backend = None
    database_sqlite._DB_PATH = tmp_path / "replay_audit.db"

    recorder = ReplayRecorder(run_id="run-3", module="equipment")
    step = recorder.begin_step(StepType.SKILL, "automation/demo")
    recorder.end_step(step.id, output_data={"finish_reason": "stop"}, status="success")
    recorder.finish()

    audit = AuditLogger()
    audit._on_event(make_event(
        EventType.RUN_COMPLETED,
        run_id="run-3",
        module="equipment",
        replay_session_id=recorder.session_id,
    ))

    player = ReplayPlayer(recorder.session_id)
    entries = player.audit_entries(audit)

    assert len(entries) == 1
    assert entries[0]["data"]["replay_session_id"] == recorder.session_id

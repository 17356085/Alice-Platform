"""Platform projections for the shared runtime contract pack."""

from __future__ import annotations

from alice_engine.contracts import ExecutionContext, ExecutionResult
from alice_engine.runtime_contracts import RuntimeArtifactRecord, RuntimeEventEnvelope

from aitest.platform.checkpoint import CheckpointSnapshot
from aitest.platform.replay import ExecutionStep, ReplaySession
from aitest.platform.run_event import EventDataKey as K
from aitest.platform.runtime_contracts import (
    checkpoint_snapshot_to_record,
    replay_session_to_record,
    replay_step_to_record,
    runtime_event_from_payload,
    runtime_event_from_result,
    runtime_event_to_run_event,
)


def _make_context() -> ExecutionContext:
    return ExecutionContext(
        workspace_id="ws-1",
        user_id="alice",
        scopes=["read", "execute"],
        org_id="org-1",
        module="equipment",
        pages=["alarm-config"],
        agent="automation-agent",
        mode="full",
        request_id="req-1",
        run_id="run-1",
    )


def _make_result() -> ExecutionResult:
    return ExecutionResult(
        request_id="req-1",
        run_id="run-1",
        status="completed",
        module="equipment",
        pages=["alarm-config"],
        agent="automation-agent",
        mode="full",
        total_tokens=222,
        total_cost=1.25,
        agent_runs=4,
        artifacts=["artifacts/report.md"],
        duration_ms=321.0,
        completed_phases=["Requirement"],
        failed_phases=[],
        metadata={"policy_version": "p1"},
    )


def test_runtime_event_projection_preserves_platform_event_shape():
    envelope = runtime_event_from_result(
        _make_result(),
        event_type="run.completed",
        context=_make_context(),
        replay_session_id="replay-1",
        checkpoint_thread_id="thread-1",
        artifacts=[RuntimeArtifactRecord(path="artifacts/report.md", kind="report", run_id="run-1")],
        metadata={"policy_version": "p1"},
    )

    event = runtime_event_to_run_event(envelope)

    assert event.event_type == "run.completed"
    assert event.run_id == "run-1"
    assert event.data[K.WORKSPACE_ID] == "ws-1"
    assert event.data[K.TOTAL_TOKENS] == 222
    assert event.data[K.ARTIFACT_TYPE] == "report"
    assert event.data["checkpoint_thread_id"] == "thread-1"


def test_runtime_event_projection_generates_event_id_and_keeps_metadata():
    envelope = runtime_event_from_payload(
        event_type="engine.skill_start",
        run_id="run-2",
        request_id="req-2",
        module="equipment",
        agent="automation-agent",
        metadata={"custom": "value"},
    )

    event = runtime_event_to_run_event(envelope)

    assert event.event_id != ""
    assert event.data["custom"] == "value"
    assert event.data[K.MODULE] == "equipment"
    assert event.data[K.AGENT] == "automation-agent"


def test_checkpoint_and_replay_projection_use_neutral_records():
    snapshot = CheckpointSnapshot(
        thread_id="thread-1",
        available=True,
        values={"phase": "Automation"},
        raw={"checkpoint_id": "cp-1", "channel_values": {"phase": "Automation"}},
        loaded_at="2026-07-08T00:00:00+00:00",
    )
    session = ReplaySession(
        id="replay-1",
        run_id="run-1",
        module="equipment",
        page="alarm-config",
        agent="automation-agent",
        mode="mock",
        step_count=1,
        total_duration_ms=12.5,
        status="completed",
        created_at="2026-07-08T00:00:00+00:00",
    )
    step = ExecutionStep(
        id="step-1",
        session_id="replay-1",
        step_index=1,
        step_type="skill",
        name="page-analyze",
        input_data={"page": "alarm-config"},
        output_data={"ok": True},
        status="success",
    )

    checkpoint_record = checkpoint_snapshot_to_record(snapshot)
    session_record = replay_session_to_record(session)
    step_record = replay_step_to_record(step)

    assert checkpoint_record.checkpoint_id == "cp-1"
    assert checkpoint_record.values["phase"] == "Automation"
    assert session_record.page == "alarm-config"
    assert step_record.kind == "skill"
    assert step_record.output_data["ok"] is True

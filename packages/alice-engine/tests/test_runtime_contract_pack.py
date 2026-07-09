"""Runtime contract pack regression tests."""

from __future__ import annotations

from alice_engine.contracts import ExecutionContext, ExecutionResult
from alice_engine.runtime_contracts import (
    RuntimeArtifactRecord,
    RuntimeCheckpointRecord,
    RuntimeEventEnvelope,
    RuntimeReplaySessionRecord,
    RuntimeReplayStepRecord,
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
        provider="mock",
        entrypoint="sdk",
        request_id="req-1",
        run_id="run-1",
        metadata={"policy_version": "p1"},
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
        total_tokens=123,
        total_cost=0.45,
        agent_runs=3,
        artifacts=["artifacts/report.md"],
        duration_ms=987.6,
        completed_phases=["Requirement"],
        metadata={"replay_session_id": "replay-1", "checkpoint_thread_id": "thread-1"},
    )


def test_runtime_event_envelope_can_be_derived_from_execution_result():
    envelope = RuntimeEventEnvelope.from_execution_result(
        _make_result(),
        event_type="run.completed",
        context=_make_context(),
    )

    payload = envelope.to_dict()

    assert payload["event_type"] == "run.completed"
    assert payload["context"]["workspace_id"] == "ws-1"
    assert payload["total_tokens"] == 123
    assert payload["replay_session_id"] == "replay-1"
    assert payload["checkpoint_thread_id"] == "thread-1"
    assert payload["artifacts"][0]["path"] == "artifacts/report.md"


def test_runtime_contract_records_round_trip_to_dict():
    artifact = RuntimeArtifactRecord(
        path="artifacts/report.md",
        kind="report",
        phase="Report",
        module="equipment",
        run_id="run-1",
    )
    checkpoint = RuntimeCheckpointRecord(
        thread_id="thread-1",
        checkpoint_id="cp-1",
        available=True,
        values={"phase": "Automation"},
        raw={"id": "cp-1"},
        loaded_at="2026-07-08T00:00:00+00:00",
    )
    replay_session = RuntimeReplaySessionRecord(
        session_id="replay-1",
        run_id="run-1",
        module="equipment",
        status="completed",
        step_count=2,
    )
    replay_step = RuntimeReplayStepRecord(
        step_id="step-1",
        session_id="replay-1",
        index=1,
        kind="skill",
        name="page-analyze",
        status="success",
        input_data={"page": "alarm-config"},
        output_data={"ok": True},
    )

    assert artifact.to_dict()["kind"] == "report"
    assert checkpoint.to_dict()["values"]["phase"] == "Automation"
    assert replay_session.to_dict()["step_count"] == 2
    assert replay_step.to_dict()["output_data"]["ok"] is True

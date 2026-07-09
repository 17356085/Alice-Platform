"""Hard contract tests for RunEvent schema and RuntimeEventEnvelope projection."""

from __future__ import annotations

from alice_engine.contracts import ExecutionContext, ExecutionResult
from alice_engine.runtime_contracts import RuntimeArtifactRecord

from aitest.platform.run_event import EVENT_SCHEMAS, EventType
from aitest.platform.runtime_contracts import runtime_event_from_payload, runtime_event_from_result, runtime_event_to_run_event


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
        total_tokens=111,
        total_cost=0.25,
        agent_runs=2,
        artifacts=["artifacts/report.md"],
        duration_ms=123.4,
        completed_phases=["Requirement"],
        failed_phases=["Automation"],
    )


def _common_version_metadata() -> dict[str, str]:
    return {
        "policy_version": "p1",
        "governance_version": "g1",
        "config_version": "c1",
        "governance_pack_root": "/pack",
    }


def _run_completed_event():
    envelope = runtime_event_from_result(
        _make_result(),
        event_type=EventType.RUN_COMPLETED,
        context=_make_context(),
        replay_session_id="replay-1",
        checkpoint_thread_id="thread-1",
        artifacts=[RuntimeArtifactRecord(path="artifacts/report.md", kind="report", run_id="run-1")],
        metadata={
            **_common_version_metadata(),
            "retry_count": 1,
            "max_retries": 3,
        },
    )
    return runtime_event_to_run_event(envelope)


def _contract_cases():
    return [
        (
            EventType.EXECUTION_REQUESTED,
            lambda: runtime_event_to_run_event(
                runtime_event_from_payload(
                    event_type=EventType.EXECUTION_REQUESTED,
                    request_id="req-1",
                    context=_make_context(),
                    module="equipment",
                    pages=["alarm-config"],
                    agent="automation-agent",
                    metadata=_common_version_metadata(),
                )
            ),
        ),
        (
            EventType.EXECUTION_STARTED,
            lambda: runtime_event_to_run_event(
                runtime_event_from_payload(
                    event_type=EventType.EXECUTION_STARTED,
                    run_id="run-1",
                    request_id="req-1",
                    context=_make_context(),
                    module="equipment",
                    agent="automation-agent",
                    replay_session_id="replay-1",
                    metadata=_common_version_metadata(),
                )
            ),
        ),
        (EventType.RUN_COMPLETED, _run_completed_event),
        (
            EventType.RUN_FAILED,
            lambda: runtime_event_to_run_event(
                runtime_event_from_payload(
                    event_type=EventType.RUN_FAILED,
                    run_id="run-2",
                    request_id="req-2",
                    context=_make_context(),
                    module="equipment",
                    agent="automation-agent",
                    total_tokens=9,
                    total_cost=0.5,
                    agent_runs=1,
                    duration_ms=44.0,
                    error_message="boom",
                    replay_session_id="replay-2",
                    checkpoint_thread_id="thread-2",
                    completed_phases=["Requirement"],
                    failed_phases=["Automation"],
                    artifacts=[RuntimeArtifactRecord(path="artifacts/error.log", kind="log", run_id="run-2")],
                    metadata={
                        **_common_version_metadata(),
                        "retry_count": 0,
                        "max_retries": 3,
                    },
                )
            ),
        ),
        (
            EventType.RUN_CANCELLED,
            lambda: runtime_event_to_run_event(
                runtime_event_from_payload(
                    event_type=EventType.RUN_CANCELLED,
                    run_id="run-5",
                    request_id="req-5",
                    module="equipment",
                    agent="automation-agent",
                    metadata={
                        "workspace_id": "ws-1",
                        "org_id": "org-1",
                    },
                )
            ),
        ),
        (
            EventType.COST_RECORDED,
            lambda: runtime_event_to_run_event(
                runtime_event_from_payload(
                    event_type=EventType.COST_RECORDED,
                    run_id="run-3",
                    request_id="req-3",
                    total_tokens=50,
                    total_cost=1.5,
                    replay_session_id="replay-3",
                    metadata={
                        "workspace_id": "ws-1",
                        "org_id": "org-1",
                        **_common_version_metadata(),
                    },
                )
            ),
        ),
        (
            EventType.PHASE_STARTED,
            lambda: runtime_event_to_run_event(
                runtime_event_from_payload(
                    event_type=EventType.PHASE_STARTED,
                    run_id="run-4",
                    request_id="req-4",
                    module="equipment",
                    phase="execution",
                    replay_session_id="replay-4",
                    metadata=_common_version_metadata(),
                )
            ),
        ),
        (
            EventType.PHASE_COMPLETED,
            lambda: runtime_event_to_run_event(
                runtime_event_from_payload(
                    event_type=EventType.PHASE_COMPLETED,
                    run_id="run-4",
                    request_id="req-4",
                    module="equipment",
                    phase="execution",
                    replay_session_id="replay-4",
                    metadata=_common_version_metadata(),
                )
            ),
        ),
    ]


def test_runtime_event_projection_matches_frozen_schema_keys_for_core_events():
    for event_type, build_event in _contract_cases():
        event = build_event()
        assert set(event.data) == set(EVENT_SCHEMAS[event_type]), event_type


def test_run_completed_projection_matches_frozen_schema_keys_and_values():
    event = _run_completed_event()

    assert set(event.data) == set(EVENT_SCHEMAS[EventType.RUN_COMPLETED])
    assert event.data["workspace_id"] == "ws-1"
    assert event.data["org_id"] == "org-1"
    assert event.data["module"] == "equipment"
    assert event.data["pages"] == ["alarm-config"]
    assert event.data["agent"] == "automation-agent"
    assert event.data["total_tokens"] == 111
    assert event.data["total_cost"] == 0.25
    assert event.data["agent_runs"] == 2
    assert event.data["duration_ms"] == 123.4
    assert event.data["retry_count"] == 1
    assert event.data["max_retries"] == 3
    assert event.data["replay_session_id"] == "replay-1"
    assert event.data["checkpoint_thread_id"] == "thread-1"
    assert event.data["completed_phases"] == ["Requirement"]
    assert event.data["failed_phases"] == ["Automation"]
    assert event.data["artifact_type"] == "report"
    assert event.data["artifact_path"] == "artifacts/report.md"
    assert event.data["artifacts"] == [
        {
            "path": "artifacts/report.md",
            "kind": "report",
            "phase": "",
            "module": "",
            "page": "",
            "run_id": "run-1",
            "metadata": {},
        }
    ]


def test_run_cancelled_projection_matches_frozen_schema_keys_and_values():
    cancelled = dict(_contract_cases())[EventType.RUN_CANCELLED]()

    assert set(cancelled.data) == set(EVENT_SCHEMAS[EventType.RUN_CANCELLED])
    assert cancelled.data["workspace_id"] == "ws-1"
    assert cancelled.data["org_id"] == "org-1"
    assert cancelled.data["module"] == "equipment"
    assert cancelled.data["agent"] == "automation-agent"

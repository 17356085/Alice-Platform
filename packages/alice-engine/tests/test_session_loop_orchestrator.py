from __future__ import annotations

from types import SimpleNamespace

from alice_engine.core.session_orchestrator import SessionLoopOrchestrator
from alice_engine.core.task import AgentState, Observation


class _ReplaySink:
    def __init__(self):
        self.recorder = None
        self.begins = []
        self.records = []

    def begin_skill_step(self, **kwargs):
        self.begins.append(kwargs)
        return SimpleNamespace(id="step-1")

    def record_skill_response(self, **kwargs):
        self.records.append(kwargs)


def _make_orchestrator(*, plan_results, observation=None, abort_set=False):
    state = AgentState(agent_name="project-agent", goal="goal", module="equipment", page="alarm-config")
    replay_sink = _ReplaySink()
    emissions = []
    logs = []
    updates = []
    persists = []
    plan_iter = iter(plan_results)
    abort_event = SimpleNamespace(is_set=lambda: abort_set)
    observed = observation or Observation(skill_id="project/demo", status="pass", suggestion="continue", summary="ok")

    orchestrator = SessionLoopOrchestrator(
        state=state,
        skills=["project/demo"],
        agent_name="project-agent",
        module="equipment",
        page="alarm-config",
        provider="mock",
        abort_event=abort_event,
        replay_sink=replay_sink,
        replay_recorder=object(),
        perceive_fn=lambda skill_id: {"skill_id": skill_id},
        plan_fn=lambda skill_index, perception: next(plan_iter),
        act_fn=lambda skill_id: SimpleNamespace(content="content", finish_reason="stop", usage={"input": 1, "output": 2}),
        observe_fn=lambda skill_id, response: observed,
        update_fn=lambda skill_id, obs: updates.append((skill_id, obs)),
        persist_skill_artifact_fn=lambda skill_id, content: persists.append((skill_id, content)) or "D:/tmp/output.md",
        emit_obs_fn=lambda event_type, data: emissions.append((event_type, data)),
        log_fn=lambda message: logs.append(message),
        retry_counts={},
        completed_skills_getter=lambda: state.completed_skills,
    )
    return orchestrator, state, replay_sink, emissions, logs, updates, persists


def test_orchestrator_handles_abort_before_planning():
    orchestrator, state, replay_sink, emissions, logs, updates, persists = _make_orchestrator(
        plan_results=[],
        abort_set=True,
    )

    result = orchestrator.run_iteration(0)

    assert result.should_continue is False
    assert state.done is True
    assert state.termination_reason == "cancelled"
    assert replay_sink.begins == []
    assert emissions == []
    assert updates == []
    assert persists == []


def test_orchestrator_handles_skip_without_acting():
    orchestrator, state, replay_sink, emissions, logs, updates, persists = _make_orchestrator(
        plan_results=[{"action": "skip", "skill_id": "project/demo", "reason": "already done"}],
    )

    result = orchestrator.run_iteration(0)

    assert result.should_continue is False
    assert state.done is True
    assert state.termination_reason == "some_skills_failed"
    assert len(updates) == 1
    assert updates[0][0] == "project/demo"
    assert updates[0][1].status == "skipped"
    assert replay_sink.begins == []


def test_orchestrator_runs_skill_turn_and_emits_events():
    orchestrator, state, replay_sink, emissions, logs, updates, persists = _make_orchestrator(
        plan_results=[{"action": "execute", "skill_id": "project/demo"}],
    )
    state.completed_skills.append("project/demo")

    result = orchestrator.run_iteration(0)

    assert result.should_continue is False
    assert state.done is True
    assert state.success is True
    assert state.termination_reason == "all_skills_completed"
    assert replay_sink.begins[0]["skill_id"] == "project/demo"
    assert replay_sink.records[0]["provider"] == "mock"
    assert persists == [("project/demo", "content")]
    assert emissions[0][0] == "skill_start"
    assert emissions[1][0] == "skill_complete"
    assert updates[0][0] == "project/demo"

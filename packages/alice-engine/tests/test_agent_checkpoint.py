"""AgentLoop durable checkpoint contract tests."""

from alice_engine.core.executor import AgentLoop
from alice_engine.core.task import AgentState, Observation


def test_agent_state_checkpoint_round_trip_preserves_progress():
    original = AgentState(
        agent_name="automation-agent",
        goal="continue the staging run",
        module="checkout",
        page="cart",
        provider="mimo",
        step=2,
        max_steps=8,
        current_skill="automation/tech-analysis",
        completed_skills=["automation/project-init"],
        failed_skills={"automation/tech-analysis": "temporary provider error"},
        retry_counts={"automation/tech-analysis": 1},
        memory={"mode": "resume", "marker": "checkpoint"},
        artifacts={"report": "report.md"},
    )
    original.observations.append(
        Observation(
            skill_id="automation/project-init",
            status="pass",
            summary="project loaded",
            token_usage={"input": 3, "output": 5},
        )
    )

    restored = AgentState.from_dict(original.to_dict())

    assert restored.to_dict() == original.to_dict()
    assert restored.observations[0].summary == "project loaded"


def test_agent_loop_resume_starts_at_unfinished_skill(monkeypatch):
    import alice_engine.core.executor as executor

    monkeypatch.setitem(
        executor.AGENT_SKILL_MAP,
        "automation-agent",
        ["skill-one", "skill-two", "skill-three"],
    )
    loop = AgentLoop.__new__(AgentLoop)
    loop.agent_name = "automation-agent"
    loop._skill_subset = None
    loop.mode = "resume"
    loop._resume_state = {"current_skill": "skill-two"}
    loop.state = AgentState(
        agent_name="automation-agent",
        current_skill="skill-two",
        completed_skills=["skill-one"],
    )

    assert loop._resume_skill_index() == 1


def test_agent_loop_resume_retries_skill_interrupted_before_update(monkeypatch):
    import alice_engine.core.executor as executor

    monkeypatch.setitem(executor.AGENT_SKILL_MAP, "automation-agent", ["skill-one", "skill-two"])
    loop = AgentLoop.__new__(AgentLoop)
    loop.agent_name = "automation-agent"
    loop._skill_subset = None
    loop.mode = "resume"
    loop._resume_state = {"current_skill": "skill-two"}
    loop.state = AgentState(
        agent_name="automation-agent",
        current_skill="skill-two",
        completed_skills=["skill-one"],
    )

    assert loop._resume_skill_index() == 1

"""Importable local functions used by the RQ staging probes."""

import time


def stage_success(
    agent_name: str,
    provider: str = "mock",
    module: str = "",
    page: str = "",
    mode: str = "full",
) -> dict:
    return {
        "agent_name": agent_name,
        "provider": provider,
        "module": module,
        "page": page,
        "mode": mode,
    }


def stage_failure(
    agent_name: str,
    provider: str = "mock",
    module: str = "",
    page: str = "",
    mode: str = "full",
) -> dict:
    raise RuntimeError(f"staging failure mode={mode}")


def stage_long_task(seconds: float = 60, marker: str = "") -> dict:
    """A deterministic long task used only to exercise worker recovery."""
    time.sleep(max(0.0, float(seconds)))
    return {"status": "completed", "marker": marker}


def stage_agentloop_long_task(seconds: float = 5, marker: str = "") -> dict:
    """Run one real MiMo AgentLoop, then remain killable for recovery testing."""
    import os
    import tempfile
    from pathlib import Path

    with tempfile.TemporaryDirectory(prefix="rq-agentloop-skill-") as tmp:
        skill = Path(tmp) / "skills" / "automation" / "tech-analysis.md"
        skill.parent.mkdir(parents=True, exist_ok=True)
        skill.write_text(
            "# RQ staging skill\n\nConfirm the staging task was received. Do not use tools.\n",
            encoding="utf-8",
        )
        previous = os.environ.get("ENGINE_GOVERNANCE_PATH")
        os.environ["ENGINE_GOVERNANCE_PATH"] = tmp
        try:
            from alice_engine.core.executor import AgentLoop

            agent = AgentLoop(
                "automation-agent",
                provider="mimo",
                model=os.environ.get("MIMO_MODEL", "mimo-v2.5"),
                skill_subset=["automation/tech-analysis"],
                deep_review=False,
                use_reliable_provider=False,
                use_window_monitor=False,
                verbose=False,
                goal="Confirm the RQ staging prompt was received.",
                max_steps=1,
            )
            agent._use_tool_calling = False
            state = agent.run()
        finally:
            if previous is None:
                os.environ.pop("ENGINE_GOVERNANCE_PATH", None)
            else:
                os.environ["ENGINE_GOVERNANCE_PATH"] = previous

    time.sleep(max(0.0, float(seconds)))
    return {
        "status": "completed",
        "marker": marker,
        "provider": state.provider,
        "termination": state.termination_reason,
    }

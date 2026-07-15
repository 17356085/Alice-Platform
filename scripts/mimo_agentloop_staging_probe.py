"""Run one real AgentLoop skill against MiMo.

By default this uses a synthetic public prompt.  ``MIMO_LOCAL_SKILL_PATH`` can
be set to one explicitly approved local Markdown skill to verify the complete
local-skill -> SkillLoader -> AgentLoop -> MiMo path.  The probe still sends
no project path, page config, workspace context, or repository files.

Run from the repository root::

    python scripts/mimo_agentloop_staging_probe.py
"""

from __future__ import annotations

import json
import os
import tempfile
from pathlib import Path


def _load_dotenv() -> None:
    try:
        from dotenv import load_dotenv

        load_dotenv(Path(__file__).resolve().parents[1] / ".env", override=False)
    except Exception:
        pass


def _synthetic_governance(root: Path) -> None:
    skill = root / "skills" / "automation" / "tech-analysis.md"
    skill.parent.mkdir(parents=True, exist_ok=True)
    skill.write_text(
        """# Public staging skill

You are a staging probe. Do not use tools or access files. Reply with a short
confirmation that the public prompt was received.
""",
        encoding="utf-8",
    )


def _local_governance(root: Path, source: Path) -> str:
    skill_id = "test-design/page-observe"
    target = root / "skills" / f"{skill_id}.md"
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(source.read_text(encoding="utf-8"), encoding="utf-8")
    return skill_id


def main() -> None:
    _load_dotenv()
    if not os.environ.get("MIMO_API_KEY"):
        raise SystemExit("MIMO_API_KEY is not configured")

    with tempfile.TemporaryDirectory(prefix="mimo-agentloop-public-") as tmp:
        governance = Path(tmp)
        local_skill = os.environ.get("MIMO_LOCAL_SKILL_PATH", "").strip()
        if local_skill:
            skill_id = _local_governance(governance, Path(local_skill).resolve())
            agent_name = "test-design-agent"
            goal = "Confirm the approved local skill prompt was received. Do not use tools or access files."
        else:
            _synthetic_governance(governance)
            skill_id = "automation/tech-analysis"
            agent_name = "automation-agent"
            goal = "Confirm the synthetic public staging prompt was received."
        os.environ["ENGINE_GOVERNANCE_PATH"] = str(governance)

        # Import after setting ENGINE_GOVERNANCE_PATH so the engine resolves
        # only this synthetic behavior pack for the run.
        from alice_engine.core.executor import AgentLoop

        agent = AgentLoop(
            agent_name,
            provider="mimo",
            model=os.environ.get("MIMO_MODEL", "mimo-v2.5-pro"),
            skill_subset=[skill_id],
            deep_review=False,
            use_reliable_provider=False,
            use_window_monitor=False,
            verbose=False,
            goal=goal,
            max_steps=2,
        )
        # Prevent optional local tool schemas from being attached to this
        # external boundary probe; the prompt itself is still real.
        agent._use_tool_calling = False
        state = agent.run()

        observations = []
        for item in state.observations:
            usage = getattr(item, "token_usage", None) or getattr(item, "usage", None) or {}
            observations.append(
                {
                    "skill_id": getattr(item, "skill_id", ""),
                    "status": getattr(item, "status", ""),
                    "provider": getattr(item, "provider", "") or state.provider,
                    "finish_reason": getattr(item, "finish_reason", ""),
                    "token_usage": {
                        "input": usage.get("input", 0),
                        "output": usage.get("output", 0),
                        "total": usage.get("total", usage.get("input", 0) + usage.get("output", 0)),
                    },
                }
            )

        result = {
            "status": "ok" if observations and state.step >= 1 else "failed",
            "agent": state.agent_name,
            "provider": state.provider,
            "model": getattr(agent, "model", ""),
            "step": state.step,
            "termination": state.termination_reason,
            "observations": observations,
        }
        print(json.dumps(result, ensure_ascii=False))
        if result["status"] != "ok":
            raise SystemExit(1)


if __name__ == "__main__":
    main()

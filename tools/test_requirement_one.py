"""Test requirement-agent for one page — verify new skill prompts work.
Output written to test_requirement_output.txt in workspace root.
"""
import sys
from pathlib import Path
WORKSTUDY = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(WORKSTUDY))

# Write output to file directly (bypass stdout buffering issues on Windows)
out_path = WORKSTUDY / "test_requirement_output.txt"
out = open(str(out_path), "w", encoding="utf-8")

def log(msg):
    print(msg)
    out.write(msg + "\n")
    out.flush()

log("Starting requirement-agent for warehouse/hazard-item...")
log("=" * 60)

from aitest.agents.agent_runner import AgentLoop

agent = AgentLoop(
    "requirement-agent",
    provider="claude",
    module="warehouse",
    page="hazard-item",
    verbose=True,
)
state = agent.run()

log("=" * 60)
log(f"Success: {state.success}")
log(f"Termination: {state.termination_reason}")
log(f"Completed skills: {state.completed_skills}")
log(f"Failed skills: {state.failed_skills}")
log(f"Steps: {state.step}")
out.close()
print(f"\nOutput written to {out_path}")

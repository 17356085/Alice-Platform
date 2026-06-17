"""Test test-design-agent for one page — verify page-observe works."""
import sys
from pathlib import Path
WORKSTUDY = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(WORKSTUDY))

from aitest.agents.agent_runner import AgentLoop

print("Starting test-design-agent for warehouse/hazard-item...")
print("=" * 60)

agent = AgentLoop(
    "test-design-agent",
    provider="claude",
    module="warehouse",
    page="hazard-item",
    verbose=True,
)
state = agent.run()

print("=" * 60)
print(f"Success: {state.success}")
print(f"Termination: {state.termination_reason}")
print(f"Completed skills: {state.completed_skills}")
print(f"Failed skills: {state.failed_skills}")
print(f"Steps: {state.step}")

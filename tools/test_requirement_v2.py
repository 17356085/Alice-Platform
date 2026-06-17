"""Test requirement-agent v2 — verify new prompt + code injection produce accurate PAGE_CONTEXT."""
import sys
from pathlib import Path
WORKSTUDY = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(WORKSTUDY))

out_path = WORKSTUDY / "test_requirement_v2_output.txt"
out = open(str(out_path), "w", encoding="utf-8")

def log(msg):
    print(msg)
    out.write(msg + "\n")
    out.flush()

log("Testing requirement-agent v2 for warehouse/spare-item...")
log("=" * 60)

from aitest.agents.agent_runner import AgentLoop

agent = AgentLoop(
    "requirement-agent",
    provider="claude",
    module="warehouse",
    page="spare-item",
    verbose=True,
)
state = agent.run()

log("=" * 60)
log(f"Success: {state.success}")
log(f"Completed: {state.completed_skills}")
log(f"Failed: {state.failed_skills}")
log(f"Steps: {state.step}")

# Check generated PAGE_CONTEXT
pc_path = WORKSTUDY / "governance/context/projects/web-automation/modules/warehouse/pages/spare-item/PAGE_CONTEXT.md"
if pc_path.exists():
    content = pc_path.read_text(encoding="utf-8")
    log(f"\nPAGE_CONTEXT size: {len(content)} chars")
    # Check for real vs fabricated content
    if "FILTER_ITEM_NAME" in content or "物品名称" in content:
        log("QUALITY: Real PO element names found")
    if "请输入物品名称" in content:
        log("QUALITY: Real placeholder text found")
    if "库管管理" in content or "备品备件管理" in content:
        log("QUALITY: Real navigation path found")
    if "search.code" in content:
        log("QUALITY_ISSUE: Fabricated element search.code still present")
    if "search.name" in content:
        log("QUALITY_ISSUE: Fabricated element search.name still present")

out.close()
log(f"\nFull output: {out_path}")

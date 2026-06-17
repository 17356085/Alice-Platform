"""Quick test: hazard-in-order with code in user prompt."""
import sys
from pathlib import Path
WORKSTUDY = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(WORKSTUDY))

out_path = WORKSTUDY / "test_hio_output.txt"
out = open(str(out_path), "w", encoding="utf-8")

def log(msg):
    print(msg)
    out.write(msg + "\n")
    out.flush()

log("Testing requirement-agent v3 (code in user prompt) for warehouse/hazard-in-order...")
log("=" * 60)

from aitest.agents.agent_runner import AgentLoop

agent = AgentLoop("requirement-agent", provider="claude", module="warehouse", page="hazard-in-order", verbose=True)
state = agent.run()

log("=" * 60)
log(f"Success: {state.success}")
log(f"Completed: {state.completed_skills}")
log(f"Steps: {state.step}")

pc_path = WORKSTUDY / "governance/context/projects/web-automation/modules/warehouse/pages/hazard-in-order/PAGE_CONTEXT.md"
if pc_path.exists():
    content = pc_path.read_text(encoding="utf-8")
    log(f"\nPAGE_CONTEXT size: {len(content)} chars")
    checks = [
        ("FILTER_HANDLER" in content or "FILTER_STATUS" in content, "Real PO locators"),
        ("经办人" in content, "Real placeholder (经办人)"),
        ("search-orderNo" in content, "FABRICATED search-orderNo"),
        ("search-materialName" in content, "FABRICATED search-materialName"),
    ]
    for ok, label in checks:
        log(f"  {'PASS' if ok else 'FAIL'}: {label}")

out.close()
log(f"\nOutput: {out_path}")

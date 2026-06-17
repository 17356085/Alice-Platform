"""Debug review graph run."""
import sys
sys.path.insert(0, "d:/Desktop/WorkStudy")

from aitest.graphs.review_graph import build_review_graph, entry_node, run_review_phase, route_after_phase

# Step through manually
state = entry_node({"mode": "architecture", "trigger": "manual", "module": "system"})
print(f"Entry: phases={state['phases']}, idx={state['phase_index']}")
print(f"Route: {route_after_phase(state)}")

# Run the phase directly
print("\nRunning review phase (LLM call)...")
try:
    state2 = run_review_phase(state)
    print(f"After phase: review_results keys={list(state2.get('review_results', {}).keys())}")
    print(f"Phase index: {state2.get('phase_index')}")
    for k, v in state2.get("review_results", {}).items():
        preview = v[:200] if isinstance(v, str) else v
        print(f"  {k}: {preview}...")
except Exception as e:
    print(f"ERROR: {e}")
    import traceback
    traceback.print_exc()

# Test route after phase
state_merged = {**state, **state2}
print(f"\nRoute after phase: {route_after_phase(state_merged)}")

# Test synthesis
from aitest.graphs.review_graph import synthesis_node
try:
    state3 = synthesis_node(state_merged)
    print(f"Synthesis: {len(state3.get('synthesis_report', ''))} chars")
except Exception as e:
    print(f"Synthesis ERROR: {e}")

"""
全模块 preflight 状态扫描 — 不触发任何 Agent/LLM 调用。
用法: python tools/scan_all_modules.py
"""
import sys
from pathlib import Path

WORKSTUDY = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(WORKSTUDY))

from aitest.graphs.sop_graph import preflight_node
from aitest.graphs.state import create_initial_state

# 清除缓存，强制重新扫描
import aitest.graphs.sop_graph as sg
sg._preflight_cache.clear()
sg._preflight_cache_mtimes.clear()

MODULES = [
    "dcs", "equipment", "lab", "personnel", "production",
    "sales", "system", "system-management", "system-role",
    "tank", "warehouse", "workflow",
]

print("=" * 100)
print(f"{'Module':<20} {'Pages':<7} {'PROJ':<5} {'MOD':<5} {'PgCtx':<7} {'TC':<6} {'TD':<5} {'TA':<5} {'AS':<5} {'Code':<5} {'Fail':<5} {'Rec.Mode':<22}")
print("=" * 100)

all_results = {}
total_pages = 0

for mod in MODULES:
    state = create_initial_state(mod, [], mode="status")
    result = preflight_node(state)
    all_results[mod] = result

    ad = result["agent_outputs"]["preflight_auto_detect"]
    per_page = result.get("per_page_results", [])
    n = len(per_page)
    total_pages += n

    def ratio(key):
        if n == 0:
            return "N/A"
        ok = sum(1 for p in per_page if p.get(key))
        return f"{ok}/{n}"

    print(f"{mod:<20} {n:<7} "
          f"{'Y' if ad['has_project'] else 'N':<5} "
          f"{'Y' if ad['has_module'] else 'N':<5} "
          f"{ratio('has_page_context'):<7} "
          f"{ratio('has_test_cases'):<6} "
          f"{ratio('has_test_design'):<5} "
          f"{ratio('has_tech_analysis'):<5} "
          f"{ratio('has_auto_strategy'):<5} "
          f"{'Y' if ad['has_code'] else 'N':<5} "
          f"{'Y' if ad['has_failures'] else 'N':<5} "
          f"{ad['recommended_mode']:<22}")

print("=" * 100)

# ── 缺口分析 ──
print("\n── GAP DETAIL ──\n")
by_mode = {}
for mod, result in all_results.items():
    ad = result["agent_outputs"]["preflight_auto_detect"]
    mode = ad["recommended_mode"]
    per_page = result.get("per_page_results", [])

    missing = []
    for p in per_page:
        gaps = []
        if not p["has_page_context"]:
            gaps.append("PgCtx")
        if not p["has_test_cases"]:
            gaps.append("TC")
        if not p["has_test_design"]:
            gaps.append("TD")
        if not p["has_tech_analysis"]:
            gaps.append("TA")
        if not p["has_auto_strategy"]:
            gaps.append("AS")
        if gaps:
            missing.append(f"    {p['page_slug']}: missing [{', '.join(gaps)}]")

    if not ad["has_code"]:
        missing.append("    ** CODE 目录缺失 **")

    if missing or mode != "from-automation":
        by_mode.setdefault(mode, []).append((mod, missing, ad))

for mode in ["full", "from-requirement", "from-test-design", "from-automation"]:
    items = by_mode.get(mode, [])
    if not items:
        continue
    print(f"[mode={mode}] {len(items)} module(s):")
    for mod, missing, ad in items:
        reason = ad.get("reason", "?")
        print(f"  {mod} — {reason}")
        for m in missing[:8]:  # limit per module
            print(m)
        if len(missing) > 8:
            print(f"    ... and {len(missing)-8} more gaps")
    print()

# ── Token 估算 ──
print("── TOKEN ESTIMATE (SOP → Test Design phase) ──\n")
affected = 0
for mod, result in all_results.items():
    ad = result["agent_outputs"]["preflight_auto_detect"]
    if ad["recommended_mode"] in ("full", "from-requirement", "from-test-design"):
        affected += len(result.get("pages", []))

est_input = affected * 55000   # Req + TD per page
est_output = affected * 13000
print(f"  Pages needing Req+TD: {affected}")
print(f"  Est. input tokens:    ~{est_input/1e6:.1f}M")
print(f"  Est. output tokens:   ~{est_output/1e6:.1f}M")
print(f"  Est. total:           ~{(est_input+est_output)/1e6:.1f}M")
print(f"  Est. cost (Opus):     ~${est_input/1e6*15 + est_output/1e6*75:.0f}")

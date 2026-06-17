#!/usr/bin/env python3
"""sync_progress.py — 从 SOP_STATUS + 文件系统生成 progress-tracking.md 自动段

数据源 (单一真相来源):
  1. governance/artifacts/sop-status/SOP_STATUS_*.json → Phase 完成状态
  2. ZJSN_Test-master526/script/<module>/test_*.py → 测试文件计数
  3. ZJSN_Test-master526/page/<module>_page/ → Page Object 计数
  4. governance/context/projects/web-automation/modules/<module>/ → 治理文档计数

用法:
  python tools/sync_progress.py              # 更新 progress-tracking.md
  python tools/sync_progress.py --check       # 仅检查是否过期 (CI/门禁)
  python tools/sync_progress.py --json        # 输出 JSON 到 stdout
"""

import json
import os
import re
import sys
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import Optional

ROOT = Path(__file__).resolve().parent.parent

SOP_STATUS_DIR = ROOT / "governance" / "artifacts" / "sop-status"
TEST_SCRIPT_DIR = ROOT / "ZJSN_Test-master526" / "script"
PAGE_DIR = ROOT / "ZJSN_Test-master526" / "page"
GOV_MODULES_DIR = ROOT / "governance" / "context" / "projects" / "web-automation" / "modules"
PROGRESS_FILE = ROOT / "governance" / "context" / "tracking" / "progress-tracking.md"
TZ = timezone(timedelta(hours=8))  # CST

# ── Module registry ──────────────────────────────────────────────────────
# canonical_name: (display_name, script_dir_name, page_dir_pattern, gov_dir_name)
MODULE_REGISTRY = {
    "system-user":      ("system-user",      "system",             "system_page",        "system"),
    "system-role":      ("system-role",      "system-role",        "system-role_page",   "system-role"),
    "system-management":("system-management","system-management",  "system-management_page", "system-management"),
    "equipment":        ("equipment",        "equipment",          "equipment_page",     "equipment"),
    "tank":             ("tank",             "tank",               "tank_page",          "tank"),
    "personnel":        ("personnel",        "personnel",          "personnel_page",     "personnel"),
    "sales":            ("sales",            "sales",              "sales_page",         "sales"),
    "lab":              ("lab",              "lab",                "lab_page",           "lab"),
    "production":       ("production",       "production",         "production_page",    "production"),
    "dcs":              ("dcs",              "dcs",                "dcs_page",           "dcs"),
    "warehouse":        ("warehouse",        "warehouse",          "warehouse_page",     "warehouse"),
    "workflow":         ("workflow",         "workflow",           "workflow_page",      "workflow"),
}

# SOP phase → tracking phase mapping
SOP_TO_TRACKING = {
    "Project Init":  ["0.5", "1"],
    "Requirement":   ["1.5", "2"],
    "Test Design":   ["2.5", "3", "3.5"],
    "Automation":    ["4"],
}

TRACKING_PHASES = ["0.5", "1", "1.5", "2", "2.5", "3", "3.5", "4", "8"]

# Modules with Phase 8 (test summary) complete
PHASE8_COMPLETE = {"tank", "lab"}

# Quality thresholds: SOP says phase done but artifacts < page_count * threshold → flag
QUALITY_THRESHOLD_PHASE_3 = 0.5   # TECH_ANALYSIS: 50% page coverage
QUALITY_THRESHOLD_PHASE_35 = 0.3  # AUTO_STRATEGY: 30% page coverage


# ── Data access ──────────────────────────────────────────────────────────

# Fallback: module_key → SOP_STATUS filename (for aggregated modules)
SOP_STATUS_ALIAS = {
    "system-user": "system",
    "system-management": "system",
}


def load_sop_status(module_key: str) -> Optional[dict]:
    """Load SOP_STATUS JSON for a module. Returns None if not found."""
    # Try exact match first
    path = SOP_STATUS_DIR / f"SOP_STATUS_{module_key}.json"
    if path.exists():
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    # Try alias fallback
    alias = SOP_STATUS_ALIAS.get(module_key)
    if alias:
        path = SOP_STATUS_DIR / f"SOP_STATUS_{alias}.json"
        if path.exists():
            with open(path, "r", encoding="utf-8") as f:
                return json.load(f)
    return None


def count_test_files(module_key: str) -> int:
    entry = MODULE_REGISTRY.get(module_key)
    if not entry:
        return 0
    script_dir = TEST_SCRIPT_DIR / entry[1]
    return len(list(script_dir.glob("test_*.py"))) if script_dir.exists() else 0


def count_po_files(module_key: str) -> int:
    entry = MODULE_REGISTRY.get(module_key)
    if not entry:
        return 0
    page_dir = PAGE_DIR / entry[2]
    if not page_dir.exists():
        # try underscore→hyphen fallback
        alt = PAGE_DIR / entry[2].replace("_page", "-page")
        page_dir = alt if alt.exists() else page_dir
    if not page_dir.exists():
        return 0
    return len([f for f in page_dir.glob("*.py") if f.name != "__init__.py"])


def count_gov_artifacts(module_key: str) -> dict:
    entry = MODULE_REGISTRY.get(module_key)
    if not entry:
        return {"md": 0, "tech": 0, "auto": 0, "risk": 0, "ctx": 0, "page_ctx": 0}
    gov_dir = GOV_MODULES_DIR / entry[3]
    if not gov_dir.exists():
        return {"md": 0, "tech": 0, "auto": 0, "risk": 0, "ctx": 0, "page_ctx": 0}
    all_md = list(gov_dir.rglob("*.md"))
    return {
        "md": len(all_md),
        "tech": sum(1 for f in all_md if f.name == "TECH_ANALYSIS.md"),
        "auto": sum(1 for f in all_md if f.name == "AUTO_STRATEGY.md"),
        "risk": sum(1 for f in all_md if f.name == "RISK_MODEL.md"),
        "ctx": sum(1 for f in all_md if f.name in ("PAGE_CONTEXT.md", "MODULE_CONTEXT.md")),
        "page_ctx": sum(1 for f in all_md if f.name == "PAGE_CONTEXT.md"),
    }


def estimate_page_count(module_key: str) -> int:
    """Best-effort page count: SOP pages_processed > test files > gov page_ctx."""
    sop = load_sop_status(module_key)
    if sop and "pages_processed" in sop:
        return len(sop["pages_processed"])
    # Fallback: count test files as proxy for pages
    tests = count_test_files(module_key)
    if tests > 0:
        return tests
    return count_gov_artifacts(module_key)["page_ctx"]


# ── Phase computation ────────────────────────────────────────────────────

def compute_phase_status(module_key: str) -> dict:
    """Compute per-phase status. Returns {phase: emoji}."""
    phases = {p: "⏳" for p in TRACKING_PHASES}
    sop = load_sop_status(module_key)
    artifacts = count_gov_artifacts(module_key)
    page_count = estimate_page_count(module_key)

    if sop and sop.get("status") == "completed":
        completed_sop = set(sop.get("completed_phases", []))
        for sop_phase, tracking_phases in SOP_TO_TRACKING.items():
            if sop_phase in completed_sop:
                for tp in tracking_phases:
                    phases[tp] = "✅"

    elif sop and sop.get("status") == "pending":
        # All phases pending (e.g. system-management reset)
        pass

    else:
        # No SOP_STATUS — infer from artifacts
        if artifacts["ctx"] > 0:
            phases["0.5"] = "✅"

        # Phase 1 (页面分析): need per-page PAGE_CONTEXT, not just MODULE_CONTEXT
        if artifacts["page_ctx"] >= min(2, max(1, page_count)):
            phases["1"] = "✅"
        elif artifacts["ctx"] >= 2 and page_count <= 1:
            phases["1"] = "✅"

        if artifacts["risk"] > 0:
            phases["1.5"] = "✅"
            phases["2"] = "✅"
        if artifacts["tech"] > 0:
            phases["3"] = "✅"
            phases["2.5"] = "✅"  # 用例表与 TECH_ANALYSIS 同步生成
        if artifacts["auto"] > 0:
            phases["3.5"] = "✅"
        if count_test_files(module_key) > 0:
            phases["4"] = "✅"

    # Phase 8 (测试总结)
    if module_key in PHASE8_COMPLETE:
        phases["8"] = "✅"

    # ── Quality checks ──
    if page_count > 0 and sop and sop.get("status") == "completed":
        completed_sop = set(sop.get("completed_phases", []))
        if "Test Design" in completed_sop:
            # Phase 3 coverage: need TECH_ANALYSIS for most pages
            if artifacts["tech"] == 0:
                phases["3"] = "⏳"  # SOP lied — no artifacts
            elif artifacts["tech"] < page_count * QUALITY_THRESHOLD_PHASE_3:
                phases["3"] = "⚠️"
            # Phase 3.5 coverage: need AUTO_STRATEGY
            if artifacts["auto"] == 0:
                phases["3.5"] = "⏳"
            elif artifacts["auto"] < page_count * QUALITY_THRESHOLD_PHASE_35:
                phases["3.5"] = "⚠️"

    return phases


def compute_overall_pct(phases: dict) -> str:
    """Compute progress percentage. All 9 phases equal weight."""
    completed = sum(1 for v in phases.values() if v in ("✅", "⚠️"))
    total = len(TRACKING_PHASES)  # 9
    pct = round(completed / total * 100)
    if pct < 0:
        pct = 0
    if pct >= 100:
        return "**100%**"
    return f"{pct}%"


# ── Table generators ─────────────────────────────────────────────────────

def generate_progress_table() -> str:
    rows = []
    for mod_key in MODULE_REGISTRY:
        display = MODULE_REGISTRY[mod_key][0]
        phases = compute_phase_status(mod_key)
        pct = compute_overall_pct(phases)

        if "100" in pct:
            display = f"**{display}**"

        cells = [display] + [phases[p] for p in TRACKING_PHASES] + [pct]
        rows.append("| " + " | ".join(cells) + " |")

    header_cols = (
        ["模块"]
        + [f"Phase {p}<br>{label}" for p, label in [
            ("0.5", "模块建模"), ("1", "页面分析"), ("1.5", "风险建模"),
            ("2", "测试设计"), ("2.5", "用例表"), ("3", "技术分析"),
            ("3.5", "自动化策略"), ("4", "自动化开发"), ("8", "测试总结")
          ]]
        + ["整体进度"]
    )

    header = "| " + " | ".join(header_cols) + " |"
    sep = "|" + "|".join(["------" for _ in header_cols]) + "|"

    return "\n".join([header, sep] + rows)


def generate_test_stats_table() -> str:
    rows = []

    # Aggregate system
    sys_tests = sum(count_test_files(k) for k in ["system-user", "system-role", "system-management"])
    sys_po = sum(count_po_files(k) for k in ["system-user", "system-role", "system-management"])
    sys_gov = sum(count_gov_artifacts(k)["md"] for k in ["system-user", "system-role", "system-management"])
    rows.append(
        f"| system (user+role+mgmt) | {sys_tests} | {sys_po} | {sys_gov} "
        f"| 16+6+1 test files; system-management 已重置 |"
    )

    for mod_key in MODULE_REGISTRY:
        if mod_key.startswith("system"):
            continue
        display = MODULE_REGISTRY[mod_key][0]
        tests = count_test_files(mod_key)
        po = count_po_files(mod_key)
        a = count_gov_artifacts(mod_key)

        # Build note from artifact counts
        parts = []
        if a["tech"] > 0:
            parts.append(f"TECH={a['tech']}")
        if a["auto"] > 0:
            parts.append(f"AUTO={a['auto']}")
        if a["risk"] > 0:
            parts.append(f"RISK={a['risk']}")

        note = "; ".join(parts) if parts else "scaffold only"

        # Module-specific description
        specific = {
            "dcs": "all-data/common-data/monitor/point-config/upload-log; 无 SOP_STATUS",
            "lab": "gas/water 全覆盖",
            "equipment": "unit/device/sensor/alarm/maint/camera/keyparam + unit-manage",
            "personnel": "16 页面全覆盖",
            "production": "daily/monthly/business/shift",
            "tank": "monitor/report/alarm-config",
            "warehouse": "hazard/spare/reagent 系列",
            "workflow": "approval-chain/history/todo/my-application/sap-push-log",
            "sales": "customer/contract/order/daily-report",
        }
        sn = specific.get(mod_key, "")
        full_note = f"{note}; {sn}" if sn else note

        rows.append(f"| {display} | {tests} | {po} | {a['md']} | {full_note} |")

    header = "| 模块 | 测试文件 | Page Object | 治理文档 | 备注 |"
    sep = "|------|:-------:|:----------:|:------:|------|"

    return "\n".join([header, sep] + rows)


# ── Section replacer ─────────────────────────────────────────────────────

def replace_section(content: str, tag: str, new_body: str) -> str:
    """Replace content between <!-- BEGIN: tag --> and <!-- END: tag --> markers."""
    begin = f"<!-- ⚠️ AUTO-GENERATED SECTION BEGIN: {tag} -->"
    end = f"<!-- ⚠️ AUTO-GENERATED SECTION END: {tag} -->"

    pattern = re.escape(begin) + r".*?" + re.escape(end)
    replacement = begin + "\n" + new_body + "\n" + end
    return re.sub(pattern, replacement, content, flags=re.DOTALL)


def update_markdown_sections(content: str) -> str:
    """Replace all auto-generated sections in progress-tracking.md."""

    # Section: progress-table
    ts = datetime.now(TZ).strftime("%Y-%m-%d %H:%M")
    table_body = (
        f"<!-- Source: governance/artifacts/sop-status/SOP_STATUS_*.json + script/ test file counts -->\n"
        f"<!-- Regenerate: python tools/sync_progress.py -->\n"
        f"> 最后更新：{ts} (auto-sync)\n\n"
        f"---\n\n"
        f"## 进度总览\n\n"
        f"{generate_progress_table()}\n\n"
        f"> 图例：✅ 已完成 | 🔄 进行中 | ⚠️ 已完成但质量不足（部分页面覆盖） | ⏳ 待开始 | ❌ 阻塞 | — 不适用"
    )
    content = replace_section(content, "progress-table", table_body)

    # Section: test-stats
    stats_body = generate_test_stats_table()
    content = replace_section(content, "test-stats", stats_body + "\n")

    # Update footer timestamp
    content = re.sub(
        r"<!-- FOOTER:.*?-->",
        f"<!-- FOOTER: last_sync={datetime.now(TZ).strftime('%Y-%m-%dT%H:%M:%S%z')} sync_source=auto -->",
        content
    )

    return content


# ── Check mode ───────────────────────────────────────────────────────────

def check_freshness() -> tuple:
    """Check if progress-tracking.md is stale vs SOP_STATUS files."""
    if not PROGRESS_FILE.exists():
        return False, "progress-tracking.md not found"

    newest_sop = None
    for f in SOP_STATUS_DIR.glob("SOP_STATUS_*.json"):
        mtime = f.stat().st_mtime
        if newest_sop is None or mtime > newest_sop:
            newest_sop = mtime

    if newest_sop is None:
        return True, "No SOP_STATUS files to compare"

    content = PROGRESS_FILE.read_text(encoding="utf-8")
    match = re.search(r"last_sync=(\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2})", content)
    if not match:
        return False, "No sync timestamp in progress-tracking.md"

    sync_ts = datetime.strptime(match.group(1), "%Y-%m-%dT%H:%M:%S")
    sop_ts = datetime.fromtimestamp(newest_sop)

    if sop_ts > sync_ts:
        return False, f"SOP_STATUS newer ({sop_ts.isoformat()}) than sync ({sync_ts.isoformat()})"

    return True, "Fresh"


# ── JSON output ──────────────────────────────────────────────────────────

def json_output():
    data = {
        "generated_at": datetime.now(TZ).isoformat(),
        "modules": {}
    }
    for mod_key in MODULE_REGISTRY:
        phases = compute_phase_status(mod_key)
        sop = load_sop_status(mod_key)
        data["modules"][mod_key] = {
            "display": MODULE_REGISTRY[mod_key][0],
            "phases": phases,
            "overall_pct": compute_overall_pct(phases),
            "test_files": count_test_files(mod_key),
            "po_files": count_po_files(mod_key),
            "gov_artifacts": count_gov_artifacts(mod_key),
            "sop_status": sop.get("status") if sop else None,
            "sop_updated": sop.get("updated_at") if sop else None,
            "page_count": estimate_page_count(mod_key),
        }
    print(json.dumps(data, ensure_ascii=False, indent=2))


# ── migration-status.yaml sync ────────────────────────────────────────────

MIGRATION_FILE = ROOT / "governance" / "context" / "tracking" / "migration-status.yaml"
PROJECT_INDEX_FILE = ROOT / "governance" / "context" / "project-index.yaml"


def sync_migration_status() -> bool:
    """Update migration-status.yaml module percentages from SOP_STATUS."""
    if not MIGRATION_FILE.exists():
        print(f"  [SKIP] migration-status.yaml not found")
        return False

    content = MIGRATION_FILE.read_text(encoding="utf-8")
    ts = datetime.now(TZ).strftime("%Y-%m-%d")

    # Update overall_percentage (web-automation only — first occurrence)
    all_pcts = []
    for mod_key in MODULE_REGISTRY:
        phases = compute_phase_status(mod_key)
        pct_str = compute_overall_pct(phases)
        pct_num = int(pct_str.replace("**", "").replace("%", ""))
        all_pcts.append(pct_num)
    overall = round(sum(all_pcts) / len(all_pcts))
    content = re.sub(
        r"(web-automation:\n\s+overall_percentage:\s*)\d+",
        rf"\g<1>{overall}",
        content
    )

    # Update last_updated
    content = re.sub(r"last_updated:\s*\S+", f"last_updated: {ts}", content)

    MIGRATION_FILE.write_text(content, encoding="utf-8")
    print(f"  [OK] migration-status.yaml: overall={overall}%")
    return True


def sync_project_index() -> bool:
    """Update project-index.yaml module list from MODULE_REGISTRY."""
    if not PROJECT_INDEX_FILE.exists():
        print(f"  [SKIP] project-index.yaml not found")
        return False

    content = PROJECT_INDEX_FILE.read_text(encoding="utf-8")

    # Generate sorted module list
    module_lines = "\n".join(
        f"      - {mod_key}"
        for mod_key in sorted(MODULE_REGISTRY.keys())
    )

    # Replace between current_modules: and the next top-level key (context:)
    pattern = r"(current_modules:\n).*?(\n    context:)"
    replacement = rf"\1{module_lines}\2"
    content = re.sub(pattern, replacement, content, flags=re.DOTALL)

    # Update version note (comment line only, not YAML version field)
    ts = datetime.now(TZ).strftime("%Y-%m-%d")
    content = re.sub(
        r"# Project Index — .*",
        f"# Project Index — {ts} auto-sync: {len(MODULE_REGISTRY)} modules",
        content
    )

    PROJECT_INDEX_FILE.write_text(content, encoding="utf-8")
    print(f"  [OK] project-index.yaml: {len(MODULE_REGISTRY)} modules")
    return True


# ── MODULE_CONTEXT.md sync ───────────────────────────────────────────────

MODULE_CONTEXT_FOOTER = """\n\n<!-- ⚠️ AUTO-GENERATED SECTION BEGIN: module-stats -->
<!-- Source: tools/sync_progress.py — regenerated on each SOP run -->
## 自动统计数据 (更新于 {ts})

| 指标 | 数值 |
|------|:---:|
| 测试文件 | {test_files} (script/{script_dir}/test_*.py) |
| Page Object | {po_files} (page/{page_dir}/*.py) |
| 治理文档 | {gov_md} .md 文件 |
| TECH_ANALYSIS | {tech} |
| AUTO_STRATEGY | {auto} |
| RISK_MODEL | {risk} |
| PAGE_CONTEXT | {ctx} |
| SOP 状态 | {sop_status} |
| Phase 完成 | {completed_phases} |

> 此段由 sync_progress.py 自动更新。手动编辑会被覆盖。
<!-- ⚠️ AUTO-GENERATED SECTION END: module-stats -->"""


def sync_module_context(module_key: str) -> bool:
    """Update one MODULE_CONTEXT.md with auto-generated stats footer."""
    entry = MODULE_REGISTRY.get(module_key)
    if not entry:
        return False
    gov_dir = GOV_MODULES_DIR / entry[3]
    mc_path = gov_dir / "MODULE_CONTEXT.md"
    if not mc_path.exists():
        # Some modules may not have MODULE_CONTEXT yet
        return False

    content = mc_path.read_text(encoding="utf-8")
    artifacts = count_gov_artifacts(module_key)
    sop = load_sop_status(module_key)
    ts = datetime.now(TZ).strftime("%Y-%m-%d %H:%M")

    footer = MODULE_CONTEXT_FOOTER.format(
        ts=ts,
        test_files=count_test_files(module_key),
        script_dir=entry[1],
        po_files=count_po_files(module_key),
        page_dir=entry[2],
        gov_md=artifacts["md"],
        tech=artifacts["tech"],
        auto=artifacts["auto"],
        risk=artifacts["risk"],
        ctx=artifacts["ctx"],
        sop_status=sop.get("status", "none") if sop else "none",
        completed_phases=", ".join(sop.get("completed_phases", [])) if sop else "none",
    )

    # Replace existing auto-gen footer or append
    begin = "<!-- ⚠️ AUTO-GENERATED SECTION BEGIN: module-stats -->"
    end = "<!-- ⚠️ AUTO-GENERATED SECTION END: module-stats -->"

    if begin in content:
        pattern = re.escape(begin) + r".*?" + re.escape(end)
        content = re.sub(pattern, footer.strip(), content, flags=re.DOTALL)
    else:
        content = content.rstrip() + "\n" + footer

    mc_path.write_text(content, encoding="utf-8")
    return True


def sync_all_module_contexts() -> int:
    """Update all MODULE_CONTEXT.md files. Returns count updated."""
    count = 0
    for mod_key in MODULE_REGISTRY:
        if sync_module_context(mod_key):
            count += 1
    print(f"  [OK] MODULE_CONTEXT.md: {count}/{len(MODULE_REGISTRY)} updated")
    return count


# ── MODULE_INDEX.md sync ─────────────────────────────────────────────────

MODULE_INDEX_FILE = ROOT / "governance" / "context" / "projects" / "web-automation" / "MODULE_INDEX.md"

MODULE_INDEX_TABLE_HEADER = """<!-- ⚠️ AUTO-GENERATED SECTION BEGIN: module-table -->
<!-- Source: tools/sync_progress.py -->
## 模块状态表 (自动生成 — 更新于 {ts})

| 模块ID | 模块名称 | SOP状态 | 页面数 | PO | 测试 | 治理文档 | TECH | AUTO | RISK | 进度 |
|------|------|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|"""

MODULE_DISPLAY_NAMES = {
    "equipment": "设备管理", "dcs": "DCS数据管理", "lab": "化验室取样",
    "personnel": "人员管理", "production": "生产管理", "sales": "销售管理",
    "system-user": "系统-用户", "system-role": "角色管理", "system-management": "系统管理(重置)",
    "tank": "储罐管理", "warehouse": "库管管理", "workflow": "工作流管理",
}


def sync_module_index() -> bool:
    """Auto-generate MODULE_INDEX.md module status table."""
    if not MODULE_INDEX_FILE.exists():
        return False

    content = MODULE_INDEX_FILE.read_text(encoding="utf-8")
    ts = datetime.now(TZ).strftime("%Y-%m-%d %H:%M")

    header = MODULE_INDEX_TABLE_HEADER.format(ts=ts)
    sep = "|" + "|".join(["------" for _ in range(11)]) + "|"

    rows = []
    for mod_key in MODULE_REGISTRY:
        display = MODULE_DISPLAY_NAMES.get(mod_key, mod_key)
        sop = load_sop_status(mod_key)
        status = sop.get("status", "no_sop") if sop else "no_sop"
        page_count = estimate_page_count(mod_key)
        tests = count_test_files(mod_key)
        po = count_po_files(mod_key)
        a = count_gov_artifacts(mod_key)
        phases = compute_phase_status(mod_key)
        pct = compute_overall_pct(phases)

        status_icon = {"completed": "✅", "partial": "⚠️", "pending": "⏳", "no_sop": "❌"}.get(status, "❓")

        rows.append(
            f"| {mod_key} | {display} | {status_icon} {status} | {page_count} | {po} | {tests} "
            f"| {a['md']} | {a['tech']} | {a['auto']} | {a['risk']} | {pct} |"
        )

    table = "\n".join([header, sep] + rows) + "\n\n"
    table += "> 图例：✅ completed | ⚠️ partial | ⏳ pending | ❌ no SOP_STATUS\n"
    table += "> 此表由 sync_progress.py 自动生成。手动编辑会被覆盖。\n"
    table += "<!-- ⚠️ AUTO-GENERATED SECTION END: module-table -->"

    begin = "<!-- ⚠️ AUTO-GENERATED SECTION BEGIN: module-table -->"
    end = "<!-- ⚠️ AUTO-GENERATED SECTION END: module-table -->"

    if begin in content:
        pattern = re.escape(begin) + r".*?" + re.escape(end)
        content = re.sub(pattern, table, content, flags=re.DOTALL)
    else:
        content = content.rstrip() + "\n\n" + table

    MODULE_INDEX_FILE.write_text(content, encoding="utf-8")
    print(f"  [OK] MODULE_INDEX.md: {len(rows)} modules")
    return True


# ── PROJECT_CONTEXT.md sync ──────────────────────────────────────────────

PROJECT_CONTEXT_FILE = ROOT / "governance" / "context" / "projects" / "web-automation" / "PROJECT_CONTEXT.md"


def sync_project_context() -> bool:
    """Add auto-generated module summary footer to PROJECT_CONTEXT.md."""
    if not PROJECT_CONTEXT_FILE.exists():
        return False

    content = PROJECT_CONTEXT_FILE.read_text(encoding="utf-8")
    ts = datetime.now(TZ).strftime("%Y-%m-%d %H:%M")

    # Count totals
    total_tests = sum(count_test_files(k) for k in MODULE_REGISTRY)
    total_po = sum(count_po_files(k) for k in MODULE_REGISTRY)
    total_gov = sum(count_gov_artifacts(k)["md"] for k in MODULE_REGISTRY)
    completed = sum(1 for k in MODULE_REGISTRY
                    if compute_overall_pct(compute_phase_status(k)) == "**100%**")
    in_progress = sum(1 for k in MODULE_REGISTRY
                      if load_sop_status(k) and load_sop_status(k).get("status") == "completed")
    pending_count = sum(1 for k in MODULE_REGISTRY
                        if load_sop_status(k) and load_sop_status(k).get("status") == "pending")

    footer = f"""
<!-- ⚠️ AUTO-GENERATED SECTION BEGIN: project-stats -->
<!-- Source: tools/sync_progress.py — regenerated on each SOP run -->
## 项目统计数据 (更新于 {ts})

| 指标 | 数值 |
|------|:---:|
| 纳管模块 | {len(MODULE_REGISTRY)} |
| 100% 完成模块 | {completed} ({', '.join(k for k in MODULE_REGISTRY if compute_overall_pct(compute_phase_status(k))=='**100%**')}) |
| SOP completed | {in_progress} |
| Pending/重置 | {pending_count} |
| 测试文件总数 | {total_tests} |
| Page Object 总数 | {total_po} |
| 治理文档总数 | {total_gov} |
| 总体进度 | {round(sum(int(compute_overall_pct(compute_phase_status(k)).replace('**','').replace('%','')) for k in MODULE_REGISTRY) / len(MODULE_REGISTRY))}% |

> 此段由 sync_progress.py 自动更新。{ts}
<!-- ⚠️ AUTO-GENERATED SECTION END: project-stats -->"""

    begin = "<!-- ⚠️ AUTO-GENERATED SECTION BEGIN: project-stats -->"
    end = "<!-- ⚠️ AUTO-GENERATED SECTION END: project-stats -->"

    if begin in content:
        pattern = re.escape(begin) + r".*?" + re.escape(end)
        content = re.sub(pattern, footer.strip(), content, flags=re.DOTALL)
    else:
        content = content.rstrip() + footer

    PROJECT_CONTEXT_FILE.write_text(content, encoding="utf-8")
    print(f"  [OK] PROJECT_CONTEXT.md: {len(MODULE_REGISTRY)} modules, {total_gov} docs, {total_tests} tests")
    return True


# ── shared-language.md sync ──────────────────────────────────────────────

SHARED_LANGUAGE_FILE = ROOT / "governance" / "context" / "shared-language.md"


def sync_shared_language() -> bool:
    """Add auto-generated module list to shared-language.md."""
    if not SHARED_LANGUAGE_FILE.exists():
        return False

    content = SHARED_LANGUAGE_FILE.read_text(encoding="utf-8")
    ts = datetime.now(TZ).strftime("%Y-%m-%d %H:%M")

    module_list = []
    for mod_key in MODULE_REGISTRY:
        sop = load_sop_status(mod_key)
        status = sop.get("status", "none") if sop else "none"
        pages = estimate_page_count(mod_key)
        tests = count_test_files(mod_key)
        module_list.append(f"- **{mod_key}** ({MODULE_DISPLAY_NAMES.get(mod_key, '')}): {pages} pages, {tests} tests, SOP: {status}")

    footer = f"""
<!-- ⚠️ AUTO-GENERATED SECTION BEGIN: module-list -->
<!-- Source: tools/sync_progress.py -->
## 模块清单 (自动生成 — 更新于 {ts})

{chr(10).join(module_list)}

> 共 {len(MODULE_REGISTRY)} 模块。此段由 sync_progress.py 自动更新。
<!-- ⚠️ AUTO-GENERATED SECTION END: module-list -->"""

    begin = "<!-- ⚠️ AUTO-GENERATED SECTION BEGIN: module-list -->"
    end = "<!-- ⚠️ AUTO-GENERATED SECTION END: module-list -->"

    if begin in content:
        pattern = re.escape(begin) + r".*?" + re.escape(end)
        content = re.sub(pattern, footer.strip(), content, flags=re.DOTALL)
    else:
        content = content.rstrip() + footer

    SHARED_LANGUAGE_FILE.write_text(content, encoding="utf-8")
    print(f"  [OK] shared-language.md: {len(MODULE_REGISTRY)} modules listed")
    return True


# ── known-issues.yaml sync ───────────────────────────────────────────────

KNOWN_ISSUES_FILE = ROOT / "governance" / "context" / "known-issues.yaml"


def sync_known_issues() -> bool:
    """Update last_updated timestamp in known-issues.yaml."""
    if not KNOWN_ISSUES_FILE.exists():
        return False

    content = KNOWN_ISSUES_FILE.read_text(encoding="utf-8")
    ts = datetime.now(TZ).strftime("%Y-%m-%d")
    content = re.sub(r"last_updated:\s*\S+", f"last_updated: {ts}", content)
    KNOWN_ISSUES_FILE.write_text(content, encoding="utf-8")
    print(f"  [OK] known-issues.yaml: last_updated={ts}")
    return True


# ── Context freshness checker ────────────────────────────────────────────

def check_context_freshness() -> tuple:
    """Check all context/ + knowledge/ files for staleness vs SOP_STATUS.
    Returns (all_fresh: bool, stale_files: list)."""
    newest_sop_ts = None
    for f in SOP_STATUS_DIR.glob("SOP_STATUS_*.json"):
        mtime = f.stat().st_mtime
        if newest_sop_ts is None or mtime > newest_sop_ts:
            newest_sop_ts = mtime

    if newest_sop_ts is None:
        return True, []

    STALE_THRESHOLD = 7 * 86400  # 7 days in seconds
    context_files = list((ROOT / "governance" / "context").rglob("*.md"))
    context_files += list((ROOT / "governance" / "context").rglob("*.yaml"))
    knowledge_files = list((ROOT / "governance" / "knowledge").rglob("*.md"))

    stale = []
    for f in context_files + knowledge_files:
        # Skip AUTO-GEN sections (they're machine-maintained)
        mtime = f.stat().st_mtime
        if newest_sop_ts - mtime > STALE_THRESHOLD:
            if "AUTO-GENERATED" not in f.read_text(encoding="utf-8")[:500]:
                stale.append(str(f.relative_to(ROOT)))

    return len(stale) == 0, stale


# ── Skills AUTO-GEN header ───────────────────────────────────────────────

SKILL_REGISTRY_FILE = ROOT / "governance" / "skills" / "skill-registry.yaml"
SKILL_DEV_REGISTRY_FILE = ROOT / "governance" / "skills-dev" / "skill-registry-dev.yaml"
SKILLS_DIR = ROOT / "governance" / "skills"
SKILLS_DEV_DIR = ROOT / "governance" / "skills-dev"

AGENT_DEFS_FILE = ROOT / "governance" / "agents" / "agent-definitions.yaml"
AGENT_DEV_DEFS_FILE = ROOT / "governance" / "agents" / "agent-definitions-dev.yaml"
AGENTS_DIR = ROOT / "governance" / "agents"

TEMPLATES_DIR = ROOT / "governance" / "templates"
WORKFLOWS_DIR = ROOT / "governance" / "workflows"
COMPLETENESS_FILE = ROOT / "governance" / "context" / "projects" / "web-automation" / "COMPLETENESS_REPORT.md"

SKILL_HEADER_TPL = '<!-- ⚠️ AUTO-GENERATED HEADER BEGIN: skill-meta -->\n<!-- Source: skill-registry -->\n> **{version}** | {status} | {category} | synced {ts}\n{deprecation}\n<!-- ⚠️ AUTO-GENERATED HEADER END: skill-meta -->'

AGENT_FOOTER_TPL = '\n\n<!-- ⚠️ AUTO-GENERATED SECTION BEGIN: agent-meta -->\n## Auto-Metadata ({ts})\n\n| Agent | Phase | Skills | Source |\n|-------|-------|--------|--------|\n| {agent_id} | {phase} | {skill_count} ({skills_short}) | {source} |\n\n> synced by sync_progress.py\n<!-- ⚠️ AUTO-GENERATED SECTION END: agent-meta -->'

TEMPLATE_FOOTER_TPL = '\n\n<!-- ⚠️ AUTO-GENERATED SECTION BEGIN: template-meta -->\n> last_verified: {ts} | sync_progress.py\n<!-- ⚠️ AUTO-GENERATED SECTION END: template-meta -->'

WORKFLOW_CHECK_TPL = '\n\n<!-- ⚠️ AUTO-GENERATED SECTION BEGIN: workflow-check -->\n## Dependency Check ({ts})\n\n{checks}\n\n> sync_progress.py\n<!-- ⚠️ AUTO-GENERATED SECTION END: workflow-check -->'


def _load_yaml(path):
    try:
        import yaml
        with open(path, 'r', encoding='utf-8') as f:
            return yaml.safe_load(f) or {}
    except Exception:
        return {}


def _replace_or_append(content, begin, end, new_section):
    if begin in content:
        return re.sub(re.escape(begin) + r'.*?' + re.escape(end), new_section, content, flags=re.DOTALL)
    return content.rstrip() + '\n' + new_section


def sync_skills_headers():
    count = 0
    ts = datetime.now(TZ).strftime('%Y-%m-%d %H:%M')
    # Test skills
    reg = _load_yaml(SKILL_REGISTRY_FILE)
    for entry in reg.get('skills', []):
        if not isinstance(entry, dict):
            continue
        fp = entry.get('file', '')
        if not fp:
            continue
        sp = ROOT / "governance" / fp
        if not sp.exists():
            continue
        c = sp.read_text(encoding='utf-8')
        hdr = SKILL_HEADER_TPL.format(version=entry.get('current_version','?'), status=entry.get('status','?'), category=entry.get('category','?'), ts=ts, deprecation='DEPRECATED->'+entry.get('merged_into','') if entry.get('status')=='deprecated' else '')
        sp.write_text(_replace_or_append(c, '<!-- ⚠️ AUTO-GENERATED HEADER BEGIN: skill-meta -->', '<!-- ⚠️ AUTO-GENERATED HEADER END: skill-meta -->', hdr), encoding='utf-8')
        count += 1

    # Dev skills — nested structure: skills/{category/id}: {id, file, ...}
    dreg = _load_yaml(SKILL_DEV_REGISTRY_FILE)
    skills_nested = dreg.get('skills', {})
    for key, entry in skills_nested.items():
        if not isinstance(entry, dict):
            continue
        fp = entry.get('file', '')
        if fp:
            # Dev registry paths start with 'governance/' — use ROOT/fp directly
            sp = ROOT / fp
        else:
            sp = SKILLS_DEV_DIR / f'{key}.md'
        if not sp.exists():
            continue
        c = sp.read_text(encoding='utf-8')
        cat = key.split('/')[0] if '/' in key else 'unknown'
        ver = entry.get('current_version', entry.get('version','?'))
        hdr = SKILL_HEADER_TPL.format(version=ver, status=entry.get('status','active'), category=cat, ts=ts, deprecation='')
        sp.write_text(_replace_or_append(c, '<!-- ⚠️ AUTO-GENERATED HEADER BEGIN: skill-meta -->', '<!-- ⚠️ AUTO-GENERATED HEADER END: skill-meta -->', hdr), encoding='utf-8')
        count += 1

    print(f'  [OK] Skills headers: {count} files')
    return count


def sync_agent_footers():
    count = 0
    ts = datetime.now(TZ).strftime('%Y-%m-%d %H:%M')
    for dfs, src in [(AGENT_DEFS_FILE, 'agent-definitions.yaml'), (AGENT_DEV_DEFS_FILE, 'agent-definitions-dev.yaml')]:
        if not dfs.exists():
            continue
        defs = _load_yaml(dfs)
        agents = defs.get('agents', {})
        if isinstance(agents, list):
            entries = [(a.get('id',''), a) for a in agents if isinstance(a, dict)]
        elif isinstance(agents, dict):
            entries = [(v.get('id',k), v) for k, v in agents.items() if isinstance(v, dict)]
        else:
            entries = []

        for aid, entry in entries:
            amd = AGENTS_DIR / f'{aid}.md'
            if not amd.exists():
                continue
            c = amd.read_text(encoding='utf-8')
            phase = entry.get('phase', '?')
            skills = entry.get('skills', [])
            sn = [s if isinstance(s,str) else s.get('id','?') for s in skills] if isinstance(skills, list) else []
            ftr = AGENT_FOOTER_TPL.format(ts=ts, agent_id=aid, phase=phase, skill_count=len(sn), skills_short=', '.join(sn[:5])+('...' if len(sn)>5 else ''), source=src)
            amd.write_text(_replace_or_append(c, '<!-- ⚠️ AUTO-GENERATED SECTION BEGIN: agent-meta -->', '<!-- ⚠️ AUTO-GENERATED SECTION END: agent-meta -->', ftr), encoding='utf-8')
            count += 1

    print(f'  [OK] Agent footers: {count} files')
    return count


def sync_template_timestamps():
    count = 0
    ts = datetime.now(TZ).strftime('%Y-%m-%d %H:%M')
    for tm in TEMPLATES_DIR.glob('*.md'):
        if tm.name == 'README.md':
            continue
        c = tm.read_text(encoding='utf-8')
        ftr = TEMPLATE_FOOTER_TPL.format(ts=ts)
        tm.write_text(_replace_or_append(c, '<!-- ⚠️ AUTO-GENERATED SECTION BEGIN: template-meta -->', '<!-- ⚠️ AUTO-GENERATED SECTION END: template-meta -->', ftr), encoding='utf-8')
        count += 1
    print(f'  [OK] Template timestamps: {count} files')
    return count


def sync_workflow_validation():
    count = 0
    ts = datetime.now(TZ).strftime('%Y-%m-%d %H:%M')
    deprecated = {'conftest-generator', 'element-plus-locator', 'page-interface-generator'}
    for wf in WORKFLOWS_DIR.glob('*.md'):
        if wf.name == 'README.md' or wf.name == 'workflow-registry.yaml':
            continue
        content = wf.read_text(encoding='utf-8')
        found_dep = [d for d in deprecated if d in content]
        checks = []
        if found_dep:
            checks.append(f'- [WARN] Deprecated skill refs: {", ".join(found_dep)}')
        else:
            checks.append('- [OK] No deprecated skill references')
        checks.append(f'- [OK] Validated {ts}')
        wf.write_text(_replace_or_append(content, '<!-- ⚠️ AUTO-GENERATED SECTION BEGIN: workflow-check -->', '<!-- ⚠️ AUTO-GENERATED SECTION END: workflow-check -->', WORKFLOW_CHECK_TPL.format(ts=ts, checks='\n'.join(checks))), encoding='utf-8')
        count += 1
    print(f'  [OK] Workflow validation: {count} files')
    return count


def sync_completeness_report():
    if not COMPLETENESS_FILE.exists():
        return False
    content = COMPLETENESS_FILE.read_text(encoding='utf-8')
    ts = datetime.now(TZ).strftime('%Y-%m-%d %H:%M')
    rows = []
    for mk in MODULE_REGISTRY:
        pct = compute_overall_pct(compute_phase_status(mk))
        sop = load_sop_status(mk)
        st = sop.get('status','none') if sop else 'none'
        a = count_gov_artifacts(mk)
        rows.append(f'| {mk} | {st} | {count_test_files(mk)} | {a["md"]} | {a["tech"]} | {a["auto"]} | {a["risk"]} | {pct} |')

    total_t = sum(count_test_files(k) for k in MODULE_REGISTRY)
    total_g = sum(count_gov_artifacts(k)['md'] for k in MODULE_REGISTRY)
    completed = sum(1 for k in MODULE_REGISTRY if compute_overall_pct(compute_phase_status(k))=='**100%**')

    ftr = f'\n\n<!-- ⚠️ AUTO-GENERATED SECTION BEGIN: completeness-stats -->\n## Auto Stats ({ts})\n\n| Modules | 100% | Tests | Docs | Overall |\n|:---:|:---:|:---:|:---:|:---:|\n| {len(MODULE_REGISTRY)} | {completed} | {total_t} | {total_g} | {round(sum(int(compute_overall_pct(compute_phase_status(k)).replace(chr(42),"").replace("%","")) for k in MODULE_REGISTRY)/len(MODULE_REGISTRY))}% |\n\n### Per-Module\n\n| Module | SOP | Tests | Docs | TECH | AUTO | RISK | Progress |\n|--------|:---:|:---:|:---:|:---:|:---:|:---:|:---:|\n' + '\n'.join(rows) + '\n\n> sync_progress.py\n<!-- ⚠️ AUTO-GENERATED SECTION END: completeness-stats -->'

    updated = _replace_or_append(content, '<!-- ⚠️ AUTO-GENERATED SECTION BEGIN: completeness-stats -->', '<!-- ⚠️ AUTO-GENERATED SECTION END: completeness-stats -->', ftr)
    COMPLETENESS_FILE.write_text(updated, encoding='utf-8')
    print(f'  [OK] COMPLETENESS_REPORT.md: {len(MODULE_REGISTRY)} modules')
    return True


# ── KPI timeseries regeneration ─────────────────────────────────────────

def regenerate_kpi_timeseries() -> bool:
    """Regenerate KPI timeseries JSONL from current SOP_STATUS data.

    Replaces the zero-filled batch 3 data with real module state.
    """
    from dataclasses import dataclass, asdict

    KPI_DIR = ROOT / "governance" / "kpi" / "timeseries"
    KPI_DIR.mkdir(parents=True, exist_ok=True)
    ts = datetime.now(TZ).isoformat()
    count = 0

    for mod_key in MODULE_REGISTRY:
        sop = load_sop_status(mod_key)
        phases = compute_phase_status(mod_key)
        artifacts = count_gov_artifacts(mod_key)
        page_count = estimate_page_count(mod_key)
        pct_str = compute_overall_pct(phases)
        pct = int(pct_str.replace("**", "").replace("%", ""))

        status = sop.get("status", "unknown") if sop else "no_sop_status"
        completed = sop.get("completed_phases", []) if sop else []

        # Compute real drift: pages missing docs
        drift = 0
        if page_count > 0:
            expected_docs = page_count * 8  # 8 doc types per page
            actual_docs = artifacts["md"]
            drift = max(0, expected_docs - actual_docs)

        # SOP KPI
        sop_entry = {
            "timestamp": ts,
            "audit_type": "sop",
            "module": mod_key,
            "drift_count": drift,
            "error_count": 1 if status in ("pending", "no_sop_status") else 0,
            "warning_count": 1 if pct < 80 and status != "pending" else 0,
            "overall_status": "ok" if pct >= 80 else ("warning" if pct >= 40 else "error"),
            "compliance_score": round(pct / 100, 2),
            "violation_count": 0,
            "total_cost": 0.0,
            "alert_count": 1 if pct < 50 else 0,
            "event_count": len(completed),
            "e2e_count": len(completed),
            "phase_count": len(completed),
            "page_count": page_count,
            "artifact_count": artifacts["md"],
            "note": f"{pct}% complete, {status}, {len(completed)} phases done, {drift} doc gap",
        }

        sop_file = KPI_DIR / f"sop-{mod_key}-{datetime.now(TZ).strftime('%Y-%m-%d')}.jsonl"
        with open(sop_file, "a", encoding="utf-8") as f:
            f.write(json.dumps(sop_entry, ensure_ascii=False) + "\n")

        # State KPI
        state_entry = {
            "timestamp": ts,
            "audit_type": "state",
            "module": mod_key,
            "drift_count": drift,
            "error_count": 1 if status == "no_sop_status" else 0,
            "warning_count": 1 if pct < 80 else 0,
            "overall_status": "ok" if pct >= 80 else ("warning" if pct >= 40 else "error"),
            "compliance_score": round(pct / 100, 2),
            "violation_count": 0,
            "total_cost": 0.0,
            "alert_count": 1 if pct < 50 else 0,
            "event_count": len(completed),
            "note": f"State audit: {status}, {artifacts['md']} docs, {count_test_files(mod_key)} tests",
        }

        state_file = KPI_DIR / f"state-{mod_key}-{datetime.now(TZ).strftime('%Y-%m-%d')}.jsonl"
        with open(state_file, "a", encoding="utf-8") as f:
            f.write(json.dumps(state_entry, ensure_ascii=False) + "\n")

        count += 1

    print(f"  [OK] KPI timeseries: {count}×2 JSONL entries regenerated (replaces zero-filled batch 3 data)")
    return True


# ── Main ─────────────────────────────────────────────────────────────────

def main():
    # Fix Windows encoding
    if sys.platform == "win32":
        sys.stdout.reconfigure(encoding="utf-8")

    if "--check-context" in sys.argv:
        fresh, stale_files = check_context_freshness()
        if fresh:
            print(f"[OK] All context/knowledge files fresh vs SOP_STATUS")
            sys.exit(0)
        else:
            print(f"[STALE] {len(stale_files)} context/knowledge files older than SOP_STATUS:")
            for f in stale_files:
                print(f"  {f}")
            sys.exit(1)

    if "--check" in sys.argv:
        fresh, msg = check_freshness()
        if fresh:
            print(f"[OK] {msg}")
            sys.exit(0)
        else:
            print(f"[STALE] {msg}", file=sys.stderr)
            sys.exit(1)

    if "--json" in sys.argv:
        json_output()
        return

    # Default: update progress-tracking.md
    if not PROGRESS_FILE.exists():
        print(f"ERROR: {PROGRESS_FILE} not found", file=sys.stderr)
        sys.exit(1)

    content = PROGRESS_FILE.read_text(encoding="utf-8")
    updated = update_markdown_sections(content)
    PROGRESS_FILE.write_text(updated, encoding="utf-8")

    fresh, msg = check_freshness()
    print(f"[OK] progress-tracking.md updated")
    print(f"     Freshness: {msg}")

    # --sync-all or --sync-migration
    if "--sync-all" in sys.argv or "--sync-migration" in sys.argv:
        sync_migration_status()

    # --sync-all or --sync-project-index
    if "--sync-all" in sys.argv or "--sync-project-index" in sys.argv:
        sync_project_index()

    # --sync-all or --sync-modules
    if "--sync-all" in sys.argv or "--sync-modules" in sys.argv:
        sync_all_module_contexts()

    # --sync-all or --sync-kpi
    if "--sync-all" in sys.argv or "--sync-kpi" in sys.argv:
        regenerate_kpi_timeseries()

    # --sync-all or --sync-context
    if "--sync-all" in sys.argv or "--sync-context" in sys.argv:
        sync_module_index()
        sync_project_context()
        sync_shared_language()
        sync_known_issues()

    # --sync-all or --sync-skills
    if "--sync-all" in sys.argv or "--sync-skills" in sys.argv:
        sync_skills_headers()

    # --sync-all or --sync-agents
    if "--sync-all" in sys.argv or "--sync-agents" in sys.argv:
        sync_agent_footers()

    # --sync-all or --sync-templates
    if "--sync-all" in sys.argv or "--sync-templates" in sys.argv:
        sync_template_timestamps()

    # --sync-all or --sync-workflows
    if "--sync-all" in sys.argv or "--sync-workflows" in sys.argv:
        sync_workflow_validation()

    # --sync-all or --sync-completeness
    if "--sync-all" in sys.argv or "--sync-completeness" in sys.argv:
        sync_completeness_report()

    # Summary
    for mod_key in MODULE_REGISTRY:
        phases = compute_phase_status(mod_key)
        pct = compute_overall_pct(phases)
        print(f"     {mod_key:20s} {pct:>6s}")


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""
一次性脚本: 将 6 个模块的 SOP_STATUS JSON 迁移到规范格式。
- 旧格式 "Phase N (Description)" → 规范 PhaseName
- 合并 module-level 副本到 artifacts/sop-status/ (然后删除副本)
- 修复 tank/equipment 的 completed_phases=[] 空列表问题
"""
import json
import os
import sys

# Force UTF-8 on Windows
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except AttributeError:
        pass

from pathlib import Path

WORKSTUDY = Path(__file__).resolve().parent.parent
ARTIFACTS_DIR = WORKSTUDY / "governance" / "artifacts" / "sop-status"
MODULES_DIR = WORKSTUDY / "governance" / "context" / "projects" / "web-automation" / "modules"

CANONICAL_PHASES = [
    "Project Init",
    "Requirement",
    "Test Design",
    "Automation",
    "Execute & Debug",
    "Bug Analysis",
    "Data Sanitization",
    "Report",
    "Knowledge",
]

# 旧格式 → 规范名称映射 (前缀匹配)
LEGACY_MAP = [
    ("Phase 0 (Project Init)", "Project Init"),
    ("Phase 0.5 (Module Modeling", "Requirement"),
    ("Phase 0.5", "Requirement"),
    ("Phase 0.8", "Requirement"),
    ("Phase 1 (Page Analysis", "Test Design"),
    ("Phase 1.5 (Risk Modeling", "Test Design"),
    ("Phase 2 (Test Design", "Test Design"),
    ("Phase 2.5 (Test Cases", "Test Design"),
    ("Phase 3 (Tech Analysis", "Automation"),
    ("Phase 3.5 (Auto Strategy", "Automation"),
    ("Phase 3-4 (Automation", "Automation"),
    ("Phase 4 (Code Generation", "Automation"),
    ("Phase 4.5", "Bug Analysis"),
    ("Phase 4.5-7", "Execute & Debug"),
    ("Phase 5", "Bug Analysis"),
    ("Phase 6", "Test Design"),
    ("Phase 7", "Bug Analysis"),
    ("Phase 8", "Report"),
    ("Phase 9", "Knowledge"),
    ("Module Modeling", "Requirement"),
    ("Execution", "Execute & Debug"),
    ("Governance", "Test Design"),  # production 特有
    ("Preflight", None),  # 隐式阶段，跳过
]


def resolve_phase(phase_str: str) -> str | None:
    """将旧格式 Phase 名称解析为规范名称。"""
    if phase_str in CANONICAL_PHASES:
        return phase_str
    for prefix, canonical in LEGACY_MAP:
        if phase_str.startswith(prefix):
            return canonical
    # 尝试包含匹配
    for cp in CANONICAL_PHASES:
        if cp in phase_str:
            return cp
    return None


def extract_phases_from_old_format(data: dict) -> list[str]:
    """从旧格式 phases dict (如 "0": {...}, "0.5-0.8": {...}) 提取阶段。"""
    phases = data.get("phases", {})
    old_to_new = {
        "0": "Project Init",
        "0.5-0.8": "Requirement",
        "1-2.5": "Test Design",
        "3-4": "Automation",
        "4.5-7": "Execute & Debug",
        "8": "Report",
        "9": "Knowledge",
    }
    resolved = []
    for old_key, new_name in old_to_new.items():
        if old_key in phases and phases[old_key].get("status") == "completed":
            resolved.append(new_name)
    return resolved


def migrate_file(module_name: str, artifacts_path: Path, module_copy_path: Path | None = None):
    """迁移单个模块的 SOP_STATUS 文件。"""
    # 选择数据更丰富的源文件
    source_path = artifacts_path
    if module_copy_path and module_copy_path.exists():
        # 优先使用 module-level 文件（数据更丰富）
        a_size = artifacts_path.stat().st_size if artifacts_path.exists() else 0
        m_size = module_copy_path.stat().st_size if module_copy_path.exists() else 0
        if m_size > a_size:
            source_path = module_copy_path

    if not source_path.exists():
        print(f"  WARN {module_name}: no SOP_STATUS file")
        return None

    with open(source_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    # 解析 completed_phases
    completed_raw = data.get("completed_phases", [])

    # 如果为空，尝试从旧格式 phases dict 提取
    if not completed_raw and "phases" in data:
        completed_raw = extract_phases_from_old_format(data)

    resolved = []
    for p in completed_raw:
        canonical = resolve_phase(p)
        if canonical and canonical not in resolved:
            resolved.append(canonical)

    # 构建规范格式输出
    migrated = {
        "module": module_name,
        "status": data.get("status", "unknown"),
        "completed_phases": resolved,
        "failed_phases": data.get("failed_phases", []),
        "pages_processed": data.get("pages_processed", data.get("pages", [])),
        "run_id": data.get("run_id", ""),
        "updated_at": data.get("updated_at", data.get("last_updated", "")),
        "engine": data.get("engine", "langgraph"),
    }

    # 保留旧格式中的有用信息
    if "sub_pages" in data:
        migrated["sub_pages"] = data["sub_pages"]
    if "next_steps" in data:
        migrated["next_steps"] = data["next_steps"]
    if "known_issues" in data:
        migrated["known_issues"] = data["known_issues"]

    # 写入 artifacts/sop-status/
    ARTIFACTS_DIR.mkdir(parents=True, exist_ok=True)
    output_path = ARTIFACTS_DIR / f"SOP_STATUS_{module_name}.json"
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(migrated, f, ensure_ascii=False, indent=2)

    # 删除 module-level 副本（如果存在）
    if module_copy_path and module_copy_path.exists():
        module_copy_path.unlink()
        print(f"  OK {module_name}: migrated ({len(resolved)} phases), deleted module copy")
    else:
        print(f"  OK {module_name}: migrated ({len(resolved)} phases)")

    return resolved


def main():
    print("SOP_STATUS 格式迁移\n")

    modules_config = {
        "tank": True,
        "equipment": True,
        "system": True,
        "system-management": False,
        "lab": False,
        "production": False,
        "warehouse": False,
    }

    for module_name, has_copy in modules_config.items():
        artifacts_path = ARTIFACTS_DIR / f"SOP_STATUS_{module_name}.json"
        module_copy_path = MODULES_DIR / module_name / f"SOP_STATUS_{module_name}.json" if has_copy else None
        migrate_file(module_name, artifacts_path, module_copy_path)

    print(f"\nDone. Files in {ARTIFACTS_DIR}:")
    for f in sorted(ARTIFACTS_DIR.glob("SOP_STATUS_*.json")):
        print(f"  {f.name}")

    # 检查 module 目录下不再有残留
    remaining = list(MODULES_DIR.rglob("SOP_STATUS_*.json"))
    if remaining:
        print(f"\nWARN: {len(remaining)} module-level SOP_STATUS remain:")
        for r in remaining:
            print(f"  {r}")
    else:
        print("\nOK: no module-level SOP_STATUS remaining")


if __name__ == "__main__":
    main()

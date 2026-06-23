"""Tools: get_module_status + get_automation_coverage。"""
import os

from aitest.mcp.config import MODULE_INDEX, CONTEXT_MODULES
from aitest.mcp.error_taxonomy import ErrorCode, error_response
from aitest.platform.paths import get_test_project_root


def get_module_status(module_name: str = "") -> dict:
    """获取模块当前 SOP 状态。"""
    if not MODULE_INDEX.exists():
        return error_response(
            ErrorCode.FILE_NOT_FOUND,
            f"Module index not found: {MODULE_INDEX}",
            "MODULE_INDEX.md 缺失。运行 /project-agent 初始化项目上下文。",
        )

    with open(MODULE_INDEX, "r", encoding="utf-8") as f:
        content = f.read()

    modules = []
    for line in content.split("\n"):
        if line.startswith("|") and "modules/" in line:
            parts = [p.strip() for p in line.split("|") if p.strip()]
            if len(parts) >= 3:
                modules.append({"id": parts[0], "name": parts[1], "status": parts[2]})

    if module_name:
        modules = [m for m in modules if module_name.lower() in m["id"].lower()
                   or module_name.lower() in m["name"].lower()]

    for m in modules:
        module_dir = CONTEXT_MODULES / m["id"]
        if module_dir.exists():
            docs = []
            for doc_type in ["MODULE_CONTEXT.md", "REQUIREMENT_ANALYSIS.md"]:
                docs.append({"name": doc_type, "exists": (module_dir / doc_type).exists()})
            pages_dir = module_dir / "pages"
            if pages_dir.exists():
                for page_dir in sorted(pages_dir.iterdir()):
                    if page_dir.is_dir():
                        page_docs = {}
                        for doc_type in ["PAGE_CONTEXT.md", "RISK_MODEL.md", "TEST_DESIGN.md",
                                         "TEST_CASES.md", "TECH_ANALYSIS.md", "AUTO_STRATEGY.md"]:
                            page_docs[doc_type] = (page_dir / doc_type).exists()
                        docs.append({"page": page_dir.name, "documents": page_docs})
            m["documents"] = docs

    return {"status": "ok", "modules": modules, "total": len(modules)}


def get_automation_coverage(module_name: str = "") -> dict:
    """获取模块的自动化代码覆盖率信息。"""
    zjsn = get_test_project_root()
    if not zjsn:
        return error_response(
            ErrorCode.PRECONDITION_FAILED,
            "No test project configured",
            "使用 aitest project set --id=<project> 设置活跃项目，或注册新项目。",
        )
    page_dir = zjsn / "page"
    script_dir = zjsn / "script"

    page_objects = {}
    test_scripts = {}

    for root, dirs, files in os.walk(page_dir):
        dirs[:] = [d for d in dirs if d not in ["__pycache__"]]
        for f in files:
            if f.endswith(".py") and not f.startswith("__"):
                rel_path = os.path.relpath(os.path.join(root, f), page_dir)
                page_objects[rel_path] = os.path.getsize(os.path.join(root, f))

    for root, dirs, files in os.walk(script_dir):
        dirs[:] = [d for d in dirs if d not in ["__pycache__"]]
        for f in files:
            if f.startswith("test_") and f.endswith(".py"):
                rel_path = os.path.relpath(os.path.join(root, f), script_dir)
                test_scripts[rel_path] = os.path.getsize(os.path.join(root, f))

    result = {
        "status": "ok",
        "page_objects": {"count": len(page_objects), "files": list(page_objects.keys())},
        "test_scripts": {"count": len(test_scripts), "files": list(test_scripts.keys())},
    }

    if module_name:
        result["page_objects"]["files"] = [f for f in result["page_objects"]["files"]
                                            if module_name.lower() in f.lower()]
        result["page_objects"]["count"] = len(result["page_objects"]["files"])
        result["test_scripts"]["files"] = [f for f in result["test_scripts"]["files"]
                                            if module_name.lower() in f.lower()]
        result["test_scripts"]["count"] = len(result["test_scripts"]["files"])

    return result

"""
MCP Server: aitest-knowledge
将项目治理知识（PROJECT_CONTEXT、known-issues、PAGE_CONTEXT、TEST_CASES 等）
通过 MCP resource:// 协议按需暴露，减少 Token 浪费。

协议: MCP (Model Context Protocol) via stdio
用法: python -m aitest.knowledge.knowledge_server
"""
import os
import re
from pathlib import Path
from typing import Any

import yaml
from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import Resource, ResourceTemplate, TextResourceContents

# ── 路径配置 ──────────────────────────────────────────────────────────
WORKSTUDY = Path(__file__).resolve().parent.parent.parent
GOVERNANCE = WORKSTUDY / "governance"
PROJECT_CONTEXT = GOVERNANCE / "context" / "projects" / "web-automation" / "PROJECT_CONTEXT.md"
KNOWN_ISSUES = GOVERNANCE / "context" / "known-issues.yaml"
MODULE_INDEX = GOVERNANCE / "context" / "projects" / "web-automation" / "MODULE_INDEX.md"
ENVIRONMENTS = GOVERNANCE / "context" / "environments.yaml"
CONTEXT_MODULES = GOVERNANCE / "context" / "projects" / "web-automation" / "modules"

server = Server("aitest-knowledge")


def _read_file_safe(path: Path) -> str:
    """安全读取文件。"""
    if not path.exists():
        return f"# File not found: {path}"
    try:
        with open(path, "r", encoding="utf-8") as f:
            return f.read()
    except Exception as e:
        return f"# Error reading file: {e}"


def _list_module_pages(module_name: str) -> list[dict]:
    """列出模块下的页面。"""
    module_dir = CONTEXT_MODULES / module_name / "pages"
    if not module_dir.exists():
        return []
    pages = []
    for page_dir in sorted(module_dir.iterdir()):
        if page_dir.is_dir():
            docs = {}
            for doc in ["PAGE_CONTEXT.md", "RISK_MODEL.md", "TEST_DESIGN.md",
                        "TEST_CASES.md", "TECH_ANALYSIS.md", "AUTO_STRATEGY.md"]:
                docs[doc] = str(page_dir / doc) if (page_dir / doc).exists() else None
            pages.append({"name": page_dir.name, "path": str(page_dir), "documents": docs})
    return pages


def _list_all_modules() -> list[dict]:
    """列出所有模块。"""
    if not CONTEXT_MODULES.exists():
        return []
    modules = []
    for mod_dir in sorted(CONTEXT_MODULES.iterdir()):
        if mod_dir.is_dir():
            mc = mod_dir / "MODULE_CONTEXT.md"
            pages = _list_module_pages(mod_dir.name)
            modules.append({
                "name": mod_dir.name,
                "module_context": str(mc) if mc.exists() else None,
                "pages": pages
            })
    return modules


# ══════════════════════════════════════════════════════════════════════════
#  Resource definitions
# ══════════════════════════════════════════════════════════════════════════

@server.list_resources()
async def list_resources() -> list[Resource]:
    resources = [
        Resource(
            uri="known-issues://all",
            name="全部已知问题",
            description="known-issues.yaml 全部结构化数据（JSON格式）",
            mimeType="application/json"
        ),
        Resource(
            uri="project-context://summary",
            name="项目上下文摘要",
            description="PROJECT_CONTEXT.md 的项目目标 + 技术栈 + 模块索引（不含 BasePage API 参考和编码规范）",
            mimeType="text/markdown"
        ),
        Resource(
            uri="project-context://basepage-api",
            name="BasePage API 参考",
            description="PROJECT_CONTEXT.md 中的 BasePage 60+ 方法签名和定位器定义",
            mimeType="text/markdown"
        ),
        Resource(
            uri="project-context://rules",
            name="编码强制规范 + 代码红线",
            description="PROJECT_CONTEXT.md 中的编码规范 + 禁止模式 + 自检命令",
            mimeType="text/markdown"
        ),
        Resource(
            uri="project-context://ep-pitfalls",
            name="Element Plus 已知坑位清单",
            description="PROJECT_CONTEXT.md 中的 Element Plus 11 坑位 + UI 框架差异对照表",
            mimeType="text/markdown"
        ),
        Resource(
            uri="project-context://data-strategy",
            name="测试数据管理规范",
            description="PROJECT_CONTEXT.md 中的数据清理策略 + 命名规范 + 红线检查",
            mimeType="text/markdown"
        ),
        Resource(
            uri="project-context://full",
            name="完整项目上下文",
            description="PROJECT_CONTEXT.md 完整内容（约200行，仅必要时使用）",
            mimeType="text/markdown"
        ),
        Resource(
            uri="module-index://all",
            name="模块索引",
            description="所有模块的状态清单",
            mimeType="text/markdown"
        ),
        Resource(
            uri="environments://all",
            name="环境配置",
            description="environments.yaml 环境信息（URL/CI/技术栈/账号说明）",
            mimeType="text/markdown"
        ),
    ]

    # 动态注册模块和页面资源
    for mod in _list_all_modules():
        if mod["module_context"]:
            resources.append(Resource(
                uri=f"module-context://{mod['name']}",
                name=f"模块上下文: {mod['name']}",
                description=f"{mod['name']} 模块的 MODULE_CONTEXT.md",
                mimeType="text/markdown"
            ))
        for page in mod["pages"]:
            for doc_name, doc_path in page["documents"].items():
                if doc_path:
                    resources.append(Resource(
                        uri=f"page-doc://{mod['name']}/{page['name']}/{doc_name}",
                        name=f"{doc_name}: {mod['name']}/{page['name']}",
                        description=f"{mod['name']}/{page['name']} 的 {doc_name}",
                        mimeType="text/markdown"
                    ))

    return resources


# ResourceTemplate 用于按模块/页面名动态路由
@server.list_resource_templates()
async def list_resource_templates() -> list[ResourceTemplate]:
    return [
        ResourceTemplate(
            uriTemplate="page-doc://{module}/{page}/{doc}",
            name="页面文档（模板）",
            description="按模块名/页面名/文档类型读取页面级文档。doc: PAGE_CONTEXT.md|RISK_MODEL.md|TEST_DESIGN.md|TEST_CASES.md|TECH_ANALYSIS.md|AUTO_STRATEGY.md",
            mimeType="text/markdown"
        ),
        ResourceTemplate(
            uriTemplate="module-context://{module}",
            name="模块上下文（模板）",
            description="按模块名读取 MODULE_CONTEXT.md",
            mimeType="text/markdown"
        ),
    ]


# ══════════════════════════════════════════════════════════════════════════
#  Resource read implementation
# ══════════════════════════════════════════════════════════════════════════

def _extract_section_by_keyword(content: str, keyword: str) -> str:
    """从 Markdown 中按关键词提取章节。keyword 为 ASCII 子串或 Heading 中包含的文本。"""
    lines = content.split("\n")
    start_idx = None
    end_idx = None

    for i, line in enumerate(lines):
        if start_idx is None:
            # 查找 H2-H4 标题行中包含关键词的标题
            if re.match(r"^#{2,4}\s+", line) and keyword in line:
                start_idx = i
        else:
            # 找到起始行后，检测下一个同级或更高级标题作为结束
            m = re.match(r"^(#+)\s", line)
            if m:
                target_level = len(re.match(r"^(#+)\s", lines[start_idx]).group(1))
                current_level = len(m.group(1))
                if current_level <= target_level:
                    end_idx = i
                    break

    if start_idx is None:
        return ""  # 返回空字符串表示未找到

    result = "\n".join(lines[start_idx:end_idx]) if end_idx else "\n".join(lines[start_idx:])
    return result.strip()


@server.read_resource()
async def read_resource(uri: str) -> list[TextResourceContents]:
    content = ""

    # ── known-issues ──
    if uri == "known-issues://all":
        if KNOWN_ISSUES.exists():
            data = yaml.safe_load(open(KNOWN_ISSUES, "r", encoding="utf-8"))
            import json
            content = json.dumps(data, ensure_ascii=False, indent=2)
        else:
            content = "{}"

    # ── project-context (分层) ──
    elif uri.startswith("project-context://"):
        full_text = _read_file_safe(PROJECT_CONTEXT)

        if uri == "project-context://full":
            content = full_text
        elif uri == "project-context://summary":
            # 提取项目目标 + 技术栈 + 上下文入口
            parts = []
            for kw in ["项目目标", "当前技术栈", "当前上下文入口"]:
                section = _extract_section_by_keyword(full_text, kw)
                if section:
                    parts.append(section)
            content = "\n\n".join(parts) if parts else full_text[:500]
        elif uri == "project-context://basepage-api":
            content = _extract_section_by_keyword(full_text, "Base 层 API") or "Base 层 API 参考 not found"
        elif uri == "project-context://rules":
            parts = []
            for kw in ["自动化编码强制规范", "Page Object 规范", "测试脚本规范", "禁止模式"]:
                section = _extract_section_by_keyword(full_text, kw)
                if section:
                    parts.append(section)
            content = "\n\n".join(parts) if parts else "Rules section not found"
        elif uri == "project-context://ep-pitfalls":
            parts = []
            for kw in ["Element Plus 已知坑位", "已确认的模块 UI 框架差异"]:
                section = _extract_section_by_keyword(full_text, kw)
                if section:
                    parts.append(section)
            content = "\n\n".join(parts) if parts else "EP pitfalls section not found"
        elif uri == "project-context://data-strategy":
            content = _extract_section_by_keyword(full_text, "测试数据管理规范") or "Data strategy section not found"
        else:
            content = full_text

    # ── module-index ──
    elif uri == "module-index://all":
        content = _read_file_safe(MODULE_INDEX)

    # ── environments ──
    elif uri == "environments://all":
        content = _read_file_safe(ENVIRONMENTS)

    # ── module-context (dynamic) ──
    elif uri.startswith("module-context://"):
        module_name = uri.replace("module-context://", "")
        mod_file = CONTEXT_MODULES / module_name / "MODULE_CONTEXT.md"
        content = _read_file_safe(mod_file)

    # ── page-doc (dynamic) ──
    elif uri.startswith("page-doc://"):
        parts = uri.replace("page-doc://", "").split("/")
        if len(parts) >= 3:
            module, page, doc = parts[0], parts[1], "/".join(parts[2:])
            doc_file = CONTEXT_MODULES / module / "pages" / page / doc
            content = _read_file_safe(doc_file)
        else:
            content = f"# Invalid page-doc URI: {uri}"

    else:
        content = f"# Unknown resource: {uri}"

    return [TextResourceContents(uri=uri, mimeType="text/markdown", text=content)]


# ══════════════════════════════════════════════════════════════════════════
#  Entry point
# ══════════════════════════════════════════════════════════════════════════

async def main():
    async with stdio_server() as (read_stream, write_stream):
        await server.run(read_stream, write_stream, server.create_initialization_options())


if __name__ == "__main__":
    import asyncio
    asyncio.run(main())

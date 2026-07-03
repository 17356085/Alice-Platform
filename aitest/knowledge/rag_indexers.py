"""RAG Indexers — indexing functions for ChromaDB.

Extracted from rag_engine.py for single-responsibility.
"""

import logging
from pathlib import Path

import chromadb

from aitest.knowledge.rag_engine import (
    chunk_markdown_by_headings, _read_file_safe, get_chroma_client,
)

logger = logging.getLogger(__name__)


def _ensure_known_issues_synced(client: chromadb.PersistentClient = None) -> bool:
    """
    P2-1: 自动检测 known-issues.yaml 是否变更，按需重建 ChromaDB 索引。

    known-issues.yaml 是单一事实源。ChromaDB 是只读向量索引。
    此函数在每次 search_known_issues() 调用前自动执行，
    仅在 YAML 文件变更时触发重建。

    返回: True 如果执行了同步，False 如果已是最新。
    """
    global _known_issues_mtime

    if not KNOWN_ISSUES.exists():
        return False

    current_mtime = KNOWN_ISSUES.stat().st_mtime
    if current_mtime <= _known_issues_mtime:
        return False  # 未变更，跳过

    # YAML 已变更 → 重建索引
    count = index_known_issues(client)
    _known_issues_mtime = current_mtime
    import logging
    logging.getLogger("aitest.rag").info(
        f"P2-1 auto-sync: known_issues ChromaDB rebuilt ({count} docs, mtime={current_mtime})"
    )
    return True


# P2-8: tech_analysis / page_context 增量索引 — 基于文件 mtime 按需重建
_tech_analysis_mtime: float = 0.0
_page_context_mtime: float = 0.0



def _ensure_tech_analysis_synced(client = None) -> bool:
    """
    P2-8: 自动检测所有 TECH_ANALYSIS.md 是否有变更，按需重建 ChromaDB 索引。

    返回: True 如果执行了同步，False 如果已是最新。
    """
    global _tech_analysis_mtime

    latest_mtime = 0.0
    for ta_file in sorted(MODULES_DIR.glob("**/TECH_ANALYSIS.md")):
        mtime = ta_file.stat().st_mtime
        if mtime > latest_mtime:
            latest_mtime = mtime

    if latest_mtime <= _tech_analysis_mtime and _tech_analysis_mtime > 0:
        return False

    count = index_tech_analysis(client)
    _tech_analysis_mtime = latest_mtime
    import logging
    logging.getLogger("aitest.rag").info(
        f"P2-8 auto-sync: tech_analysis ChromaDB rebuilt ({count} docs)"
    )
    return True



def _ensure_page_context_synced(client = None) -> bool:
    """
    P2-8: 自动检测所有 PAGE_CONTEXT.md 是否有变更，按需重建 ChromaDB 索引。

    返回: True 如果执行了同步，False 如果已是最新。
    """
    global _page_context_mtime

    latest_mtime = 0.0
    for pc_file in sorted(MODULES_DIR.glob("**/PAGE_CONTEXT.md")):
        mtime = pc_file.stat().st_mtime
        if mtime > latest_mtime:
            latest_mtime = mtime

    if latest_mtime <= _page_context_mtime and _page_context_mtime > 0:
        return False

    count = index_page_context(client)
    _page_context_mtime = latest_mtime
    import logging
    logging.getLogger("aitest.rag").info(
        f"P2-8 auto-sync: page_context ChromaDB rebuilt ({count} docs)"
    )
    return True


# ══════════════════════════════════════════════════════════════════════════
#  索引管线
# ══════════════════════════════════════════════════════════════════════════


def index_known_issues(client: chromadb.PersistentClient = None) -> int:
    """索引 known-issues.yaml 的每条问题为独立文档。"""
    global _known_issues_mtime
    if client is None:
        client = get_chroma_client()

    import yaml
    data = yaml.safe_load(_read_file_safe(KNOWN_ISSUES))
    issues = data.get("issues", [])

    try:
        client.delete_collection("known_issues")
    except Exception as e:
        from aitest.infra.error_logger import log_error
        log_error("rag_engine.index_known_issues", "delete_collection", e, {"collection": "known_issues"})

    collection = client.create_collection(
        name="known_issues",
        metadata={"description": "Element Plus 坑位 + 失败模式 + 环境问题"}
    )

    yaml_mtime = int(KNOWN_ISSUES.stat().st_mtime) if KNOWN_ISSUES.exists() else 0

    docs, ids, metadatas = [], [], []
    for issue in issues:
        # 构造可检索文本：标题 + 症状 + 根因 + 解决方案
        searchable = (
            f"[{issue.get('id')}] {issue.get('title', '')}\n"
            f"组件: {issue.get('component', '')}\n"
            f"症状: {'; '.join(issue.get('symptoms', []))}\n"
            f"根因: {issue.get('root_cause', '')}\n"
            f"方案: {issue.get('solution', '')}\n"
            f"影响模块: {', '.join(issue.get('affected_modules', []))}"
        )
        docs.append(searchable)
        ids.append(issue.get("id", f"unknown-{len(ids)}"))
        metadatas.append({
            "id": issue.get("id", ""),
            "title": issue.get("title", ""),
            "category": issue.get("category", ""),
            "component": issue.get("component", ""),
            "severity": issue.get("severity", ""),
            "status": issue.get("status", ""),
            "reproduce_rate": issue.get("reproduce_rate", 0),
            "occurrence_count": issue.get("occurrence_count", 0),
            "type": "known_issue",
            "update_time": yaml_mtime,
        })

    collection.add(documents=docs, ids=ids, metadatas=metadatas)

    # P2-1: 记录同步时间戳，供 _ensure_known_issues_synced() 使用
    if KNOWN_ISSUES.exists():
        global _known_issues_mtime
        _known_issues_mtime = KNOWN_ISSUES.stat().st_mtime

    return len(docs)



def index_project_context(client: chromadb.PersistentClient = None) -> int:
    """索引 PROJECT_CONTEXT.md，按 ## 标题分块。"""
    if client is None:
        client = get_chroma_client()

    text = _read_file_safe(PROJECT_CONTEXT)
    chunks = chunk_markdown_by_headings(text, {
        "source": "PROJECT_CONTEXT.md",
        "type": "project_context",
        "title": "Web Automation Project Context"
    })

    try:
        client.delete_collection("project_context")
    except Exception as e:
        from aitest.infra.error_logger import log_error
        log_error("rag_engine.index_project_context", "delete_collection", e, {"collection": "project_context"})

    collection = client.create_collection(
        name="project_context",
        metadata={"description": "PROJECT_CONTEXT.md 分层块"}
    )

    docs, ids, metadatas = [], [], []
    for i, chunk in enumerate(chunks):
        docs.append(chunk["text"])
        ids.append(f"pc-{i:03d}")
        metadatas.append({
            "source": chunk["source"],
            "type": chunk["type"],
            "heading": chunk["heading"],
            "chunk_index": i
        })

    collection.add(documents=docs, ids=ids, metadatas=metadatas)
    return len(docs)



def index_tech_analysis(client: chromadb.PersistentClient = None) -> int:
    """索引所有 TECH_ANALYSIS.md 文件。"""
    if client is None:
        client = get_chroma_client()

    try:
        client.delete_collection("tech_analysis")
    except Exception as e:
        from aitest.infra.error_logger import log_error
        log_error("rag_engine.index_tech_analysis", "delete_collection", e, {"collection": "tech_analysis"})

    collection = client.create_collection(
        name="tech_analysis",
        metadata={"description": "TECH_ANALYSIS.md — 定位器设计 + 等待策略 + Element Plus 组件识别"}
    )

    docs, ids, metadatas = [], [], []
    idx = 0

    for ta_file in sorted(MODULES_DIR.glob("**/TECH_ANALYSIS.md")):
        text = _read_file_safe(ta_file)
        if not text:
            continue

        # 提取模块/页面名
        parts = ta_file.relative_to(MODULES_DIR).parts
        module_name = parts[0] if len(parts) > 0 else "unknown"
        page_name = parts[2] if len(parts) > 2 and parts[1] == "pages" else "unknown"
        file_mtime = int(ta_file.stat().st_mtime)

        # 添加模块/页面元数据到头信息
        meta = {
            "source": str(ta_file.relative_to(GOVERNANCE)),
            "type": "tech_analysis",
            "module": module_name,
            "page": page_name,
            "title": f"TECH_ANALYSIS — {module_name}/{page_name}",
            "update_time": file_mtime,
        }

        chunks = chunk_markdown_by_headings(text, meta)
        for chunk in chunks:
            docs.append(chunk["text"])
            ids.append(f"ta-{idx:04d}")
            metadatas.append({
                "source": meta["source"],
                "type": meta["type"],
                "module": module_name,
                "page": page_name,
                "heading": chunk["heading"],
                "chunk_index": idx,
                "update_time": file_mtime,
            })
            idx += 1

    collection.add(documents=docs, ids=ids, metadatas=metadatas)
    return len(docs)



def index_page_context(client: chromadb.PersistentClient = None) -> int:
    """索引所有 PAGE_CONTEXT.md 文件。"""
    if client is None:
        client = get_chroma_client()

    try:
        client.delete_collection("page_context")
    except Exception as e:
        from aitest.infra.error_logger import log_error
        log_error("rag_engine.index_page_context", "delete_collection", e, {"collection": "page_context"})

    collection = client.create_collection(
        name="page_context",
        metadata={"description": "PAGE_CONTEXT.md — 页面元素清单"}
    )

    docs, ids, metadatas = [], [], []
    idx = 0

    for pc_file in sorted(MODULES_DIR.glob("**/PAGE_CONTEXT.md")):
        text = _read_file_safe(pc_file)
        if not text:
            continue

        parts = pc_file.relative_to(MODULES_DIR).parts
        module_name = parts[0]
        page_name = parts[2] if len(parts) > 2 and parts[1] == "pages" else "unknown"
        file_mtime = int(pc_file.stat().st_mtime)

        meta = {
            "source": str(pc_file.relative_to(GOVERNANCE)),
            "type": "page_context",
            "module": module_name,
            "page": page_name,
            "title": f"PAGE_CONTEXT — {module_name}/{page_name}",
            "update_time": file_mtime,
        }

        chunks = chunk_markdown_by_headings(text, meta)
        for chunk in chunks:
            docs.append(chunk["text"])
            ids.append(f"pc-{idx:04d}")
            metadatas.append({
                "source": meta["source"],
                "type": meta["type"],
                "module": module_name,
                "page": page_name,
                "heading": chunk["heading"],
                "chunk_index": idx,
                "update_time": file_mtime,
            })
            idx += 1

    collection.add(documents=docs, ids=ids, metadatas=metadatas)
    return len(docs)



def index_page_objects(client: chromadb.PersistentClient = None) -> int:
    """索引所有 Page Object .py 文件（方法签名 + 定位器 + 注释）。"""
    if client is None:
        client = get_chroma_client()

    try:
        client.delete_collection("page_objects")
    except Exception as e:
        from aitest.infra.error_logger import log_error
        log_error("rag_engine.index_page_objects", "delete_collection", e, {"collection": "page_objects"})

    collection = client.create_collection(
        name="page_objects",
        metadata={"description": "Page Object .py — 定位器写法 + 方法签名 + 等待策略示例"}
    )

    zjsn = get_test_project_root()
    if not zjsn:
        raise RuntimeError(
            "No test project configured. "
            "Use aitest project set --id=<project> to configure an active project."
        )
    page_dir = zjsn / "page"
    docs, ids, metadatas = [], [], []
    idx = 0

    for po_file in sorted(page_dir.glob("**/*.py")):
        if po_file.name.startswith("__"):
            continue
        text = _read_file_safe(po_file)
        if not text or len(text) < 50:
            continue

        # 提取模块名（从路径）
        rel_path = po_file.relative_to(page_dir)
        parts = rel_path.parts
        module_name = parts[0] if len(parts) > 0 else "unknown"

        # 提取类名和方法名作为元数据
        class_match = __import__("re").search(r"class\s+(\w+)", text)
        class_name = class_match.group(1) if class_match else "Unknown"

        methods = __import__("re").findall(r"def\s+(\w+)", text)
        locators = __import__("re").findall(r'(\w+)\s*=\s*\(By\.\w+,\s*["\'](.+?)["\']\)', text)

        # 用代码文本作为检索文档
        docs.append(text[:3000])  # 截断前3000字符
        ids.append(f"po-{idx:04d}")
        metadatas.append({
            "source": str(rel_path),
            "type": "page_object",
            "module": module_name,
            "class": class_name,
            "file": po_file.name,
            "methods": ", ".join(methods[:20]),
            "locator_count": len(locators),
            "update_time": int(po_file.stat().st_mtime),
        })
        idx += 1

    collection.add(documents=docs, ids=ids, metadatas=metadatas)
    return len(docs)



def index_all() -> dict:
    """全量索引构建。返回各集合的文档数。"""
    client = get_chroma_client()
    results = {}
    results["known_issues"] = index_known_issues(client)
    results["project_context"] = index_project_context(client)
    results["tech_analysis"] = index_tech_analysis(client)
    results["page_context"] = index_page_context(client)
    results["page_objects"] = index_page_objects(client)
    return results


# ══════════════════════════════════════════════════════════════════════════
#  检索接口
# ══════════════════════════════════════════════════════════════════════════


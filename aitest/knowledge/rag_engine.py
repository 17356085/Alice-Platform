"""
RAG Engine — 向量检索增强生成

功能:
  1. 索引管线: PROJECT_CONTEXT + known-issues + TECH_ANALYSIS + PAGE_CONTEXT
  2. 检索接口: bug-analysis 自动匹配已知问题 / 上下文按需检索
  3. 分块策略: Markdown 按 ## 标题分块 + 元数据标注

依赖: chromadb, sentence-transformers (可选，ChromaDB 内置 ONNX)
数据目录: governance/.chroma/
"""
import os
import re
import json
from pathlib import Path
from typing import Optional

import chromadb
from chromadb.config import Settings

# ── 距离阈值 ──────────────────────────────────────────────────────────
# 向量距离超过此值的结果被过滤（ChromaDB L2 distance，越小越相关）
RAG_DISTANCE_THRESHOLD = 1.5

# ── 路径配置 ──────────────────────────────────────────────────────────
WORKSTUDY = Path(__file__).resolve().parent.parent.parent
GOVERNANCE = WORKSTUDY / "governance"
CHROMA_DIR = GOVERNANCE / ".chroma"
PROJECT_CONTEXT = GOVERNANCE / "context" / "projects" / "web-automation" / "PROJECT_CONTEXT.md"
KNOWN_ISSUES = GOVERNANCE / "context" / "known-issues.yaml"
MODULES_DIR = GOVERNANCE / "context" / "projects" / "web-automation" / "modules"

# ── 分块工具 ──────────────────────────────────────────────────────────

def chunk_markdown_by_headings(text: str, base_meta: dict, min_chunk_size: int = 100) -> list[dict]:
    """按 ## 标题分割 Markdown，返回带元数据的块列表。"""
    lines = text.split("\n")
    chunks = []
    current_heading = base_meta.get("title", "Untitled")
    current_lines = []

    for line in lines:
        if re.match(r"^##\s+", line) and current_lines and len("\n".join(current_lines).strip()) >= min_chunk_size:
            chunk_text = "\n".join(current_lines).strip()
            if len(chunk_text) >= min_chunk_size:
                chunks.append({**base_meta, "heading": current_heading, "text": chunk_text})
            current_heading = line.strip().lstrip("#").strip()
            current_lines = [line]
        else:
            current_lines.append(line)

    # 最后一个块
    if current_lines:
        chunk_text = "\n".join(current_lines).strip()
        if len(chunk_text) >= min_chunk_size:
            chunks.append({**base_meta, "heading": current_heading, "text": chunk_text})

    return chunks


def _read_file_safe(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except Exception as e:
        from aitest.infra.error_logger import log_error
        log_error("rag_engine._read_file_safe", "read_file", e, {"path": str(path)})
        return ""


# ── ChromaDB 客户端 ───────────────────────────────────────────────────

def get_chroma_client() -> chromadb.PersistentClient:
    """获取 ChromaDB 持久化客户端。"""
    CHROMA_DIR.mkdir(parents=True, exist_ok=True)
    return chromadb.PersistentClient(
        path=str(CHROMA_DIR),
        settings=Settings(anonymized_telemetry=False)
    )


# ══════════════════════════════════════════════════════════════════════════
#  P2-1: YAML → ChromaDB 自动同步
# ══════════════════════════════════════════════════════════════════════════

_known_issues_mtime: float = 0.0  # 上次同步时 YAML 的 mtime


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

    page_dir = WORKSTUDY / "ZJSN_Test-master526" / "page"
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

def search_known_issues(query: str, n_results: int = 5,
                        category: str = None, severity: str = None,
                        client = None) -> list[dict]:
    """搜索已知问题 — bug-analysis 自动匹配入口。

    参数:
        query: 错误描述/异常类型/报错信息
        n_results: 返回结果数
        category: 按类别筛选 (element-plus/failure-pattern/environment)
        severity: 按严重度筛选 (high/medium/low)
        client: P0-2: 可选 ChromaDB PersistentClient（复用避免重复创建连接）
    """
    if client is None:
        client = get_chroma_client()

    # P2-1: 自动同步 — 检测 YAML 变更并按需重建 ChromaDB 索引
    _ensure_known_issues_synced(client)

    try:
        collection = client.get_collection("known_issues")
    except Exception as e:
        from aitest.infra.error_logger import log_error
        log_error("rag_engine.search_known_issues", "get_collection", e, {"collection": "known_issues"})
        return []

    # 构建 where 过滤条件
    where = None
    conditions = []
    if category:
        conditions.append({"category": category})
    if severity:
        conditions.append({"severity": severity})
    if len(conditions) == 1:
        where = conditions[0]
    elif len(conditions) > 1:
        where = {"$and": conditions}

    try:
        results = collection.query(
            query_texts=[query],
            n_results=min(n_results, collection.count()),
            where=where
        )
    except Exception as e:
        from aitest.infra.error_logger import log_error
        log_error("rag_engine.search_known_issues", "query", e, {"query": query[:100]})
        return []

    output = []
    if results["ids"] and results["ids"][0]:
        for i, doc_id in enumerate(results["ids"][0]):
            output.append({
                "id": doc_id,
                "document": results["documents"][0][i] if results["documents"] else "",
                "metadata": results["metadatas"][0][i] if results["metadatas"] else {},
                "distance": results["distances"][0][i] if results["distances"] else None
            })
    return output


def find_similar_page_objects(query: str, n_results: int = 5, module: str = None) -> list[dict]:
    """查找相似 Page Object — 用于新页面自动化时参考已有代码。

    示例: find_similar_page_objects("el-cascader 级联选择器 弹窗表单")
    """
    return search_context(query, "page_objects", module=module, n_results=n_results)


def recommend_test_patterns(page_description: str, n_results: int = 5) -> list[dict]:
    """跨模块推荐测试用例模式。

    基于页面描述，在已索引的 TEST_DESIGN/TECH_ANALYSIS 中搜索类似场景。

    示例: recommend_test_patterns("表格页面 搜索筛选 弹窗CRUD Element Plus")
    """
    results = []
    # 搜索技术分析
    tech_results = search_context(page_description, "tech_analysis", n_results=n_results)
    for r in tech_results:
        r["source_type"] = "tech_analysis"
        results.append(r)

    # 搜索页面上下文
    page_results = search_context(page_description, "page_context", n_results=n_results)
    for r in page_results:
        r["source_type"] = "page_context"
        results.append(r)

    # 按距离排序
    results.sort(key=lambda r: r.get("distance", 999))
    return results[:n_results]


def search_context(query: str, collection_name: str = "tech_analysis",
                   module: str = None, n_results: int = 5,
                   client = None, max_chars: int = None) -> list[dict]:
    """搜索上下文文档。

    参数:
        query: 搜索查询
        collection_name: tech_analysis | page_context | project_context
        module: 按模块筛选
        n_results: 返回结果数
        client: P0-2: 可选 ChromaDB PersistentClient（复用避免重复创建连接）
        max_chars: Token 预算感知截断 — 按段落截断每条文档到指定字符数。
                   None = 沿用现有 500 字符截断。
    """
    if client is None:
        client = get_chroma_client()

    # ★ P2-8: 查询前自动同步 — 仅当源文件变更时重建索引
    if collection_name == "tech_analysis":
        _ensure_tech_analysis_synced(client)
    elif collection_name == "page_context":
        _ensure_page_context_synced(client)

    try:
        collection = client.get_collection(collection_name)
    except Exception as e:
        from aitest.infra.error_logger import log_error
        log_error("rag_engine.search_context", "get_collection", e, {"collection": collection_name})
        return []

    where = {"module": module} if module else None

    try:
        results = collection.query(
            query_texts=[query],
            n_results=min(n_results, collection.count()),
            where=where
        )
    except Exception as e:
        from aitest.infra.error_logger import log_error
        log_error("rag_engine.search_context", "query", e, {"query": query[:100], "collection": collection_name})
        return []

    output = []
    if results["ids"] and results["ids"][0]:
        for i, doc_id in enumerate(results["ids"][0]):
            raw_doc = results["documents"][0][i] if results["documents"] else ""
            # max_chars: 按段落智能截断（不是盲目字符截断）
            if max_chars and len(raw_doc) > max_chars:
                # 尝试按段落边界截断
                paragraphs = raw_doc.split("\n\n")
                truncated = ""
                for para in paragraphs:
                    if len(truncated) + len(para) + 2 > max_chars:
                        break
                    truncated = (truncated + "\n\n" + para).lstrip("\n")
                raw_doc = truncated or raw_doc[:max_chars]
            else:
                raw_doc = raw_doc[:500]  # 沿用现有截断

            output.append({
                "id": doc_id,
                "document": raw_doc,
                "metadata": results["metadatas"][0][i] if results["metadatas"] else {},
                "distance": results["distances"][0][i] if results["distances"] else None
            })
    return output


# ══════════════════════════════════════════════════════════════════════════
#  CLI
# ══════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    import sys

    if len(sys.argv) < 2:
        print("Usage: python rag_engine.py index|search|status")
        sys.exit(0)

    cmd = sys.argv[1]

    if cmd == "index":
        print("Building indices...")
        results = index_all()
        for name, count in results.items():
            print(f"  {name}: {count} documents")
        print(f"Done. Data: {CHROMA_DIR}")

    elif cmd == "search":
        if len(sys.argv) < 3:
            print("Usage: python rag_engine.py search '<query>' [collection]")
            sys.exit(1)
        query = sys.argv[2]
        coll = sys.argv[3] if len(sys.argv) > 3 else "known_issues"
        if coll == "known_issues":
            results = search_known_issues(query)
        elif coll == "page_objects":
            from aitest.knowledge.rag_engine import search_context
            results = search_context(query, "page_objects")
        else:
            results = search_context(query, coll)
        for r in results:
            print(f"  [{r['id']}] dist={r['distance']:.4f} | {r['metadata']}")
            print(f"    {r['document'][:200]}")
            print()

    elif cmd == "status":
        client = get_chroma_client()
        collections = client.list_collections()
        for c in collections:
            print(f"  {c.name}: {c.count()} docs | {c.metadata}")

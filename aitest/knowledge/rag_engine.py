"""RAG Engine — ChromaDB indexing and search.

拆分为:
  - rag_engine.py: 入口 + 搜索函数 (本文件)
  - rag_indexers.py: 索引函数
"""

import logging
from pathlib import Path

import chromadb

logger = logging.getLogger(__name__)


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


# ═══════════════════════════════════════════════════════════════════════════
#  Task 3b (P0): Planner Memory Context — 5-type memory query + graceful degrade
# ═══════════════════════════════════════════════════════════════════════════


def build_planner_memory_context(
    module: str,
    task_description: str = "",
    client=None,
    n_results: int = 5,
) -> str:
    """Query 5 memory types and format as planner context for agent injection.

    Memory types queried:
      - task_calibration    → past timing/effort estimates vs actual
      - dead_end            → known failure paths (auto-detected)
      - workflow_recipe     → successful testing strategies
      - decision            → key decisions from past executions
      - historical_failure  → failure patterns with known fixes

    Graceful degradation:
      - Empty ChromaDB (cold start) → returns explicit hint text
      - DB unavailable (connect fail) → returns "" silently
      - Partial results → formats only non-empty sections

    Args:
        module: Business module name (e.g. "equipment").
        task_description: Human-readable goal for workflow recipe matching.
        client: Optional ChromaDB PersistentClient (reuse connection).
        n_results: Max results per memory type.

    Returns:
        Formatted context string for planner agent injection,
        or "" on DB failure, or explicit hint on cold start.
    """
    if client is None:
        try:
            client = get_chroma_client()
        except Exception:
            return ""  # DB unreachable → silent fallback

    # Query each memory type — each call is independently try/except safe
    def _safe_query(query_text: str, collection: str, module_filter: str = None) -> list[dict]:
        """Query a collection safely. Returns empty list on any failure."""
        try:
            return search_context(
                query=query_text,
                collection_name=collection,
                module=module_filter,
                n_results=n_results,
                client=client,
            )
        except Exception:
            return []

    try:
        calibrations = _safe_query(
            f"{module} effort estimates timing", "project_context", module,
        )
        dead_ends = _safe_query(
            f"{module} dead end failure path", "project_context", module,
        )
        recipes = _safe_query(
            f"{task_description or module} workflow strategy", "project_context", module,
        )
        decisions = _safe_query(
            f"{module} decision made", "project_context", module,
        )
        failures = _safe_query(
            f"{module} failure pattern fix", "project_context", module,
        )
    except Exception:
        return ""  # Catastrophic DB failure → silent fallback

    # Build sections — only include non-empty
    sections: dict[str, list[dict]] = {}
    if calibrations:
        sections["历史标定 (Past Calibrations)"] = calibrations
    if dead_ends:
        sections["已知死胡同 (Known Dead Ends)"] = dead_ends
    if recipes:
        sections["工作流配方 (Workflow Recipes)"] = recipes
    if decisions:
        sections["关键决策 (Key Decisions)"] = decisions
    if failures:
        sections["历史失败 (Historical Failures)"] = failures

    # All empty → cold start hint
    if not sections:
        return (
            "[Memory] No relevant project memory found. "
            "This appears to be a first-time execution for this module. "
            "Proceed with fresh reasoning — key decisions and outcomes "
            "will be recorded for future runs."
        )

    # Format non-empty sections
    parts = ["## 项目记忆 (Project Memory)\n"]
    for label, results in sections.items():
        parts.append(f"### {label}")
        for r in results[:3]:  # Top 3 per section
            content = str(r.get("content", r.get("text", "")))[:300]
            if content.strip():
                parts.append(f"- {content}")
        parts.append("")
    return "\n".join(parts)


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
        logger.info("Usage: python rag_engine.py index|search|status")
        sys.exit(0)

    cmd = sys.argv[1]

    if cmd == "index":
        logger.info("Building indices...")
        results = index_all()
        for name, count in results.items():
            logger.info(f"  {name}: {count} documents")
        logger.info(f"Done. Data: {CHROMA_DIR}")

    elif cmd == "search":
        if len(sys.argv) < 3:
            logger.info("Usage: python rag_engine.py search '<query>' [collection]")
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
            logger.info(f"  [{r['id']}] dist={r['distance']:.4f} | {r['metadata']}")
            logger.info(f"    {r['document'][:200]}")
            logger.info()

    elif cmd == "status":
        client = get_chroma_client()
        collections = client.list_collections()
        for c in collections:
            logger.info(f"  {c.name}: {c.count()} docs | {c.metadata}")

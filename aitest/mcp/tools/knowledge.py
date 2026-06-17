"""Tools: search_known_issues + rag_search_known_issues (with P2-1 Sampling)。"""
import yaml

from aitest.mcp.config import KNOWN_ISSUES
from aitest.mcp.error_taxonomy import ErrorCode, error_response
from aitest.mcp.sampling import request_llm_sync
from aitest.knowledge.rag_engine import search_known_issues as rag_search_known_issues_raw


def search_known_issues(query: str = "", category: str = "", component: str = "",
                        severity: str = "", offset: int = 0, limit: int = 50) -> dict:
    """从 known-issues.yaml 搜索匹配的问题。P3-4: 支持 offset/limit 分页。"""
    if not KNOWN_ISSUES.exists():
        return error_response(
            ErrorCode.FILE_NOT_FOUND,
            f"Known issues file not found: {KNOWN_ISSUES}",
            "known-issues.yaml 缺失。运行 /project-agent 初始化项目上下文。",
        )

    with open(KNOWN_ISSUES, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f)

    issues = data.get("issues", [])
    results = []

    for issue in issues:
        match = True
        if query:
            q = query.lower()
            match = match and (
                q in issue.get("title", "").lower()
                or q in issue.get("id", "").lower()
                or any(q in s.lower() for s in issue.get("symptoms", []))
                or q in issue.get("root_cause", "").lower()
                or q in issue.get("component", "").lower()
            )
        if category:
            match = match and issue.get("category") == category
        if component:
            match = match and component.lower() in issue.get("component", "").lower()
        if severity:
            match = match and issue.get("severity") == severity

        if match:
            results.append(issue)

    total = len(results)
    # P3-4: 分页
    paged = results[offset:offset + limit] if limit > 0 else results

    return {
        "status": "ok",
        "query": query,
        "total": total,
        "offset": offset,
        "limit": limit,
        "returned": len(paged),
        "results": paged,
    }


def rag_search_with_sampling(query: str, n_results: int = 5, use_sampling: bool = True) -> dict:
    """P2-1: RAG 搜索 + LLM Sampling 重排序。sampling 不可用时自动降级。"""
    try:
        raw_result = rag_search_known_issues_raw(query=query, n_results=n_results)
    except Exception as e:
        return error_response(ErrorCode.EXECUTION_FAILED, f"RAG search failed: {str(e)}",
                              "检查 ChromaDB 是否运行，向量索引是否已构建。", retryable=True)

    if not isinstance(raw_result, dict):
        return raw_result

    results = raw_result.get("results", [])
    raw_result["sampling_used"] = False

    if use_sampling and len(results) > 3:
        prompt = (
            f"以下是 {len(results)} 条已知问题匹配结果。请按与查询 '{query[:200]}' 的相关度从高到低重排序，"
            f"保留最相关的 3 条。对于每条，给出 1 句话说明为什么相关。\n\n"
        )
        for i, r in enumerate(results):
            prompt += f"[{i}] {r.get('id', '?')}: {r.get('title', 'No title')} — {r.get('root_cause', '?')[:200]}\n"

        summary = request_llm_sync(prompt, max_tokens=300)
        if summary:
            raw_result["sampling_used"] = True
            raw_result["llm_rerank_summary"] = summary
            raw_result["note"] = "llm_rerank_summary contains AI-reranked top-3 with relevance explanation."

    return raw_result

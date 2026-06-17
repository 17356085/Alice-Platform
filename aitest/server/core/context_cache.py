"""
Context Cache — Context 分层缓存。

三层缓存策略:
  L1: 内存缓存 (Python dict, TTL 5 分钟)
  L2: ChromaDB RAG 检索 (按需加载 chunk)
  L3: 磁盘读取 (Markdown 文件，L1/L2 miss 时)

用于 FastAPI 长期运行服务中避免每次请求都从磁盘全量读取 Context。
"""
import time
from pathlib import Path

WORKSTUDY = Path(__file__).resolve().parent.parent.parent.parent
GOVERNANCE = WORKSTUDY / "governance"


class ContextCache:
    """Context 分层缓存。"""

    def __init__(self, ttl: int = 300):
        self._memory: dict[str, tuple[float, str]] = {}  # key → (timestamp, content)
        self._ttl = ttl  # 5 分钟 TTL（与 Anthropic Prompt Cache TTL 对齐）

    def get(self, key: str) -> str:
        """从缓存获取内容。

        参数:
            key: 缓存键，格式: "file_path#heading" 如 "PROJECT_CONTEXT.md#BasePage API"

        返回:
            内容字符串，或空字符串表示未命中
        """
        # L1: 内存
        if key in self._memory:
            ts, content = self._memory[key]
            if time.time() - ts < self._ttl:
                return content
            del self._memory[key]  # 过期

        # L2: ChromaDB RAG（尝试）
        content = self._search_rag(key)
        if content:
            self._memory[key] = (time.time(), content)
            return content

        # L3: 磁盘读取（按文件+章节）
        content = self._read_file_section(key)
        if content:
            self._memory[key] = (time.time(), content)

        return content

    def set(self, key: str, content: str):
        """手动设置缓存。"""
        self._memory[key] = (time.time(), content)

    def invalidate(self, key: str = None):
        """使缓存失效。key 为 None 则清空全部。"""
        if key:
            self._memory.pop(key, None)
        else:
            self._memory.clear()

    # ── 内部 ──

    def _search_rag(self, key: str) -> str:
        """通过 RAG 检索。"""
        try:
            parts = key.split("#", 1)
            if len(parts) < 2:
                return ""
            query = parts[1]  # heading 作为查询

            from aitest.knowledge.rag_engine import search_context
            results = search_context(query, "project_context", n_results=1)
            if results and results[0].get("distance", 999) < 0.3:
                return results[0].get("document", "")
        except Exception as e:
            from aitest.infra.error_logger import log_error
            log_error("context_cache.get", "rag_search", e, {"query": query[:100]})
        return ""

    def _read_file_section(self, key: str) -> str:
        """从磁盘文件读取指定章节。"""
        import re
        parts = key.split("#", 1)
        file_name = parts[0]
        heading = parts[1] if len(parts) > 1 else ""

        # 查找文件
        file_path = GOVERNANCE / "context" / "projects" / "web-automation" / file_name
        if not file_path.exists():
            # 尝试在 context/ 下搜索
            candidates = list(GOVERNANCE.rglob(file_name))
            file_path = candidates[0] if candidates else None
            if not file_path:
                return ""

        try:
            content = file_path.read_text(encoding="utf-8")
        except Exception as e:
            from aitest.infra.error_logger import log_error
            log_error("context_cache._read_file", "read", e, {"file": str(file_path)})
            return ""

        if not heading:
            return content

        # 按 ## heading 分割，返回匹配的章节
        pattern = rf"^##\s+{re.escape(heading)}.*$"
        lines = content.split("\n")
        matched_lines = []
        in_section = False

        for line in lines:
            if re.match(pattern, line, re.IGNORECASE):
                in_section = True
                matched_lines.append(line)
            elif in_section and line.startswith("## "):
                break  # 下一个章节开始
            elif in_section:
                matched_lines.append(line)

        return "\n".join(matched_lines) if matched_lines else ""


# 全局单例
_cache = ContextCache()


def get_cache() -> ContextCache:
    return _cache

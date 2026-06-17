"""
Context Injector — 为 Skill Prompt 按需注入项目上下文。

设计原则:
  1. 不加载完整文档——通过 ChromaDB RAG 按需检索相关片段
  2. 不同 Skill 需要不同的上下文（由 SKILL_CONTEXT_MAP 定义）
  3. 变量替换支持（{module}, {page}, {error_msg} 等）

用法:
    injector = ContextInjector()
    prompt = injector.inject(
        skill_id="automation/tech-analysis",
        skill_prompt=raw_prompt,
        variables={"module": "equipment", "page": "alarm-config"}
    )
"""
from pathlib import Path

# ── 路径配置 ──
WORKSTUDY = Path(__file__).resolve().parent.parent.parent
GOVERNANCE = WORKSTUDY / "governance"
CONTEXT_MODULES = GOVERNANCE / "context" / "projects" / "web-automation" / "modules"

# ── Skill → 上下文需求映射 ──
# 每个条目定义该 Skill 需要的上下文类型及如何获取

SKILL_CONTEXT_MAP = {
    # ── requirements (无-PRD 模式: 从代码反推) ──
    "requirements/module-modeling": [
        {"type": "file", "path": "{project_context_path}", "label": "项目上下文", "max_chars": 4000, "optional": True},
        {"type": "file", "path": "{po_dir}", "label": "Page Object 目录列表（用于发现页面）", "max_chars": 3000, "optional": True},
        {"type": "file", "path": "{test_dir}", "label": "测试脚本目录列表", "max_chars": 2000, "optional": True},
        {"type": "rag", "collection": "project_context", "query": "{module} 模块结构"},
    ],
    "requirements/requirement-analysis": [
        {"type": "file", "path": "{po_path}", "label": "Page Object 代码（真实DOM/定位器来源）", "max_chars": 8000},
        {"type": "file", "path": "{test_path}", "label": "测试脚本（真实测试场景来源）", "max_chars": 6000},
        {"type": "file", "path": "{module_dir}/MODULE_CONTEXT.md", "label": "模块上下文", "max_chars": 4000, "optional": True},
        {"type": "rag", "collection": "project_context", "query": "Element Plus 定位规范 页面分析"},
    ],

    # test-design
    "test-design/page-analysis": [
        {"type": "file", "path": "{po_path}", "label": "Page Object 代码（真实定位器来源）", "max_chars": 6000},
        {"type": "file", "path": "{module_dir}/pages/{page}/PAGE_CONTEXT.md", "label": "页面上下文（需求阶段产出）", "optional": True, "max_chars": 3000},
        {"type": "rag", "collection": "project_context", "query": "BasePage API 交互方法"},
        {"type": "rag", "collection": "project_context", "query": "Element Plus 定位规范"},
    ],
    "test-design/risk-modeling": [
        {"type": "file", "path": "{po_path}", "label": "Page Object 代码", "max_chars": 4000, "optional": True},
        {"type": "file", "path": "{module_dir}/pages/{page}/PAGE_CONTEXT.md", "label": "页面上下文", "optional": True, "max_chars": 3000},
        {"type": "rag", "collection": "known_issues", "query": "{module} 已知问题"},
        {"type": "rag", "collection": "project_context", "query": "Element Plus 坑位"},
    ],
    "test-design/testcase-design": [
        {"type": "file", "path": "{po_path}", "label": "Page Object 代码（真实方法/定位器）", "max_chars": 5000},
        {"type": "file", "path": "{test_path}", "label": "现有测试脚本（场景参考）", "max_chars": 4000, "optional": True},
        {"type": "file", "path": "{module_dir}/pages/{page}/PAGE_CONTEXT.md", "label": "页面上下文", "optional": True, "max_chars": 3000},
        {"type": "file", "path": "{module_dir}/pages/{page}/RISK_MODEL.md", "label": "风险模型", "optional": True, "max_chars": 2000},
        {"type": "rag", "collection": "project_context", "query": "测试用例命名规范"},
    ],

    # automation (PAGE_CONTEXT.md 为主要页面信息来源；PAGE_INTERFACE.yaml 是可选的精简索引)
    "automation/tech-analysis": [
        {"type": "rag", "collection": "project_context", "query": "定位器规范 CSS XPath Element Plus"},
        {"type": "rag", "collection": "project_context", "query": "Element Plus 坑位 定位"},
        {"type": "file", "path": "{module_dir}/pages/{page}/PAGE_CONTEXT.md", "label": "页面元素清单（主源）", "max_chars": 2000},
        {"type": "file", "path": "{module_dir}/pages/{page}/PAGE_INTERFACE.yaml", "label": "结构化页面接口（可选索引）", "optional": True, "max_chars": 500},
    ],
    "automation/auto-strategy": [
        {"type": "file", "path": "{module_dir}/pages/{page}/TECH_ANALYSIS.md", "label": "技术分析"},
        {"type": "rag", "collection": "project_context", "query": "自动化策略 等待策略"},
    ],
    "automation/page-object-generator": [
        {"type": "rag", "collection": "project_context", "query": "代码红线 BasePage 继承"},
        {"type": "rag", "collection": "project_context", "query": "定位器写法规范"},
        {"type": "rag", "collection": "page_objects", "query": "{module} {page}"},
        {"type": "file", "path": "{module_dir}/pages/{page}/PAGE_CONTEXT.md", "label": "页面元素清单（主源）", "max_chars": 2000},
        {"type": "file", "path": "{module_dir}/pages/{page}/PAGE_INTERFACE.yaml", "label": "结构化页面接口（可选索引）", "optional": True, "max_chars": 500},
    ],
    "automation/test-script-generator": [
        {"type": "rag", "collection": "project_context", "query": "pytest 测试脚本规范 fixture"},
        {"type": "file", "path": "{module_dir}/pages/{page}/TEST_CASES.md", "label": "测试用例"},
    ],
    "automation/code-consistency-checker": [
        # 机械化 Skill，不需要 LLM 上下文
    ],

    # diagnosis
    "diagnosis/bug-analysis": [
        {"type": "rag", "collection": "known_issues", "query": "{error_msg}"},
        {"type": "rag", "collection": "project_context", "query": "Element Plus 坑位"},
        {"type": "rag", "collection": "project_context", "query": "失败模式 常见原因"},
    ],

    # reporting
    "reporting/report-generator": [
        {"type": "rag", "collection": "project_context", "query": "模块状态 测试覆盖率"},
    ],

    # knowledge
    "knowledge/knowledge-manager": [
        {"type": "rag", "collection": "known_issues", "query": "{module}"},
    ],
}

# ── 开发 Skills 上下文映射 ──
# 与 SKILL_CONTEXT_MAP 并行，为开发技能提供上下文注入
DEV_SKILL_CONTEXT_MAP: dict[str, list[dict]] = {
    "architecture/project-scanner": [
        {"type": "file", "path": "{module_dir}/PROJECT_CONTEXT.md", "max_chars": 2000},
    ],
    "architecture/tech-stack-decider": [
        {"type": "file", "path": "{module_dir}/PROJECT_STRUCTURE.md", "max_chars": 2000},
        {"type": "file", "path": "{module_dir}/TECH_STACK_REFERENCE.md", "max_chars": 2000},
    ],
    "architecture/component-tree-designer": [
        {"type": "file", "path": "{module_dir}/TECH_STACK.md", "max_chars": 1500},
    ],
    "architecture/api-contract-designer": [
        {"type": "file", "path": "{module_dir}/COMPONENT_TREE.md", "max_chars": 2000},
    ],
    "frontend/vue-component-generator": [
        {"type": "file", "path": "{module_dir}/CODING_STANDARDS.md", "max_chars": 2000},
        {"type": "file", "path": "{module_dir}/TECH_STACK_REFERENCE.md", "max_chars": 1500},
    ],
    "frontend/page-implementer": [
        {"type": "file", "path": "{module_dir}/COMPONENT_TREE.md", "max_chars": 2000},
        {"type": "file", "path": "{module_dir}/API_CONTRACTS.md", "max_chars": 2000},
    ],
    "backend/fastapi-router-generator": [
        {"type": "file", "path": "{module_dir}/CODING_STANDARDS.md", "max_chars": 2000},
        {"type": "file", "path": "{module_dir}/TECH_STACK_REFERENCE.md", "max_chars": 1500},
        {"type": "file", "path": "{module_dir}/API_CONTRACTS.md", "max_chars": 2000},
    ],
    "backend/pydantic-schema-generator": [
        {"type": "file", "path": "{module_dir}/API_CONTRACTS.md", "max_chars": 2000},
    ],
    "backend/sqlalchemy-model-generator": [
        {"type": "file", "path": "{module_dir}/TECH_STACK_REFERENCE.md", "max_chars": 1500},
    ],
}


class ContextInjector:
    """按需注入上下文到 Skill Prompt 中。"""

    def __init__(self):
        # P0-1a: 文件读取缓存 (path → content)
        self._file_cache: dict[str, str] = {}
        # P0-1b: RAG 查询缓存 ((query, collection) → result)
        self._rag_cache: dict[tuple, str] = {}
        # P1 可观测性: 缓存命中/未命中计数器
        self._file_cache_hits: int = 0
        self._file_cache_misses: int = 0
        self._rag_cache_hits: int = 0
        self._rag_cache_misses: int = 0
        # P0 可观测性: 最近一次 inject() 的上下文统计
        self._last_inject_stats: dict = {}

    def inject(
        self,
        skill_id: str,
        skill_prompt: str,
        variables: dict = None,
    ) -> str:
        """
        为 Skill Prompt 注入相关上下文。

        参数:
            skill_id:    Skill 标识符（如 "automation/tech-analysis"）
            skill_prompt: 原始 Skill Prompt
            variables:   变量替换字典（如 {"module": "equipment", "page": "alarm-config"}）

        返回:
            注入了上下文的完整 system prompt
        """
        variables = variables or {}

        # ── ContextAgent 精准注入 —— 跳过 SKILL_CONTEXT_MAP 文件读取（省 token）──
        if variables.get("focused_context"):
            focused = variables["focused_context"]
            self._last_inject_stats = {
                "context_chars": len(focused),
                "source_count": 1,
                "sources": ["context_agent:focused"],
            }
            return f"{skill_prompt}\n\n## 参考上下文\n\n{focused}"

        context_map = SKILL_CONTEXT_MAP.get(skill_id, [])

        # 开发技能: 检查 DEV_SKILL_CONTEXT_MAP
        if not context_map:
            context_map = DEV_SKILL_CONTEXT_MAP.get(skill_id, [])

        # 尝试也匹配简化 ID（去掉 category 前缀）
        if not context_map:
            simple_id = skill_id.split("/")[-1] if "/" in skill_id else skill_id
            for key, value in SKILL_CONTEXT_MAP.items():
                if key.endswith(simple_id):
                    context_map = value
                    break
            if not context_map:
                for key, value in DEV_SKILL_CONTEXT_MAP.items():
                    if key.endswith(simple_id):
                        context_map = value
                        break

        if not context_map:
            # ★ P0 可观测性: 记录空上下文注入
            self._last_inject_stats = {"context_chars": 0, "source_count": 0, "sources": []}
            return skill_prompt  # 该 Skill 不需要上下文注入

        context_blocks = []
        sources = []
        for ctx_entry in context_map:
            content = self._resolve_context(ctx_entry, variables)
            if content:
                label = ctx_entry.get("label", "")
                sources.append(label or ctx_entry.get("type", "?"))
                if label:
                    context_blocks.append(f"### {label}\n{content}")
                else:
                    context_blocks.append(content)

        # ★ P0 可观测性: 记录注入上下文统计
        total_chars = sum(len(b) for b in context_blocks)
        self._last_inject_stats = {
            "context_chars": total_chars,
            "source_count": len(context_blocks),
            "sources": sources,
        }

        if context_blocks:
            context_text = "\n\n---\n\n".join(context_blocks)
            return f"{skill_prompt}\n\n## 参考上下文\n\n{context_text}"

        return skill_prompt

    # ── P1 可观测性: 缓存统计 ──

    def get_cache_stats(self) -> dict:
        """返回文件缓存和 RAG 缓存的命中/未命中统计。"""
        file_total = self._file_cache_hits + self._file_cache_misses
        rag_total = self._rag_cache_hits + self._rag_cache_misses
        return {
            "file_cache": {
                "hits": self._file_cache_hits,
                "misses": self._file_cache_misses,
                "rate": round(self._file_cache_hits / file_total, 3) if file_total > 0 else None,
            },
            "rag_cache": {
                "hits": self._rag_cache_hits,
                "misses": self._rag_cache_misses,
                "rate": round(self._rag_cache_hits / rag_total, 3) if rag_total > 0 else None,
            },
        }

    # ── 内部方法 ──

    def _resolve_context(self, entry: dict, variables: dict) -> str:
        """解析单个上下文条目。"""
        ctx_type = entry.get("type", "")
        optional = entry.get("optional", False)

        try:
            if ctx_type == "rag":
                return self._resolve_rag(entry, variables)
            elif ctx_type == "file":
                return self._resolve_file(entry, variables)
            elif ctx_type == "inline":
                return entry.get("content", "")
            else:
                return ""
        except Exception as e:
            if optional:
                return ""  # 可选上下文缺失不报错
            return f"[上下文加载失败: {ctx_type}] {str(e)}"

    def _resolve_rag(self, entry: dict, variables: dict) -> str:
        """通过 RAG 检索获取上下文（P0-1b: 结果缓存，跨 Skill 复用）。"""
        query = entry.get("query", "").format(**variables)
        collection = entry.get("collection", "project_context")

        # ★ P0-1b: RAG cache — (query, collection) 跨 Skill 共享
        cache_key = (query, collection)
        if cache_key in self._rag_cache:
            self._rag_cache_hits += 1  # P1 可观测性
            return self._rag_cache[cache_key]
        self._rag_cache_misses += 1

        try:
            from aitest.knowledge.rag_engine import search_context
            results = search_context(query, collection, n_results=3)
        except Exception as e:
            from aitest.infra.error_logger import log_error
            log_error("context_injector._inject_rag", "search_context", e, {"query": query[:100], "collection": collection})
            self._rag_cache[cache_key] = ""
            return ""

        if not results:
            self._rag_cache[cache_key] = ""
            return ""

        lines = []
        for r in results:
            if r.get("distance", 999) < 1.5:
                doc = r.get("document", "")[:500]
                lines.append(doc)

        result_text = "\n".join(lines) if lines else ""
        self._rag_cache[cache_key] = result_text
        return result_text

    def _resolve_file(self, entry: dict, variables: dict) -> str:
        """从文件加载上下文（P0-1a: 缓存路径→内容）。"""
        path_template = entry.get("path", "")
        path_str = path_template

        # 变量替换
        for key, value in variables.items():
            path_str = path_str.replace(f"{{{key}}}", str(value))

        # {module_dir} 特殊处理
        module = variables.get("module", "")
        path_str = path_str.replace(
            "{module_dir}",
            str(CONTEXT_MODULES / module)
        )

        file_path = Path(path_str)

        # ★ P0-1a: file read cache — 文件在会话内不变
        cache_key = str(file_path)
        if cache_key in self._file_cache:
            self._file_cache_hits += 1  # P1 可观测性
            return self._file_cache[cache_key]
        self._file_cache_misses += 1

        if not file_path.exists():
            if entry.get("optional"):
                return ""
            return f"[文件不存在: {file_path}]"

        content = file_path.read_text(encoding="utf-8")
        # 截断过大的文件
        max_chars = entry.get("max_chars", 3000)
        if len(content) > max_chars:
            content = content[:max_chars] + f"\n\n[... 文件过长，已截断。完整内容见 {file_path} ...]"

        self._file_cache[cache_key] = content
        return content

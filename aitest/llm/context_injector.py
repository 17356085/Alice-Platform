"""
Context Injector — 为 Skill Prompt 按需注入项目上下文。

设计原则:
  1. 不加载完整文档——通过 ChromaDB RAG 按需检索相关片段
  2. 不同 Skill 需要不同的上下文（由 SKILL_CONTEXT_MAP 定义）
  3. 变量替换支持（{module}, {page}, {error_msg} 等）
  4. Task Router: skill_id → 权重配置，优先召回最相关 collection
  5. ReRanker: 相关度+结构亲和度+新鲜度+多样性 混合排序
  6. DedupCache: 会话级内容去重，跨 Skill 不重复注入相同内容
  7. 固定基座分离: shared-language + PROJECT_CONTEXT 摘要独立缓存

用法:
    injector = ContextInjector()
    prompt = injector.inject(
        skill_id="automation/tech-analysis",
        skill_prompt=raw_prompt,
        variables={"module": "equipment", "page": "alarm-config"}
    )
"""
import time as _time_module
from pathlib import Path

# ── 路径配置 ──
from aitest.platform.paths import get_workstudy, get_project_dir, get_context_modules
WORKSTUDY = get_workstudy()
GOVERNANCE = WORKSTUDY / "governance"
CONTEXT_MODULES = get_context_modules()
_PROJECT_CONTEXT_PATH = get_project_dir() / "PROJECT_CONTEXT.md"

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
    "test-design/pair-seed": [
        {"type": "file", "path": "{module_dir}/pages/{page}/PAIR_SEEDS.md", "label": "结对种子（人类提供）", "optional": True, "max_chars": 4000},
        {"type": "file", "path": "{module_dir}/pages/{page}/PAGE_CONTEXT.md", "label": "页面上下文", "optional": True, "max_chars": 2000},
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
        {"type": "file", "path": "{module_dir}/pages/{page}/PAIR_SEEDS.md", "label": "🆕 结对种子（必须优先采用）", "optional": True, "max_chars": 4000},
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


# ── 固定基座文件路径 ──────────────────────────────────────────────────
_SHARED_LANGUAGE_PATH = GOVERNANCE / "context" / "shared-language.md"
_PROJECT_CONTEXT_PATH = (
    _PROJECT_CONTEXT_PATH
)
_FIXED_BASE_MAX_CHARS = 1500  # PROJECT_CONTEXT 摘要截断（含架构图和核心规范）

# ── Task Router: skill_id → collection 权重配置 ──────────────────────
# 权重决定 ReRanker 的结构亲和度加分（0.0-1.0）
SKILL_WEIGHT_PROFILES: dict[str, dict[str, float]] = {
    "diagnosis/bug-analysis": {
        "known_issues": 0.60, "tech_analysis": 0.25, "project_context": 0.10, "page_context": 0.05,
    },
    "automation/tech-analysis": {
        "project_context": 0.65, "tech_analysis": 0.20, "page_context": 0.10, "known_issues": 0.05,
    },
    "automation/auto-strategy": {
        "tech_analysis": 0.55, "project_context": 0.35, "page_context": 0.10,
    },
    "automation/page-object-generator": {
        "page_objects": 0.45, "project_context": 0.35, "page_context": 0.15, "tech_analysis": 0.05,
    },
    "automation/test-script-generator": {
        "project_context": 0.50, "page_context": 0.30, "tech_analysis": 0.20,
    },
    "test-design/page-analysis": {
        "project_context": 0.50, "page_context": 0.30, "tech_analysis": 0.20,
    },
    "test-design/risk-modeling": {
        "known_issues": 0.55, "project_context": 0.30, "tech_analysis": 0.15,
    },
    "test-design/testcase-design": {
        "project_context": 0.45, "page_context": 0.30, "tech_analysis": 0.15, "known_issues": 0.10,
    },
    "requirements/module-modeling": {
        "project_context": 0.70, "page_context": 0.20, "tech_analysis": 0.10,
    },
    "requirements/requirement-analysis": {
        "project_context": 0.60, "tech_analysis": 0.25, "page_context": 0.15,
    },
    # 默认权重（未在上表的 skill）
    "_default": {"project_context": 0.50, "tech_analysis": 0.30, "known_issues": 0.20},
}


def _get_weight_profile(skill_id: str) -> dict[str, float]:
    """根据 skill_id 获取 collection 权重配置（Task Router 核心）。"""
    if skill_id in SKILL_WEIGHT_PROFILES:
        return SKILL_WEIGHT_PROFILES[skill_id]
    # 尝试去掉 category 前缀匹配
    simple_id = skill_id.split("/")[-1] if "/" in skill_id else skill_id
    for key, profile in SKILL_WEIGHT_PROFILES.items():
        if key != "_default" and key.split("/")[-1] == simple_id:
            return profile
    return SKILL_WEIGHT_PROFILES["_default"]


def _rerank_results(
    results: list[dict],
    skill_id: str,
    weight_profile: dict[str, float],
) -> list[dict]:
    """
    ReRanker: 混合排序，替代纯向量距离排序。

    评分维度:
      D1 向量相关度 × 0.45: (1 - distance)，越小距离越相关
      D2 结构亲和度 × 0.35: 命中 weight_profile 的 collection 按权重加分
      D3 新鲜度      × 0.10: 1/(1 + days_old)，仅当 update_time 元数据存在
      D4 文件多样性  × 0.08: 同一 source 第2+条 × 0.8 惩罚，鼓励多样性
      D5 文件重要度  × 0.02: source 文件名重要性权重（PAGE_CONTEXT/TECH_ANALYSIS 最重要）
    """
    now_ts = int(_time_module.time())
    source_seen: dict[str, int] = {}  # source → 出现次数（多样性惩罚）

    # D5: 文件重要度映射（source filename → importance）
    _source_importance = {
        "PAGE_CONTEXT.md": 1.0,
        "TECH_ANALYSIS.md": 0.95,
        "TEST_DESIGN.md": 0.90,
        "TEST_CASES.md": 0.85,
        "RISK_MODEL.md": 0.80,
        "PAGE_INTERFACE.yaml": 0.75,
        "PAGE_ELEMENT_POSITION.md": 0.60,
        "known-issues.yaml": 0.85,
    }

    for r in results:
        meta = r.get("metadata", {})
        distance = r.get("distance", 1.0)

        # D1: 向量相关度 (0-1)
        d1 = max(0.0, 1.0 - distance) * 0.45

        # D2: 结构亲和度 (0-1)
        collection_type = meta.get("type", "")  # known_issue / tech_analysis / page_context / page_object
        # 将 metadata.type 映射到 collection key
        _type_to_collection = {
            "known_issue": "known_issues",
            "tech_analysis": "tech_analysis",
            "page_context": "page_context",
            "page_object": "page_objects",
            "project_context": "project_context",
        }
        coll_key = _type_to_collection.get(collection_type, collection_type)
        d2 = weight_profile.get(coll_key, 0.0) * 0.35

        # D3: 新鲜度 (0-1)，仅当 update_time 存在
        update_time = meta.get("update_time")
        if update_time:
            days_old = max(0, (now_ts - int(update_time)) / 86400)
            d3 = (1.0 / (1.0 + days_old)) * 0.10
        else:
            d3 = 0.05  # 无时间信息时给中等分

        # D4: 文件多样性惩罚
        source = meta.get("source", "unknown")
        count = source_seen.get(source, 0)
        source_seen[source] = count + 1
        diversity_factor = 0.8 ** count  # 第1条×1.0, 第2条×0.8, 第3条×0.64...
        d4 = diversity_factor * 0.08

        # D5: 文件重要度 (0-1)
        source_name = source.split("/")[-1] if "/" in source else source
        importance = _source_importance.get(source_name, 0.7)  # 默认中等重要
        d5 = importance * 0.02

        r["rerank_score"] = d1 + d2 + d3 + d4 + d5

    return sorted(results, key=lambda r: r.get("rerank_score", 0.0), reverse=True)


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
        # DedupCache: 会话级内容去重
        self._seen_content_hashes: set = set()
        # 固定基座缓存（会话内只加载一次）
        self._fixed_base_cache: str | None = None

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
                "context_tokens_est": len(focused) // 4,
                "source_count": 1,
                "sources": ["context_agent:focused"],
                "fixed_chars": 0,
                "on_demand_chars": len(focused),
                "rag_dedup_hits": 0,
                "rerank_applied": False,
            }
            return f"{skill_prompt}\n\n## 参考上下文\n\n{focused}"

        # ── 固定基座（会话内只加载一次）──
        fixed_base = self._load_fixed_base()
        fixed_chars = len(fixed_base)

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
            self._last_inject_stats = {
                "context_chars": fixed_chars,
                "context_tokens_est": fixed_chars // 4,
                "source_count": 0,
                "sources": [],
                "fixed_chars": fixed_chars,
                "on_demand_chars": 0,
                "rag_dedup_hits": 0,
                "rerank_applied": False,
            }
            if fixed_base:
                return f"{skill_prompt}\n\n## 项目基座上下文\n\n{fixed_base}"
            return skill_prompt

        # ── 获取 Task Router 权重配置 ──
        weight_profile = _get_weight_profile(skill_id)

        # ── 收集所有上下文块（file + rag）──
        raw_rag_results: list[dict] = []   # rag 类型结果集中收集，统一 rerank
        context_blocks: list[str] = []     # file 类型直接加入（保持 SKILL_CONTEXT_MAP 结构）
        sources: list[str] = []
        rag_dedup_hits = 0

        for ctx_entry in context_map:
            if ctx_entry.get("type") == "rag":
                # rag: 收集原始结果，延迟 rerank
                raw = self._resolve_rag_raw(ctx_entry, variables)
                for r in raw:
                    doc = r.get("document", "")
                    content_hash = hash(doc[:200])
                    if content_hash in self._seen_content_hashes:
                        rag_dedup_hits += 1
                        continue
                    raw_rag_results.append(r)
            else:
                # file/inline: 直接解析
                content = self._resolve_context(ctx_entry, variables)
                if content:
                    label = ctx_entry.get("label", "")
                    sources.append(label or ctx_entry.get("type", "?"))
                    if label:
                        context_blocks.append(f"### {label}\n{content}")
                    else:
                        context_blocks.append(content)

        # ── ReRanker: 对 rag 结果混合排序 ──
        rerank_applied = len(raw_rag_results) > 0
        if raw_rag_results:
            ranked = _rerank_results(raw_rag_results, skill_id, weight_profile)
            # 取前 3 条（与原 n_results=3 保持一致）
            for r in ranked[:3]:
                doc = r.get("document", "")
                if not doc:
                    continue
                content_hash = hash(doc[:200])
                self._seen_content_hashes.add(content_hash)
                label = r.get("metadata", {}).get("type", "RAG")
                sources.append(f"rag:{label}")
                context_blocks.append(doc)

        # ── 组装最终上下文 ──
        on_demand_chars = sum(len(b) for b in context_blocks)
        total_chars = fixed_chars + on_demand_chars

        # ★ P0 可观测性: 记录注入上下文统计（扩展版）
        self._last_inject_stats = {
            "context_chars": total_chars,
            "context_tokens_est": total_chars // 4,
            "source_count": len(context_blocks),
            "sources": sources,
            "fixed_chars": fixed_chars,
            "on_demand_chars": on_demand_chars,
            "rag_dedup_hits": rag_dedup_hits,
            "rerank_applied": rerank_applied,
        }

        parts = [skill_prompt]
        if fixed_base:
            parts.append(f"## 项目基座上下文\n\n{fixed_base}")
        if context_blocks:
            context_text = "\n\n---\n\n".join(context_blocks)
            parts.append(f"## 参考上下文\n\n{context_text}")

        return "\n\n".join(parts)

    # ── 固定基座加载 ─────────────────────────────────────────────

    def _load_fixed_base(self) -> str:
        """
        加载固定基座上下文（会话内只计算一次，后续从缓存返回）。

        内容：shared-language.md + PROJECT_CONTEXT.md 摘要（前 1500 chars）
        这两个文件对所有 Skill 都相关，提取为固定层避免 SKILL_CONTEXT_MAP 中重复加载。
        """
        if self._fixed_base_cache is not None:
            return self._fixed_base_cache

        parts = []

        # shared-language.md（~350 tokens，术语+歧义消除）
        cache_key = str(_SHARED_LANGUAGE_PATH)
        if cache_key not in self._file_cache:
            if _SHARED_LANGUAGE_PATH.exists():
                self._file_cache[cache_key] = _SHARED_LANGUAGE_PATH.read_text(encoding="utf-8")
            else:
                self._file_cache[cache_key] = ""
        sl = self._file_cache[cache_key]
        if sl:
            parts.append(f"### 共享语言 (shared-language)\n{sl[:1200]}")

        # PROJECT_CONTEXT.md 摘要（前 1500 chars，含架构图和核心定位规范）
        cache_key2 = str(_PROJECT_CONTEXT_PATH)
        if cache_key2 not in self._file_cache:
            if _PROJECT_CONTEXT_PATH.exists():
                content = _PROJECT_CONTEXT_PATH.read_text(encoding="utf-8")
                self._file_cache[cache_key2] = content[:_FIXED_BASE_MAX_CHARS]
            else:
                self._file_cache[cache_key2] = ""
        pc = self._file_cache[cache_key2]
        if pc:
            parts.append(f"### 项目上下文摘要 (PROJECT_CONTEXT)\n{pc}")

        self._fixed_base_cache = "\n\n".join(parts)
        return self._fixed_base_cache

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

        # _resolve_rag_raw 会填充 _rag_cache，调用完后直接读缓存返回
        self._resolve_rag_raw(entry, variables)
        return self._rag_cache.get(cache_key, "")

    def _resolve_rag_raw(self, entry: dict, variables: dict) -> list[dict]:
        """
        通过 RAG 检索返回原始结果列表（供 ReRanker 使用）。

        与 _resolve_rag() 不同：返回完整 result 对象而非拼接字符串，
        结果缓存在 _rag_cache 中共享。
        """
        query = entry.get("query", "").format(**variables)
        collection = entry.get("collection", "project_context")

        # 检查字符串缓存中是否已有此查询（复用结果）
        cache_key = (query, collection)
        if cache_key in self._rag_cache:
            self._rag_cache_hits += 1
            # 字符串缓存命中 — 无法还原原始结果，返回空列表（rerank 不会重复处理）
            return []

        self._rag_cache_misses += 1  # 计入 miss（_resolve_rag 不再单独计数）

        try:
            from aitest.knowledge.rag_engine import search_context
            results = search_context(query, collection, n_results=3)
        except Exception as e:
            from aitest.infra.error_logger import log_error
            log_error("context_injector._resolve_rag_raw", "search_context", e,
                      {"query": query[:100], "collection": collection})
            return []

        # 同步填充字符串缓存（_resolve_rag 会用）
        from aitest.knowledge.rag_engine import RAG_DISTANCE_THRESHOLD
        lines = [
            r.get("document", "")[:500]
            for r in results
            if r.get("distance", 999) < RAG_DISTANCE_THRESHOLD and r.get("document")
        ]
        self._rag_cache[cache_key] = "\n".join(lines)

        return results

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

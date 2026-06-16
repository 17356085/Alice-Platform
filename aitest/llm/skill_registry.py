"""
Skill 能力分级矩阵 — 标记每个 Skill 的最低模型要求。

设计目的:
  1. Agent Runner 在执行前自动检查模型能力是否匹配
  2. 用户使用低能力模型时给出降级建议
  3. 机械化 Skill（如 code-consistency-checker）不消耗 LLM Token

用法:
    from aitest.llm.skill_registry import get_skill_requirements, check_provider_compatibility
    req = get_skill_requirements("automation/tech-analysis")
    compat = check_provider_compatibility("automation/tech-analysis", "ollama")
"""


# ══════════════════════════════════════════════════════════════════════════
#  Skill → 最低模型要求
# ══════════════════════════════════════════════════════════════════════════

SKILL_REQUIREMENTS = {
    # === project ===
    "project/project-context-manager": {
        "min_tier": "medium",
        "requires_tools": True,
        "max_input_tokens": 8000,
        "description": "项目初始化——读取代码仓库结构，生成 PROJECT_CONTEXT",
    },
    "project/context-sync": {
        "min_tier": "low",
        "requires_tools": False,
        "max_input_tokens": 4000,
        "description": "会话同步——读写 CURRENT_TASK.md",
    },

    # === requirements ===
    "requirements/module-modeling": {
        "min_tier": "medium",
        "requires_tools": False,
        "max_input_tokens": 8000,
        "description": "模块建模——分析模块边界和业务逻辑",
    },
    "requirements/requirement-analysis": {
        "min_tier": "medium",
        "requires_tools": False,
        "max_input_tokens": 8000,
        "description": "需求分析——结构化需求文档",
    },

    # === test-design ===
    "test-design/page-analysis": {
        "min_tier": "medium",
        "requires_tools": True,
        "max_input_tokens": 12000,
        "description": "页面分析——解析 HTML/截图，提取元素清单和交互模式",
    },
    "test-design/risk-modeling": {
        "min_tier": "medium",
        "requires_tools": False,
        "max_input_tokens": 8000,
        "description": "风险建模——6 维度风险识别",
    },
    "test-design/testcase-design": {
        "min_tier": "medium",
        "requires_tools": False,
        "max_input_tokens": 10000,
        "description": "测试用例设计——8 维度覆盖",
    },
    "test-design/test-data-generation": {
        "min_tier": "low",
        "requires_tools": False,
        "max_input_tokens": 4000,
        "description": "测试数据生成——边界值/等价类",
    },
    "test-design/api-testing": {
        "min_tier": "medium",
        "requires_tools": False,
        "max_input_tokens": 6000,
        "description": "API 测试设计",
    },
    "test-design/miniapp-testing": {
        "min_tier": "medium",
        "requires_tools": False,
        "max_input_tokens": 6000,
        "description": "小程序测试设计",
    },

    # === automation ===
    "automation/tech-analysis": {
        "min_tier": "high",
        "requires_tools": True,
        "max_input_tokens": 16000,
        "description": "技术分析——定位器设计 + Element Plus 深度识别 + 等待策略（最复杂的 Skill 之一）",
    },
    "automation/auto-strategy": {
        "min_tier": "medium",
        "requires_tools": False,
        "max_input_tokens": 8000,
        "description": "自动化策略决策",
    },
    "automation/page-object-generator": {
        "min_tier": "high",
        "requires_tools": False,
        "max_input_tokens": 12000,
        "description": "Page Object 代码生成——继承 BasePage、定位器规范、代码红线",
    },
    "automation/test-script-generator": {
        "min_tier": "high",
        "requires_tools": False,
        "max_input_tokens": 12000,
        "description": "pytest 测试脚本生成——fixture、参数化、断言",
    },
    "automation/conftest-generator": {
        "min_tier": "medium",
        "requires_tools": False,
        "max_input_tokens": 6000,
        "description": "conftest.py 生成——fixture 定义",
    },
    "automation/code-consistency-checker": {
        "min_tier": "mechanical",
        "requires_tools": False,
        "max_input_tokens": 0,
        "description": "代码合规检查——机械化 grep 扫描，不调用 LLM",
        "mechanical": True,
    },

    # === execution ===
    "execution/allure-report-analyzer": {
        "min_tier": "medium",
        "requires_tools": False,
        "max_input_tokens": 10000,
        "description": "Allure 报告分析——JSON 解析 + 摘要生成",
    },

    # === diagnosis ===
    "diagnosis/bug-analysis": {
        "min_tier": "high",
        "requires_tools": True,
        "max_input_tokens": 20000,
        "description": "Bug 根因分析——日志解读 + RAG 已知问题匹配 + 修复建议",
    },
    "diagnosis/ci-pipeline-analysis": {
        "min_tier": "medium",
        "requires_tools": True,
        "max_input_tokens": 10000,
        "description": "CI Pipeline 分析——Jenkins 日志解读",
    },
    "diagnosis/jenkinsfile-generator": {
        "min_tier": "medium",
        "requires_tools": False,
        "max_input_tokens": 8000,
        "description": "Jenkinsfile 生成——Pipeline 配置",
    },

    # === knowledge ===
    "knowledge/knowledge-manager": {
        "min_tier": "low",
        "requires_tools": False,
        "max_input_tokens": 6000,
        "description": "知识管理——提取 + 沉淀 + 去重",
    },
    "knowledge/completeness-check": {
        "min_tier": "low",
        "requires_tools": False,
        "max_input_tokens": 4000,
        "description": "文档完整性审计",
    },

    # === reporting ===
    "reporting/report-generator": {
        "min_tier": "low",
        "requires_tools": False,
        "max_input_tokens": 6000,
        "description": "报告生成——测试总结 + 进度报告 + Excel 导出",
    },
}

# ── 开发 Skills 需求 ──
DEV_SKILL_REQUIREMENTS: dict[str, dict] = {
    "architecture/project-scanner": {
        "min_tier": "medium",
        "requires_tools": False,
        "max_input_tokens": 8000,
        "description": "项目扫描——分析目录结构、识别框架和入口文件",
    },
    "architecture/tech-stack-decider": {
        "min_tier": "medium",
        "requires_tools": False,
        "max_input_tokens": 8000,
        "description": "技术栈决策——分析依赖、推荐版本、记录决策理由",
    },
    "architecture/component-tree-designer": {
        "min_tier": "medium",
        "requires_tools": False,
        "max_input_tokens": 8000,
        "description": "组件树设计——页面-组件层级、Props/Events 接口、路由映射",
    },
    "architecture/api-contract-designer": {
        "min_tier": "high",
        "requires_tools": False,
        "max_input_tokens": 10000,
        "description": "API 契约设计——REST 端点、Schema 定义、错误码规范",
    },
    "frontend/vue-component-generator": {
        "min_tier": "high",
        "requires_tools": False,
        "max_input_tokens": 12000,
        "description": "Vue 3 组件生成——从 Props 接口生成完整 SFC（含模板、脚本、样式）",
    },
    "frontend/page-implementer": {
        "min_tier": "high",
        "requires_tools": False,
        "max_input_tokens": 12000,
        "description": "页面实现——组装子组件、数据获取、状态管理、路由集成",
    },
    "frontend/frontend-lint-checker": {
        "min_tier": "mechanical",
        "requires_tools": False,
        "max_input_tokens": 0,
        "description": "前端 Lint 检查——ESLint + TypeScript 编译 + 红线 grep（机械化）",
        "mechanical": True,
    },
    "backend/fastapi-router-generator": {
        "min_tier": "high",
        "requires_tools": False,
        "max_input_tokens": 12000,
        "description": "FastAPI Router 生成——从 API 契约生成完整端点代码",
    },
    "backend/pydantic-schema-generator": {
        "min_tier": "medium",
        "requires_tools": False,
        "max_input_tokens": 8000,
        "description": "Pydantic v2 Schema 生成——从 API 契约的 Schema 定义生成 BaseModel",
    },
    "backend/sqlalchemy-model-generator": {
        "min_tier": "medium",
        "requires_tools": False,
        "max_input_tokens": 8000,
        "description": "SQLAlchemy 2.0 Model 生成——从数据模型生成 ORM 映射代码",
    },
    "backend/backend-consistency-checker": {
        "min_tier": "mechanical",
        "requires_tools": False,
        "max_input_tokens": 0,
        "description": "后端一致性检查——import 完整性 + endpoint 覆盖率 + 红线 grep（机械化）",
        "mechanical": True,
    },
}

# 合并（供查询函数统一查找）
_ALL_SKILL_REQUIREMENTS = {**SKILL_REQUIREMENTS, **DEV_SKILL_REQUIREMENTS}

# ── 别名映射（简化 ID → 完整 ID）──
_ALIAS_MAP = {}
for full_id in SKILL_REQUIREMENTS:
    simple = full_id.split("/")[-1] if "/" in full_id else full_id
    if simple not in _ALIAS_MAP:
        _ALIAS_MAP[simple] = full_id


# ══════════════════════════════════════════════════════════════════════════
#  Provider 能力定义
# ══════════════════════════════════════════════════════════════════════════

PROVIDER_CAPABILITIES = {
    "claude-sonnet-4-6":    {"tier": "high",    "tools": True,  "max_tokens": 200000},
    "claude-sonnet-4":      {"tier": "high",    "tools": True,  "max_tokens": 200000},
    "claude-haiku-4-5":     {"tier": "medium",  "tools": True,  "max_tokens": 200000},
    "claude-opus-4-8":      {"tier": "high",    "tools": True,  "max_tokens": 200000},
    "gpt-4o":               {"tier": "high",    "tools": True,  "max_tokens": 128000},
    "gpt-4o-mini":          {"tier": "medium",  "tools": True,  "max_tokens": 128000},
    "gpt-4.1":              {"tier": "high",    "tools": True,  "max_tokens": 1000000},
    "qwen3-235b":           {"tier": "high",    "tools": False, "max_tokens": 131072},
    "qwen3-72b":            {"tier": "medium",  "tools": False, "max_tokens": 131072},
    "qwen3-14b":            {"tier": "medium",  "tools": False, "max_tokens": 32768},
    "qwen3-8b":             {"tier": "low",     "tools": False, "max_tokens": 32768},
    "llama3-70b":           {"tier": "medium",  "tools": False, "max_tokens": 8192},
    "llama3-8b":            {"tier": "low",     "tools": False, "max_tokens": 8192},
    "deepseek-v3":          {"tier": "high",    "tools": False, "max_tokens": 131072},
}


# Tier 排序（用于比较）
TIER_ORDER = {"mechanical": 0, "low": 1, "medium": 2, "high": 3}


# ══════════════════════════════════════════════════════════════════════════
#  查询 API
# ══════════════════════════════════════════════════════════════════════════

def get_skill_requirements(skill_id: str) -> dict:
    """获取 Skill 的模型要求。

    返回:
        {"min_tier": "high", "requires_tools": True, "max_input_tokens": 16000, ...}
        未找到时返回默认值 {"min_tier": "medium", ...}
    """
    # 精确匹配
    if skill_id in SKILL_REQUIREMENTS:
        return SKILL_REQUIREMENTS[skill_id]
    if skill_id in DEV_SKILL_REQUIREMENTS:
        return DEV_SKILL_REQUIREMENTS[skill_id]

    # 别名匹配
    full_id = _ALIAS_MAP.get(skill_id)
    if full_id and full_id in SKILL_REQUIREMENTS:
        return SKILL_REQUIREMENTS[full_id]

    # 模糊匹配（名字尾部）
    for rid, req in SKILL_REQUIREMENTS.items():
        if rid.endswith(skill_id) or rid.endswith(f"/{skill_id}"):
            return req
    for rid, req in DEV_SKILL_REQUIREMENTS.items():
        if rid.endswith(skill_id) or rid.endswith(f"/{skill_id}"):
            return req

    # 默认
    return {
        "min_tier": "medium",
        "requires_tools": False,
        "max_input_tokens": 8000,
        "description": f"Unknown skill: {skill_id}",
    }


def check_provider_compatibility(
    skill_id: str,
    provider_name: str,
    model: str = None,
) -> dict:
    """
    检查 Provider+模型 是否满足 Skill 要求。

    返回:
        {
            "compatible": True/False,
            "skill_tier": "high",
            "provider_tier": "medium",
            "warnings": [...],
            "recommendations": [...]
        }
    """
    req = get_skill_requirements(skill_id)
    skill_tier = req["min_tier"]

    # 机械化 Skill — 永远兼容
    if skill_tier == "mechanical":
        return {
            "compatible": True,
            "skill_tier": "mechanical",
            "provider_tier": "mechanical",
            "warnings": [],
            "recommendations": [],
            "note": "此 Skill 不需要 LLM，机械化执行",
        }

    # 查找 Provider 能力（优先精确模型匹配，其次 provider 默认值）
    provider_info = PROVIDER_CAPABILITIES.get(model) if model else None
    if not provider_info:
        provider_info = PROVIDER_DEFAULTS.get(provider_name, {})

    provider_tier = provider_info.get("tier", _guess_provider_tier(provider_name))
    provider_has_tools = provider_info.get("tools", False)
    provider_max_tokens = provider_info.get("max_tokens", 8192)

    warnings = []
    recommendations = []

    # 检查 tier
    skill_rank = TIER_ORDER.get(skill_tier, 2)
    provider_rank = TIER_ORDER.get(provider_tier, 2)

    compatible = provider_rank >= skill_rank

    if provider_rank < skill_rank:
        warnings.append(
            f"模型能力不足：Skill 要求 {skill_tier} 级别，当前 Provider 为 {provider_tier} 级别。"
            f"建议切换到 Claude Sonnet 或 GPT-4o。"
        )
        recommendations.append("claude-sonnet-4-6")
        recommendations.append("gpt-4o")

    # 检查 tool calling
    if req.get("requires_tools") and not provider_has_tools:
        warnings.append(
            f"Skill 需要 Tool Calling 能力，当前 Provider 不支持。"
            f"请使用 Claude 或 GPT-4o 系列。"
        )
        compatible = False
        recommendations.append("claude-sonnet-4-6")

    # 检查 context 长度
    if req.get("max_input_tokens", 0) > provider_max_tokens:
        warnings.append(
            f"Skill 需要 {req['max_input_tokens']} tokens 输入，"
            f"当前 Provider 最大 {provider_max_tokens} tokens。"
            f"可能截断上下文。"
        )
        # 不阻止执行，但发出警告

    return {
        "compatible": compatible,
        "skill_tier": skill_tier,
        "provider_tier": provider_tier,
        "warnings": warnings,
        "recommendations": list(set(recommendations)),
    }


def list_skills_by_tier(tier: str) -> list[str]:
    """列出指定能力级别的所有 Skill ID。"""
    return [rid for rid, req in SKILL_REQUIREMENTS.items() if req["min_tier"] == tier]


def get_skill_stats() -> dict:
    """Skill 能力分布统计。"""
    stats = {"mechanical": 0, "low": 0, "medium": 0, "high": 0}
    for req in SKILL_REQUIREMENTS.values():
        tier = req["min_tier"]
        stats[tier] = stats.get(tier, 0) + 1
    return stats


def _guess_provider_tier(provider_name: str) -> str:
    """根据 Provider 名称猜测能力级别。"""
    if provider_name in ("claude", "openai", "deepseek"):
        return "high"
    elif provider_name == "ollama":
        return "low"
    return "medium"


# Provider 默认能力（当未指定具体模型时使用）
PROVIDER_DEFAULTS = {
    "claude": {"tier": "high", "tools": True, "max_tokens": 200000},
    "openai": {"tier": "high", "tools": True, "max_tokens": 128000},
    "deepseek": {"tier": "high", "tools": True, "max_tokens": 131072},
    "ollama": {"tier": "low", "tools": False, "max_tokens": 32768},
}

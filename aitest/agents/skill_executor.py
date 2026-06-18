"""Skill 执行引擎 — 加载、适配、LLM 调用。

从 agent_runner.py 抽取：AGENT_SKILL_MAP, run_skill(), 上下文注入。
"""
import time
from pathlib import Path

from aitest.llm.provider import LLMResponse, get_provider
from aitest.llm.skill_loader import load_skill
from aitest.llm.prompt_adapter import PromptAdapter
from aitest.llm.context_injector import ContextInjector
from aitest.llm.skill_registry import (
    get_skill_requirements,
    check_provider_compatibility,
)

# ── 路径配置 ──────────────────────────────────────────────
WORKSTUDY = Path(__file__).resolve().parent.parent.parent
GOVERNANCE = WORKSTUDY / "governance"

# P0-1b: 模块级单例 — RAG/文件缓存跨 Skill 共享
_shared_injector = ContextInjector()
_shared_adapter = PromptAdapter()


# ═══════════════════════════════════════════════════════════
#  Agent → Skill 映射
# ═══════════════════════════════════════════════════════════

def _load_agent_definitions() -> dict:
    """从 agent-definitions.yaml 加载 Agent 定义（单一事实源）。"""
    import yaml
    yaml_path = GOVERNANCE / "agents" / "agent-definitions.yaml"
    if not yaml_path.exists():
        return _FALLBACK_AGENT_SKILL_MAP
    with open(yaml_path, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f)
    agents = data.get("agents", {})
    result = {}
    for agent_id, defn in agents.items():
        if defn.get("is_orchestrator"):
            continue
        skills = defn.get("skills", [])
        if skills:
            result[agent_id] = skills
    return result


_FALLBACK_AGENT_SKILL_MAP = {
    "project-agent": [
        "project/project-context-manager", "project/context-sync",
        "project/hygiene-check", "knowledge/completeness-check",
    ],
    "requirement-agent": [
        "requirements/module-modeling", "requirements/requirement-analysis",
    ],
    "test-design-agent": [
        "test-design/page-analysis", "test-design/risk-modeling", "test-design/testcase-design",
    ],
    "automation-agent": [
        "automation/tech-analysis", "automation/auto-strategy",
        "automation/page-object-generator", "automation/test-script-generator",
        "automation/code-consistency-checker",
    ],
    "execution-agent": [
        "execution/allure-report-analyzer",
    ],
    "bug-analysis-agent": [
        "diagnosis/bug-analysis",
    ],
    "report-agent": [
        "reporting/report-generator",
    ],
    "knowledge-agent": [
        "knowledge/knowledge-manager",
    ],
}

AGENT_SKILL_MAP = _load_agent_definitions()


def _load_dev_agent_definitions() -> dict:
    """从 agent-definitions-dev.yaml 加载开发 Agent 定义。"""
    import yaml
    yaml_path = GOVERNANCE / "agents" / "agent-definitions-dev.yaml"
    if not yaml_path.exists():
        return {}
    with open(yaml_path, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f)
    agents = data.get("agents", {})
    return {
        agent_id: defn.get("skills", [])
        for agent_id, defn in agents.items()
        if not defn.get("is_orchestrator") and defn.get("skills")
    }


DEV_AGENT_SKILL_MAP = _load_dev_agent_definitions()
_ALL_SKILL_MAP = {**AGENT_SKILL_MAP, **DEV_AGENT_SKILL_MAP}

_AGENT_DEFINITIONS_CACHE = None


def _get_all_definitions() -> dict:
    """加载完整的 Agent 定义。"""
    global _AGENT_DEFINITIONS_CACHE
    if _AGENT_DEFINITIONS_CACHE is not None:
        return _AGENT_DEFINITIONS_CACHE
    import yaml
    yaml_path = GOVERNANCE / "agents" / "agent-definitions.yaml"
    if yaml_path.exists():
        with open(yaml_path, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f)
        _AGENT_DEFINITIONS_CACHE = data.get("agents", {})
    else:
        _AGENT_DEFINITIONS_CACHE = {}
    return _AGENT_DEFINITIONS_CACHE


def get_agent_definition(agent_name: str) -> dict:
    """获取一个 Agent 的完整定义。"""
    return _get_all_definitions().get(agent_name, {})


# 简化别名（保留向后兼容）
_ALIAS_MAP = {k.replace("-agent", ""): k for k in AGENT_SKILL_MAP}
for alias, full in _ALIAS_MAP.items():
    if alias not in AGENT_SKILL_MAP:
        AGENT_SKILL_MAP[alias] = AGENT_SKILL_MAP[full]


# ═══════════════════════════════════════════════════════════
#  run_skill() — 单个 Skill 执行
# ═══════════════════════════════════════════════════════════

def run_skill(
    skill_id: str, user_input: str, provider: str = "claude",
    context_vars: dict = None, temperature: float = 0.7,
    max_tokens: int = 8192, variant: str = None,
) -> LLMResponse:
    """执行单个 Skill: 加载 → 注入上下文 → 适配 → LLM 调用。"""
    context_vars = context_vars or {}
    start_time = time.time()

    try:
        system_prompt = load_skill(skill_id, variant=variant)
    except FileNotFoundError as e:
        return LLMResponse(content=f"[Skill 加载失败] {e}", model="none", finish_reason="error")

    # P0-1: 解析 Skill 版本
    try:
        from aitest.llm.skill_loader import resolve_skill_version
        from aitest.infra.trace import TraceContext
        ver_info = resolve_skill_version(skill_id)
        TraceContext.set(run_id=TraceContext.get_run_id(),
                        agent_name=TraceContext.get_agent_name(),
                        skill_version=ver_info.resolved_version)
    except Exception:
        pass

    # ★ P2 RAG: Token 预算感知 — 计算 max_chars 以确保不超预算
    token_budget_remaining = context_vars.get("token_budget_remaining", 8000)
    # RAG 结果最多消耗 token_budget_remaining 的 30%，保留 70% 给 LLM 输出
    max_rag_chars = max(500, int(token_budget_remaining * 0.3 * 4))  # chars ≈ tokens * 4

    system_prompt = _shared_injector.inject(skill_id, system_prompt, context_vars)
    inject_stats = getattr(_shared_injector, '_last_inject_stats', {})
    # 记录 token 预算限制
    if "token_budget_remaining" in context_vars:
        inject_stats["max_rag_chars_limit"] = max_rag_chars
    system_prompt = _shared_adapter.adapt(system_prompt, provider)

    compat = check_provider_compatibility(skill_id, provider)
    if not compat["compatible"]:
        compat["skill_id"] = skill_id
        return LLMResponse(
            content=f"[能力不兼容] {skill_id}\n" + "\n".join(compat["warnings"])
            + f"\n建议切换到: {', '.join(compat.get('recommendations', ['claude-sonnet-4-6']))}",
            model="none", finish_reason="error",
        )
    if compat.get("warnings"):
        system_prompt = f"[注意] {'; '.join(compat['warnings'])}\n\n" + system_prompt

    try:
        llm = get_provider(provider)
        response = llm.complete(system_prompt=system_prompt, user_prompt=user_input,
                                temperature=temperature, max_tokens=max_tokens)
    except ValueError as e:
        return LLMResponse(content=f"[Provider 初始化失败] {e}", model="none", finish_reason="error")

    elapsed = time.time() - start_time
    if response.token_usage:
        response.token_usage["elapsed_seconds"] = round(elapsed, 1)

    # P1-1: 追踪事件
    try:
        from aitest.infra.trace import TraceEvent, write_trace_event, TraceContext
        model_name = response.model or getattr(response, "model", "")
        token_in = response.token_usage.get("input", 0) if response.token_usage else 0
        token_out = response.token_usage.get("output", 0) if response.token_usage else 0
        event = TraceEvent.create(
            event_type="skill_execution", skill_id=skill_id, provider=provider,
            model=model_name, latency_ms=getattr(response, "latency_ms", int(elapsed * 1000)),
            token_input=token_in, token_output=token_out,
            status="success" if response.finish_reason != "error" else "error",
            response_preview=(response.content or ""),
            error_message=(response.content or "")[:300] if response.finish_reason == "error" else "",
            run_id=TraceContext.get_run_id(), agent_name=TraceContext.get_agent_name(),
            metadata={**inject_stats},
        )
        write_trace_event(event)
    except Exception:
        pass

    return response

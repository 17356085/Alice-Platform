"""
Agent Runner — 去平台化的 Agent 执行引擎。

P0 重构 (2026-06-12): 从顺序 for 循环升级为真正的 Agent 循环。
  Perceive → Plan → Act → Observe → Update → (loop)

功能:
  1. run_skill()     — 执行单个 Skill（加载 → 注入上下文 → 适配 → LLM 调用）
  2. run_agent()     — 兼容旧接口，内部委托给 AgentLoop
  3. AgentLoop       — 真正的 Agent 执行循环（新增）
  4. AGENT_SKILL_MAP — Agent → Skill 映射表（单一事实源）

用法:
    from aitest.agent_runner import run_skill, run_agent, AgentLoop, AGENT_SKILL_MAP

    # 方式 A: 单个 Skill
    response = run_skill("automation/tech-analysis", "...", provider="claude")

    # 方式 B: Agent 循环（真 Agent）
    agent = AgentLoop("automation-agent", module="equipment", page="alarm-config")
    state = agent.run()
    print(state.success, state.observations)

    # 方式 C: 兼容旧接口
    result = run_agent("automation-agent", module="equipment", page="alarm-config")
"""
import os
import re
import sys
import time
import queue
from pathlib import Path
from collections.abc import Generator
from dataclasses import dataclass, field
from typing import Optional, Literal

from aitest.llm.provider import LLMResponse, StreamEvent, get_provider
from aitest.llm.skill_loader import load_skill
from aitest.llm.prompt_adapter import PromptAdapter
from aitest.llm.context_injector import ContextInjector
from aitest.llm.skill_registry import (
    get_skill_requirements,
    check_provider_compatibility,
)

# ── 路径配置 ──────────────────────────────────────────────────────────
WORKSTUDY = Path(__file__).resolve().parent.parent
ZJSN_TEST = WORKSTUDY / "ZJSN_Test-master526"
GOVERNANCE = WORKSTUDY / "governance"
CONTEXT_MODULES = GOVERNANCE / "context" / "projects" / "web-automation" / "modules"

# P0-1b: 模块级单例 — RAG/文件缓存跨 Skill 共享
_shared_injector = ContextInjector()
_shared_adapter = PromptAdapter()


# ══════════════════════════════════════════════════════════════════════════
#  Agent → Skill 映射 — 从单一事实源加载
# ══════════════════════════════════════════════════════════════════════════

def _load_agent_definitions() -> dict:
    """从 agent-definitions.yaml 加载 Agent 定义（单一事实源）。"""
    import yaml
    yaml_path = GOVERNANCE / "agents" / "agent-definitions.yaml"
    if not yaml_path.exists():
        # 如果没有 YAML，返回硬编码的后备（保持向后兼容）
        return _FALLBACK_AGENT_SKILL_MAP
    with open(yaml_path, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f)
    agents = data.get("agents", {})
    result = {}
    for agent_id, defn in agents.items():
        if defn.get("is_orchestrator"):
            continue  # full-sop 不是 Agent
        skills = defn.get("skills", [])
        if skills:
            result[agent_id] = skills
    return result


# 后备定义（仅在 agent-definitions.yaml 不存在时使用）
_FALLBACK_AGENT_SKILL_MAP = {
    "project-agent": [
        "project/project-context-manager",
        "project/context-sync",
        "project/hygiene-check",
        "knowledge/completeness-check",
    ],
    "requirement-agent": [
        "requirements/module-modeling",
        "requirements/requirement-analysis",
    ],
    "test-design-agent": [
        "test-design/page-analysis",       # P1-2: page-interface-generator 已合并为 page-analysis 的后处理
        "test-design/risk-modeling",
        "test-design/testcase-design",
    ],
    "automation-agent": [
        "automation/tech-analysis",
        "automation/auto-strategy",
        "automation/page-object-generator",
        "automation/test-script-generator",      # P1-2: conftest-generator 已合并为本 Skill 的附带产出
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

# 单一事实源
AGENT_SKILL_MAP = _load_agent_definitions()

# ── 开发 Agent 映射 ──
def _load_dev_agent_definitions() -> dict:
    """从 agent-definitions-dev.yaml 加载开发 Agent 定义。"""
    import yaml
    yaml_path = GOVERNANCE / "agents" / "agent-definitions-dev.yaml"
    if not yaml_path.exists():
        return {}
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


DEV_AGENT_SKILL_MAP = _load_dev_agent_definitions()

# 合并 skill map（供 AgentLoop 统一查找）
_ALL_SKILL_MAP = {**AGENT_SKILL_MAP, **DEV_AGENT_SKILL_MAP}

# 补充完整定义（从 YAML 加载全部字段）
_AGENT_DEFINITIONS_CACHE = None


def _get_all_definitions() -> dict:
    """加载完整的 Agent 定义（含 description, boundaries, modes 等）。"""
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
    """获取一个 Agent 的完整定义（description, skills, boundaries, modes 等）。"""
    defs = _get_all_definitions()
    return defs.get(agent_name, {})


# 简化别名（保留向后兼容）
_ALIAS_MAP = {k.replace("-agent", ""): k for k in AGENT_SKILL_MAP}
for alias, full in _ALIAS_MAP.items():
    if alias not in AGENT_SKILL_MAP:
        AGENT_SKILL_MAP[alias] = AGENT_SKILL_MAP[full]


# ══════════════════════════════════════════════════════════════════════════
#  输出验证规则 — 每个 Skill 完成后检查什么
# ══════════════════════════════════════════════════════════════════════════

@dataclass
class ArtifactRule:
    """Skill 产出的验证规则。"""
    glob_pattern: str          # 文件 glob 模式，支持 {module} {page} {PageName}
    check_type: str = "exists_non_empty"  # exists | exists_non_empty | grep_pass | import_ok | pytest_collect
    grep_pattern: str = ""    # grep 应匹配到的内容
    grep_should_find: bool = True
    required: bool = True
    label: str = ""

# automation-agent 的产出验证规则（最完整的 Agent，作为真 Agent 原型）
AUTOMATION_ARTIFACT_RULES = {
    "automation/tech-analysis": [
        ArtifactRule(
            glob_pattern="{module_dir}/pages/{page}/TECH_ANALYSIS.md",
            label="TECH_ANALYSIS.md",
        ),
    ],
    "automation/auto-strategy": [
        ArtifactRule(
            glob_pattern="{module_dir}/pages/{page}/AUTO_STRATEGY.md",
            label="AUTO_STRATEGY.md",
        ),
    ],
    "automation/page-object-generator": [
        ArtifactRule(
            glob_pattern="ZJSN_Test-master526/page/{module}_page/{PageName}Page.py",
            label="PageObject 文件",
        ),
        # 8 条红线自检
        ArtifactRule(
            glob_pattern="ZJSN_Test-master526/page/{module}_page/{PageName}Page.py",
            check_type="grep_pass",
            grep_pattern=r"class \w+\(BasePage\):",
            label="继承 BasePage",
        ),
        ArtifactRule(
            glob_pattern="ZJSN_Test-master526/page/{module}_page/{PageName}Page.py",
            check_type="grep_pass",
            grep_pattern=r"//\*\[@id=",
            grep_should_find=False,
            label="禁止绝对 XPath",
            required=False,  # 警告但允许通过
        ),
        ArtifactRule(
            glob_pattern="ZJSN_Test-master526/page/{module}_page/{PageName}Page.py",
            check_type="grep_pass",
            grep_pattern=r"time\.sleep\(",
            grep_should_find=False,
            label="禁止 time.sleep",
        ),
        ArtifactRule(
            glob_pattern="ZJSN_Test-master526/page/{module}_page/{PageName}Page.py",
            check_type="grep_pass",
            grep_pattern=r"^[^#]*\bprint\(",
            grep_should_find=False,
            label="禁止 print 调试",
        ),
    ],
    "automation/test-script-generator": [
        ArtifactRule(
            glob_pattern="ZJSN_Test-master526/script/{module}/test_{page_underscore}.py",
            label="测试脚本文件",
        ),
        ArtifactRule(
            glob_pattern="ZJSN_Test-master526/script/{module}/test_{page_underscore}.py",
            check_type="grep_pass",
            grep_pattern=r"def test_",
            label="包含 test_ 函数",
        ),
        ArtifactRule(
            glob_pattern="ZJSN_Test-master526/script/{module}/test_{page_underscore}.py",
            check_type="grep_pass",
            grep_pattern=r"time\.sleep\(",
            grep_should_find=False,
            label="禁止 time.sleep",
        ),
        # 注意: 不检查 test 文件的 BasePage 继承（test 文件不需要）
        ArtifactRule(
            glob_pattern="ZJSN_Test-master526/script/{module}/test_{page_underscore}.py",
            check_type="grep_pass",
            grep_pattern=r"^[^#]*\bprint\(",
            grep_should_find=False,
            label="禁止 print 调试",
            required=False,
        ),
        # P1-2: conftest.py 合并为 test-script-generator 的附带产出
        ArtifactRule(
            glob_pattern="ZJSN_Test-master526/script/{module}/conftest.py",
            label="conftest.py",
            required=False,  # conftest.py 可能跨页面共享，不强要求每页面都有
        ),
    ],
    "automation/code-consistency-checker": [
        # 此 Skill 本身是检查器，无需额外验证
    ],
}

# ── 开发 Agent 产出验证规则 ──
# 与 AUTOMATION_ARTIFACT_RULES 并行，用于开发 Skill 的产物检查
DEV_ARTIFACT_RULES = {
    "architecture/project-scanner": [
        ArtifactRule(
            glob_pattern="{module_dir}/PROJECT_STRUCTURE.md",
            label="PROJECT_STRUCTURE.md",
        ),
    ],
    "architecture/tech-stack-decider": [
        ArtifactRule(
            glob_pattern="{module_dir}/TECH_STACK.md",
            label="TECH_STACK.md",
        ),
    ],
    "architecture/component-tree-designer": [
        ArtifactRule(
            glob_pattern="{module_dir}/COMPONENT_TREE.md",
            label="COMPONENT_TREE.md",
        ),
    ],
    "architecture/api-contract-designer": [
        ArtifactRule(
            glob_pattern="{module_dir}/API_CONTRACTS.md",
            label="API_CONTRACTS.md",
        ),
    ],
    "frontend/vue-component-generator": [
        ArtifactRule(
            glob_pattern="{module_dir}/src/components/{PageName}.vue",
            label="Vue 组件文件",
        ),
        ArtifactRule(
            glob_pattern="{module_dir}/src/components/{PageName}.vue",
            check_type="grep_pass",
            grep_pattern=r"<script setup lang=\"ts\">",
            label="Composition API (<script setup lang=\"ts\">)",
        ),
        ArtifactRule(
            glob_pattern="{module_dir}/src/components/{PageName}.vue",
            check_type="grep_pass",
            grep_pattern=r": any",
            grep_should_find=False,
            label="禁止 any 类型",
        ),
    ],
    "backend/fastapi-router-generator": [
        ArtifactRule(
            glob_pattern="{module_dir}/routers/{page}.py",
            label="FastAPI Router 文件",
        ),
        ArtifactRule(
            glob_pattern="{module_dir}/routers/{page}.py",
            check_type="grep_pass",
            grep_pattern=r"async def",
            label="async def 端点",
        ),
    ],
    "backend/pydantic-schema-generator": [
        ArtifactRule(
            glob_pattern="{module_dir}/schemas/{page}.py",
            label="Pydantic Schema 文件",
        ),
        ArtifactRule(
            glob_pattern="{module_dir}/schemas/{page}.py",
            check_type="grep_pass",
            grep_pattern=r"model_config\s*=",
            label="Pydantic v2 model_config",
        ),
    ],
    "backend/sqlalchemy-model-generator": [
        ArtifactRule(
            glob_pattern="{module_dir}/models/{page}.py",
            label="SQLAlchemy Model 文件",
        ),
        ArtifactRule(
            glob_pattern="{module_dir}/models/{page}.py",
            check_type="grep_pass",
            grep_pattern=r"mapped_column",
            label="SQLAlchemy 2.0 mapped_column",
        ),
    ],
    "backend/backend-consistency-checker": [],
    "frontend/frontend-lint-checker": [],
}

# 合并产物规则（供 observe() 统一查找）
_ALL_ARTIFACT_RULES = {**AUTOMATION_ARTIFACT_RULES, **DEV_ARTIFACT_RULES}

# 针对 code-consistency-checker 的详细检查清单
CODE_REDLINE_CHECKS = [
    ("继承 BasePage", r"class \w+\(BasePage\):", True),
    ("绝对 XPath", r"//\*\[@id=", False),
    ("time.sleep 硬等待", r"time\.sleep\(", False),
    ("print 调试", r"^[^#]*\bprint\(", False),
    ("手动 URL 硬编码", r'get\("https?://', False),  # 弱检测
]


# ══════════════════════════════════════════════════════════════════════════
#  数据结构
# ══════════════════════════════════════════════════════════════════════════

@dataclass
class Observation:
    """Agent 执行一步 Skill 后的观察结果。"""
    skill_id: str
    status: str = "pending"        # pass | fail | partial | skipped
    artifacts_found: list[str] = field(default_factory=list)
    artifacts_missing: list[str] = field(default_factory=list)
    quality_issues: list[str] = field(default_factory=list)
    summary: str = ""
    suggestion: str = "continue"   # continue | retry | skip | abort
    raw_output_preview: str = ""
    token_usage: dict = field(default_factory=dict)
    # P1-1: 追踪字段
    timestamp: str = ""
    latency_ms: int = 0
    model_name: str = ""
    run_id: str = ""

    def __post_init__(self):
        if not self.timestamp:
            from datetime import datetime
            self.timestamp = datetime.now().isoformat()


@dataclass
class AgentState:
    """Agent 跨步骤的内部状态。"""
    agent_name: str
    goal: str = ""
    module: str = ""
    page: str = ""
    provider: str = "claude"
    step: int = 0
    max_steps: int = 12
    current_skill: str = ""
    completed_skills: list[str] = field(default_factory=list)
    failed_skills: dict = field(default_factory=dict)    # skill_id → error summary
    retry_counts: dict = field(default_factory=dict)     # skill_id → retry count
    observations: list[Observation] = field(default_factory=list)
    artifacts: dict = field(default_factory=dict)        # skill_id → output summary
    memory: dict = field(default_factory=dict)           # accumulated knowledge
    done: bool = False
    success: bool = False
    termination_reason: str = ""

    def to_dict(self) -> dict:
        return {
            "agent_name": self.agent_name,
            "goal": self.goal,
            "module": self.module,
            "page": self.page,
            "provider": self.provider,
            "step": self.step,
            "completed_skills": self.completed_skills,
            "failed_skills": self.failed_skills,
            "retry_counts": self.retry_counts,
            "observations": [
                {
                    "skill_id": o.skill_id,
                    "status": o.status,
                    "artifacts_found": o.artifacts_found,
                    "artifacts_missing": o.artifacts_missing,
                    "quality_issues": o.quality_issues,
                    "summary": o.summary,
                    "suggestion": o.suggestion,
                    "token_usage": o.token_usage,
                    "timestamp": o.timestamp,
                    "latency_ms": o.latency_ms,
                    "model_name": o.model_name,
                    "run_id": o.run_id,
                }
                for o in self.observations
            ],
            "memory": self.memory,
            "artifacts": self.artifacts,
            "done": self.done,
            "success": self.success,
            "termination_reason": self.termination_reason,
        }


# ══════════════════════════════════════════════════════════════════════════
#  AgentEvent — 交互式 Agent 的事件协议
# ══════════════════════════════════════════════════════════════════════════

AgentEventType = Literal[
    "agent_start", "agent_end",
    "perceive", "plan", "plan_result",
    "skill_start", "skill_chunk", "skill_end",
    "observation", "observation_issue",
    "interaction_required",
    "phase_complete", "agent_message",
    "sop_start",        # SOP 流水线启动
    "sop_phase",        # SOP 阶段状态更新 (running/pass/fail)
    "sop_complete",     # SOP 流水线完成
]


@dataclass
class AgentEvent:
    """
    run_interactive() 产生的单个事件。

    用于流式 Chat UI：每个事件对应一个可展示的状态变化。
    interaction_required 事件暂停执行，等待外部输入。
    """
    type: AgentEventType
    skill_id: str = ""
    content: str = ""                          # skill_chunk 文本增量 / agent_message 消息
    stream_event: Optional[StreamEvent] = None # 原始 LLM 流事件（skill_chunk 时设置）
    observation: Optional[Observation] = None  # observation 事件
    interaction_id: str = ""                   # interaction_required 的唯一 ID
    interaction_type: str = ""                 # approve_retry | approve_strategy | input_required
    interaction_prompt: str = ""               # 展示给用户的提示
    interaction_options: list = field(default_factory=list)  # ["approve","reject","skip"]
    status: str = ""                           # pass | fail | partial | skipped
    summary: str = ""
    progress: dict = field(default_factory=dict)  # {"step": 1, "total": 5}
    token_usage: dict = field(default_factory=dict)
    error: str = ""


# ══════════════════════════════════════════════════════════════════════════
#  run_skill() — 单个 Skill 执行（不变，保持向后兼容）
# ══════════════════════════════════════════════════════════════════════════

def run_skill(
    skill_id: str,
    user_input: str,
    provider: str = "claude",
    context_vars: dict = None,
    temperature: float = 0.7,
    max_tokens: int = 8192,
    variant: str = None,
) -> LLMResponse:
    """
    执行单个 Skill。

    流程:
      1. 加载 Skill Prompt（从 governance/skills/，支持 variant 参数）
      2. 注入上下文（根据 SKILL_CONTEXT_MAP，通过 RAG 或文件读取）
      3. 适配 Prompt 到目标 LLM Provider
      4. 调用 LLM

    参数:
        skill_id:     "category/skill-name" 如 "automation/tech-analysis"
        user_input:   用户输入/任务描述
        provider:     "claude" | "openai" | "ollama"
        context_vars: 上下文变量（如 {"module": "equipment", "page": "alarm-config"}）
        temperature:  随机性 (0.0-1.0)
        max_tokens:   最大输出 token

    返回:
        LLMResponse(content, token_usage, model, ...)
    """
    context_vars = context_vars or {}
    start_time = time.time()

    # 1. 加载 Skill Prompt
    try:
        system_prompt = load_skill(skill_id, variant=variant)
    except FileNotFoundError as e:
        return LLMResponse(
            content=f"[Skill 加载失败] {str(e)}",
            model="none",
            finish_reason="error",
        )

    # P0-1: 解析 Skill 版本，设置到 TraceContext
    try:
        from aitest.llm.skill_loader import resolve_skill_version
        ver_info = resolve_skill_version(skill_id)
        skill_version = ver_info.resolved_version
        from aitest.trace import TraceContext
        TraceContext.set(
            run_id=TraceContext.get_run_id(),
            agent_name=TraceContext.get_agent_name(),
            skill_version=skill_version,
        )
    except Exception:
        skill_version = ""

    # 2. 注入上下文 (P0-1b: 模块级单例，跨 Skill 共享 RAG/文件缓存)
    system_prompt = _shared_injector.inject(skill_id, system_prompt, context_vars)
    # P0 可观测性: 记录本次注入的上下文统计
    inject_stats = getattr(_shared_injector, '_last_inject_stats', {})

    # 3. 适配 Prompt (P0-1b: 单例，无状态，省对象创建)
    system_prompt = _shared_adapter.adapt(system_prompt, provider)

    # 3.5 能力兼容性检查
    compat = check_provider_compatibility(skill_id, provider)
    if not compat["compatible"]:
        compat["skill_id"] = skill_id
        return LLMResponse(
            content=(
                f"[能力不兼容] {skill_id}\n"
                + "\n".join(compat["warnings"])
                + f"\n建议切换到: {', '.join(compat.get('recommendations', ['claude-sonnet-4-6']))}"
            ),
            model="none",
            finish_reason="error",
        )
    if compat.get("warnings"):
        system_prompt = (
            f"[注意] {'; '.join(compat['warnings'])}\n\n" + system_prompt
        )

    # 4. 调用 LLM
    try:
        llm = get_provider(provider)
        response = llm.complete(
            system_prompt=system_prompt,
            user_prompt=user_input,
            temperature=temperature,
            max_tokens=max_tokens,
        )
    except ValueError as e:
        return LLMResponse(
            content=f"[Provider 初始化失败] {str(e)}",
            model="none",
            finish_reason="error",
        )

    elapsed = time.time() - start_time
    if response.token_usage:
        response.token_usage["elapsed_seconds"] = round(elapsed, 1)

    # P1-1: 发射 skill_execution 追踪事件
    try:
        from aitest.trace import TraceEvent, write_trace_event, TraceContext
        model_name = response.model or getattr(response, "model", "")
        token_in = response.token_usage.get("input", 0) if response.token_usage else 0
        token_out = response.token_usage.get("output", 0) if response.token_usage else 0
        trace_latency = getattr(response, "latency_ms", int(elapsed * 1000))
        event = TraceEvent.create(
            event_type="skill_execution",
            skill_id=skill_id,
            provider=provider,
            model=model_name,
            latency_ms=trace_latency,
            token_input=token_in,
            token_output=token_out,
            status="success" if response.finish_reason != "error" else "error",
            response_preview=(response.content or ""),
            error_message=(response.content or "")[:300] if response.finish_reason == "error" else "",
            run_id=TraceContext.get_run_id(),
            agent_name=TraceContext.get_agent_name(),
            metadata={**inject_stats, "skill_version": skill_version},  # P0-1: 版本跟踪
        )
        write_trace_event(event)
    except Exception:
        pass  # 追踪失败不影响主流程

    return response


# ══════════════════════════════════════════════════════════════════════════
#  AgentLoop — 真正的 Agent 执行循环 (Perceive → Plan → Act → Observe)
# ══════════════════════════════════════════════════════════════════════════

class AgentLoop:
    """
    真正的 Agent 执行循环。

    不再是无脑的顺序 for 循环。
    Agent 每一步都会:
      1. Perceive — 通过 context_injector + RAG 感知当前环境
      2. Plan     — 决定下一步执行哪个 Skill（默认按 AGENT_SKILL_MAP 顺序，
                     失败时自主决定重试/跳过/中止）
      3. Act      — 调用 LLM 执行 Skill
      4. Observe  — 验证产出质量（文件存在性、代码红线检查等）
      5. Update   — 更新状态、发射事件

    用法:
        agent = AgentLoop("automation-agent", module="equipment", page="alarm-config")
        state = agent.run()
        print(f"成功: {state.success}, 步骤: {state.step}")
        for obs in state.observations:
            print(f"  {obs.skill_id}: {obs.status}")
    """

    MAX_RETRIES = 3  # 单个 Skill 最大重试次数

    def __init__(
        self,
        agent_name: str,
        provider: str = "claude",
        verbose: bool = True,
        skill_subset: list = None,  # ★ P1-3 HITL: None=全部Skill, list=仅运行指定子集
        deep_review: bool = True,   # ★ #6: code-consistency-checker 通过后触发 LLM 对抗性审查（默认开启）
        **context,
    ):
        if agent_name not in AGENT_SKILL_MAP and agent_name not in DEV_AGENT_SKILL_MAP:
            raise ValueError(
                f"Unknown agent: '{agent_name}'. "
                f"Available (test): {list(AGENT_SKILL_MAP.keys())}"
                f"Available (dev): {list(DEV_AGENT_SKILL_MAP.keys())}"
            )

        self.agent_name = agent_name
        self.provider = provider
        self.verbose = verbose
        self.context = context
        self._skill_subset = skill_subset  # None=全部Skill
        self.deep_review = deep_review      # ★ #6: LLM 深度审查开关
        self._review_triggered = False      # 防止重复触发
        self._interaction_queue: queue.Queue = queue.Queue()  # 交互式模式暂停通信

        module = context.get("module", "")
        page = context.get("page", "")
        goal = context.get("goal", "")

        if not goal:
            # 自动生成目标描述
            agent_display = agent_name.replace("-agent", "")
            goal_parts = [f"执行 {agent_display} 任务"]
            if module:
                goal_parts.append(f"模块={module}")
            if page:
                goal_parts.append(f"页面={page}")
            goal = "，".join(goal_parts)

        # P1-1: 生成 run_id 并设置 TraceContext
        import time as _time
        run_id = context.get("run_id") or f"sop-{module or 'unknown'}-{int(_time.time())}"
        self.run_id = run_id
        from aitest.trace import TraceContext
        TraceContext.set(run_id=run_id, agent_name=agent_name,
                         skill_version=TraceContext.get_skill_version())  # P0-1: 保留已设置的版本

        self.state = AgentState(
            agent_name=agent_name,
            goal=goal,
            module=module,
            page=page,
            provider=provider,
            max_steps=context.get("max_steps", len(self.skills) * 2),
        )

    def send_interaction(self, response: str) -> None:
        """供外部（Chat API）调用，向暂停中的 run_interactive() 发送用户输入。"""
        self._interaction_queue.put(response)

    # ── 属性 ──────────────────────────────────────────────────────

    @property
    def skills(self) -> list[str]:
        full = AGENT_SKILL_MAP.get(self.agent_name) or DEV_AGENT_SKILL_MAP.get(self.agent_name, [])
        if self._skill_subset is not None:
            return [s for s in full if s in self._skill_subset]
        return full

    @property
    def module(self) -> str:
        return self.state.module

    @property
    def page(self) -> str:
        return self.state.page

    # ── 辅助方法 ──────────────────────────────────────────────────

    def _log(self, msg: str) -> None:
        if self.verbose:
            # 替换 Unicode 字符为普通文本，避免编码问题
            msg = msg.replace("\U0001f916", "[AGENT]")
            msg = msg.replace("\U0001f914", "[PLAN]")
            msg = msg.replace("\U0001f916", "[ACT]")
            msg = msg.replace("\U0001f441", "[OBSERVE]")
            msg = msg.replace("\U0001f4ac", "[UPDATE]")
            msg = msg.replace("▶️", "[▶️]")
            msg = msg.replace("➡️", "[➡️]")
            msg = msg.replace("✅", "[✅]")
            msg = msg.replace("❌", "[❌]")
            msg = msg.replace("⏳", "[⏳]")
            msg = msg.replace("❗", "[⚠️]")
            msg = msg.replace("ℹ️", "[ℹ️]")
            msg = msg.replace("▶️", "[▶️]")
            msg = msg.replace("⏳", "[⏳]")
            print(msg)

    def _slug_to_page_name(self, slug: str) -> str:
        """alarm-config → AlarmConfig, unit-management → UnitManagement"""
        return "".join(part.capitalize() for part in slug.replace("-", " ").split())

    def _page_slug_to_underscore(self, slug: str) -> str:
        """alarm-config → alarm_config"""
        return slug.replace("-", "_")

    def _resolve_artifact_path(self, pattern: str) -> str:
        """将 glob pattern 中的变量替换为实际值。"""
        page_name = self._slug_to_page_name(self.page)
        resolved = pattern
        # 开发 Agent 使用 dev-platform 上下文路径
        if self.agent_name in DEV_AGENT_SKILL_MAP:
            module_dir = str(GOVERNANCE / "context" / "projects" / "dev-platform")
        else:
            module_dir = str(CONTEXT_MODULES / self.module)
        resolved = resolved.replace("{module_dir}", module_dir)
        resolved = resolved.replace("{module}", self.module)
        resolved = resolved.replace("{page}", self.page)
        resolved = resolved.replace("{PageName}", page_name)
        resolved = resolved.replace("{page_underscore}", self._page_slug_to_underscore(self.page))
        return resolved

    def _resolve_path(self, pattern: str) -> Path:
        """将 pattern 解析为绝对路径。"""
        resolved = self._resolve_artifact_path(pattern)
        if resolved.startswith("ZJSN_Test-master526"):
            resolved = str(WORKSTUDY / resolved)
        return Path(resolved)

    def _build_context_vars(self, extra: dict = None) -> dict:
        """构建传递给 run_skill 的上下文变量。"""
        vars_ = {
            "module": self.module,
            "page": self.page,
        }
        # 将 memory 中的关键信息注入
        if self.state.memory.get("prev_output"):
            vars_["prev_output"] = str(self.state.memory["prev_output"])[:3000]
        if self.state.memory.get("tech_analysis_summary"):
            vars_["tech_analysis_summary"] = self.state.memory["tech_analysis_summary"]
        if extra:
            vars_.update(extra)
        return vars_

    def _build_user_input(self, skill_id: str) -> str:
        """根据当前状态构造 Skill 的用户输入。"""
        parts = []
        if self.module:
            parts.append(f"模块: {self.module}")
        if self.page:
            parts.append(f"页面: {self.page}")
        if self.state.memory.get("task_description"):
            parts.append(f"任务: {self.state.memory['task_description']}")

        # 如果是重试，加入之前的错误反馈
        if skill_id in self.state.retry_counts:
            retry_n = self.state.retry_counts[skill_id]
            prev_obs = [o for o in self.state.observations if o.skill_id == skill_id]
            if prev_obs and prev_obs[-1].quality_issues:
                issues = "\n".join(f"  - {i}" for i in prev_obs[-1].quality_issues)
                parts.append(
                    f"\n⚠️ 第 {retry_n} 次重试。上一次执行存在以下问题，请修复:\n{issues}"
                )

        if not parts:
            return f"执行 {skill_id}"
        return "，".join(parts)

    # ── 1. Perceive（感知）───────────────────────────────────────

    def perceive(self, skill_id: str) -> dict:
        """
        感知当前环境——为即将执行的 Skill 收集上下文。

        返回上下文信息字典，包括:
          - injected_context: context_injector 注入的结果
          - rag_results: RAG 检索结果（如已知问题）
          - existing_files: 已存在的相关文件
        """
        info = {
            "skill_id": skill_id,
            "existing_files": [],
            "skip_candidate": False,
        }

        # 检查前置产出是否已存在（幂等性——已完成则跳过）
        rules = _ALL_ARTIFACT_RULES.get(skill_id, [])
        all_exist = False
        if rules:
            checks = []
            for rule in rules:
                if not rule.required:
                    continue
                path = self._resolve_path(rule.glob_pattern)
                exists = path.exists() and (path.stat().st_size > 0)
                checks.append(exists)
                if exists:
                    info["existing_files"].append(str(path))
            all_exist = len(checks) > 0 and all(checks)

        if all_exist and skill_id not in self.state.failed_skills:
            info["skip_candidate"] = True
            info["skip_reason"] = "所有必需产出已存在"

        return info

    # ── 2. Plan（规划：规则 + LLM 自主决策）───────────────────

    def plan(self, skill_index: int, perception: dict) -> dict:
        """
        决定下一步执行哪个 Skill。

        混合规划:
          - 确定情况（产物已存在/第一步/正常推进）→ 规则决策，零 Token
          - 模糊情况（失败重试/部分质量/上游问题）→ LLM 自主决策
        """
        # 规则 1: 产物已存在 → 确定跳过
        if perception.get("skip_candidate"):
            return {
                "action": "skip",
                "skill_id": self.skills[skill_index] if skill_index < len(self.skills) else "",
                "reason": perception.get("skip_reason", "产物已存在"),
            }

        # 规则 2: 上一步的观察结果决定
        if self.state.observations:
            last_obs = self.state.observations[-1]

            # 明确中止
            if last_obs.suggestion == "abort":
                return {"action": "abort", "skill_id": "", "reason": last_obs.summary}

            # 上次失败或部分成功 → 决策（P0-3: 规则优先，仅模糊情况调 LLM）
            if last_obs.suggestion in ("retry", "skip") or last_obs.status in ("fail", "partial"):
                retries = self.state.retry_counts.get(last_obs.skill_id, 0)
                if retries >= self.MAX_RETRIES:
                    return {
                        "action": "execute",
                        "skill_id": self.skills[skill_index] if skill_index < len(self.skills) else "",
                        "reason": f"已达最大重试次数 ({self.MAX_RETRIES})，强制推进",
                    }

                # ★ P0-3 规则3: code-consistency-checker 失败是确定性的 — 重试无效
                if last_obs.skill_id == "automation/code-consistency-checker" and last_obs.status == "fail":
                    return {
                        "action": "execute",
                        "skill_id": self.skills[skill_index] if skill_index < len(self.skills) else "",
                        "reason": "代码合规检查是确定性的（机械grep），重试不会改变结果",
                    }

                # ★ #6: code-consistency-checker mechanical 通过 → 可选 LLM 深度审查
                if (last_obs.skill_id == "automation/code-consistency-checker"
                        and last_obs.status == "pass"
                        and self.deep_review
                        and not self._review_triggered):
                    self._review_triggered = True
                    return {
                        "action": "execute",
                        "skill_id": "automation/code-consistency-checker:review",
                        "reason": "机械grep通过，触发LLM对抗性审查（定位器稳定性/等待策略/断言充分性）",
                    }

                # ★ P0-3 规则4: 文件产出连续缺失 — 不应再消耗 token
                if last_obs.status == "fail" and last_obs.artifacts_missing and retries >= 1:
                    return {
                        "action": "execute",
                        "skill_id": self.skills[skill_index] if skill_index < len(self.skills) else "",
                        "reason": f"文件产出连续 {retries+1} 次缺失，强制推进",
                    }

                # ★ P0-3 规则5: 部分质量问题重试后仍存 → 推进
                if last_obs.status == "partial" and retries >= 1:
                    return {
                        "action": "execute",
                        "skill_id": self.skills[skill_index] if skill_index < len(self.skills) else "",
                        "reason": "部分质量问题经重试仍存在，推进至下一 Skill",
                    }

                # LLM 自主决策：仅非确定性失败
                return self._llm_plan(skill_index, perception, last_obs)

        # 规则 3: 正常推进 — 执行下一个 Skill
        if skill_index < len(self.skills):
            return {
                "action": "execute",
                "skill_id": self.skills[skill_index],
                "reason": f"按计划执行 ({skill_index + 1}/{len(self.skills)})",
            }
        else:
            return {"action": "done", "skill_id": "", "reason": "所有 Skill 已处理"}

    def _llm_plan(self, skill_index: int, perception: dict, last_obs: Observation) -> dict:
        """
        LLM 自主决策下一步动作。

        在失败/部分成功/需要调整的模糊情况下，由 LLM 根据当前状态决定:
          - retry: 重试当前 Skill，可附带调整建议
          - execute: 跳过当前，执行下一个
          - replan: 回退到之前的某个 Skill（如上游分析错了）
          - skip: 跳过当前 Skill
          - abort: 无法修复，中止
        """
        # 构建规划 Prompt
        skills_summary = "\n".join(
            f"  [{i+1}] {s} — {'✅ 完成' if s in self.state.completed_skills else ('❌ 失败' if s in self.state.failed_skills else '⏳ 待执行')}"
            for i, s in enumerate(self.skills)
        )

        quality_issues = "\n".join(f"  - {i}" for i in last_obs.quality_issues[:5]) if last_obs.quality_issues else "无"

        prompt = f"""你是 Agent 规划器。根据当前状态决定下一步动作。

## 目标
{self.state.goal}

## Skill 链状态
{skills_summary}

## 当前 Skill
{last_obs.skill_id} — 状态: {last_obs.status}

## 质量问题
{quality_issues}

## 缺失产出
{', '.join(last_obs.artifacts_missing) if last_obs.artifacts_missing else '无'}

## 决策规则
- retry: 当前 Skill 可通过调整修复（定位器改CSS/加等待/修正选择器）
- execute: 当前问题不阻塞后续，先推进
- replan: 上游 Skill 产出有误，需要回头重做（指定 skill_id）
- skip: 当前 Skill 可跳过
- abort: 无法自动修复

## 输出 JSON
{{"action": "retry"|"execute"|"replan"|"skip"|"abort",
 "skill_id": "<目标 skill_id>",
 "reason": "<一句话理由>",
 "adjustments": "<retry 时的调整建议，其他动作为空>"}}"""

        try:
            from aitest.llm.provider import get_provider
            llm = get_provider(self.provider)
            # 使用较低 temperature 以获得确定性决策
            response = llm.complete(
                system_prompt="你是 CI 自动化测试 Agent 的规划器。根据当前状态做出最优决策。输出纯 JSON。",
                user_prompt=prompt,
                temperature=0.3,
                max_tokens=300,
            )
            content = response.content.strip()

            # P1-1: 发射 agent_decision 追踪事件
            try:
                from aitest.trace import TraceEvent, write_trace_event, TraceContext
                token_in = response.token_usage.get("input", 0) if response.token_usage else 0
                token_out = response.token_usage.get("output", 0) if response.token_usage else 0
                trace_latency = getattr(response, "latency_ms", 0)
                event = TraceEvent.create(
                    event_type="agent_decision",
                    skill_id="",
                    provider=self.provider,
                    model=response.model or "",
                    latency_ms=trace_latency,
                    token_input=token_in,
                    token_output=token_out,
                    status="success" if response.finish_reason != "error" else "error",
                    prompt_preview=prompt,
                    response_preview=content,
                    run_id=TraceContext.get_run_id(),
                    agent_name=TraceContext.get_agent_name(),
                )
                write_trace_event(event)
            except Exception:
                pass
            # 提取 JSON
            import json, re
            json_match = re.search(r'\{[^}]+\}', content)
            if json_match:
                decision = json.loads(json_match.group())
                action = decision.get("action", "execute")
                skill_id = decision.get("skill_id", "")
                reason = decision.get("reason", "LLM 决策")
                adjustments = decision.get("adjustments", "")

                # 如果 LLM 决定 retry，将调整建议注入 memory
                if action == "retry" and adjustments:
                    self.state.memory["retry_adjustments"] = adjustments
                    self._log(f"  💡 LLM 调整建议: {adjustments[:100]}")

                if action == "replan" and skill_id:
                    self._log(f"  🔄 LLM 决定回退: {skill_id}")
                    return {
                        "action": "execute",
                        "skill_id": skill_id,
                        "reason": f"LLM 决策: 回退重做 {skill_id} — {reason}",
                    }

                return {
                    "action": action if action in ("retry", "execute", "skip", "abort") else "execute",
                    "skill_id": skill_id if action == "replan" else (
                        last_obs.skill_id if action == "retry"
                        else (self.skills[skill_index] if skill_index < len(self.skills) else "")
                    ),
                    "reason": f"LLM 决策: {reason[:80]}",
                }
        except Exception as e:
            self._log(f"  ⚠️ LLM 规划失败 ({str(e)[:60]})，回退到规则决策")

        # 回退到规则决策
        return {
            "action": "execute",
            "skill_id": self.skills[skill_index] if skill_index < len(self.skills) else "",
            "reason": "LLM 规划失败，按计划推进",
        }

    # ── 3. Act（执行）────────────────────────────────────────────

    def act(self, skill_id: str) -> LLMResponse:
        """
        执行一个 Skill——调用 LLM 完成具体任务 + 自动保存产出到文件。

        如果是机械化 Skill（如 code-consistency-checker），直接运行本地脚本。
        如果是 review 模式（code-consistency-checker:review），运行 LLM 对抗性审查。
        """
        # ★ #6: LLM 深度审查模式 — 加载完整 Skill prompt，调用 LLM 审查代码质量
        if skill_id == "automation/code-consistency-checker:review":
            return self._act_llm_consistency_review()

        # 机械化 Skill 走本地脚本
        if skill_id == "automation/code-consistency-checker":
            return self._act_mechanical_consistency_check()

        context_vars = self._build_context_vars()
        user_input = self._build_user_input(skill_id)

        response = run_skill(
            skill_id=skill_id,
            user_input=user_input,
            provider=self.provider,
            context_vars=context_vars,
        )

        # API 模式下 LLM 无法自己写文件——AgentLoop 自动保存产出
        if response.finish_reason != "error" and response.content:
            self._save_skill_output(skill_id, response.content)

        return response

    def _save_skill_output(self, skill_id: str, content: str) -> str:
        """将 LLM 输出保存到对应的文件路径。返回保存路径或空字符串。"""
        # Skill → 目标文件映射
        page_name = self._slug_to_page_name(self.page)
        page_underscore = self._page_slug_to_underscore(self.page)

        SKILL_OUTPUT_MAP = {
            "automation/tech-analysis": (
                CONTEXT_MODULES / self.module / "pages" / self.page / "TECH_ANALYSIS.md",
                "md"
            ),
            "automation/auto-strategy": (
                CONTEXT_MODULES / self.module / "pages" / self.page / "AUTO_STRATEGY.md",
                "md"
            ),
            "automation/page-object-generator": (
                ZJSN_TEST / "page" / f"{self.module}_page" / f"{page_name}Page.py",
                "py"
            ),
            "automation/test-script-generator": [
                (ZJSN_TEST / "script" / self.module / f"test_{page_underscore}.py", "py"),
                (ZJSN_TEST / "script" / self.module / "conftest.py", "py"),  # P1-2: 合并 conftest 产出
            ],
            "test-design/page-analysis": [
                (CONTEXT_MODULES / self.module / "pages" / self.page / "PAGE_CONTEXT.md", "md"),
                # PAGE_INTERFACE.yaml — 可选的精简索引。如存在且小于 PAGE_CONTEXT.md，可用于快速索引。
                # 不再自动生成（page-interface-generator 已 deprecated）。以 PAGE_CONTEXT.md 为主源。
                (CONTEXT_MODULES / self.module / "pages" / self.page / "PAGE_INTERFACE.yaml", "yaml"),
            ],
            "test-design/risk-modeling": (
                CONTEXT_MODULES / self.module / "pages" / self.page / "RISK_MODEL.md",
                "md"
            ),
            "test-design/testcase-design": (
                CONTEXT_MODULES / self.module / "pages" / self.page / "TEST_CASES.md",
                "md"
            ),
        }

        target = SKILL_OUTPUT_MAP.get(skill_id)
        if not target:
            return ""  # 无对应文件映射的 Skill

        # P1-2: 支持单文件 (tuple) 和多文件 (list of tuples)
        targets = target if isinstance(target, list) else [target]

        saved_paths = []
        for file_path, file_type in targets:
            # 提取实际内容（.py 文件从 markdown code block 中提取）
            if file_type == "py":
                extracted = self._extract_code_block(content, "python")
                if not extracted:
                    extracted = self._extract_code_block(content, "py")
                if not extracted:
                    extracted = content  # 兜底：直接当代码保存
            else:
                extracted = content  # .md 直接保存

            # 确保目录存在
            file_path.parent.mkdir(parents=True, exist_ok=True)
            file_path.write_text(extracted, encoding="utf-8")
            self._log(f"  Saved: {file_path}")
            saved_paths.append(str(file_path))

        # P1-ACTIVATION (2026-06-15): Dead Path #6 修复 — ContextUpdated 事件
        # 当 Agent 产出任何文件时发射事件，通知 KnowledgeAgentSubscriber 同步
        if saved_paths:
            try:
                from aitest.event_bus import emit
                # 区分治理上下文 vs 测试代码产出
                gov_files = [p for p in saved_paths if "governance/context" in str(p).replace("\\", "/")]
                code_files = [p for p in saved_paths if p not in gov_files]
                if gov_files:
                    emit("ContextUpdated",
                         file=str(gov_files[0]),
                         changes=f"Agent {self.agent_name} updated {len(gov_files)} governance context file(s): {', '.join(str(Path(f).name) for f in gov_files)}")
                if code_files:
                    emit("ContextUpdated",
                         file=str(code_files[0]),
                         changes=f"Agent {self.agent_name} generated {len(code_files)} code file(s): {', '.join(str(Path(f).name) for f in code_files)}")
            except Exception as e:
                from aitest.error_logger import log_error
                log_error("agent_runner._save_skill_output", "emit_ContextUpdated", e,
                          {"agent": self.agent_name, "files": saved_paths})

        return saved_paths[0] if saved_paths else ""

    @staticmethod
    def _extract_yaml_block(text: str) -> str:
        """P1-7: 从 markdown 中提取 YAML code block。"""
        import re
        pattern = r'```yaml\s*\n(.*?)```'
        match = re.search(pattern, text, re.DOTALL)
        if match:
            return match.group(1).strip()
        # 尝试无 language 标记的 code block，检测是否为 YAML
        match = re.search(r'```\s*\n(.*?)```', text, re.DOTALL)
        if match:
            content = match.group(1).strip()
            if content.startswith("interface:") or content.startswith("meta:") or content.startswith("elements:"):
                return content
        return ""

    @staticmethod
    def _extract_code_block(text: str, language: str = "python") -> str:
        """从 markdown 中提取代码块。"""
        import re
        pattern = rf'```{language}\s*\n(.*?)```'
        match = re.search(pattern, text, re.DOTALL)
        if match:
            return match.group(1).strip()
        # 也尝试不带 language 标记的代码块
        match = re.search(r'```\s*\n(.*?)```', text, re.DOTALL)
        if match:
            return match.group(1).strip()
        return ""

    def _act_mechanical_consistency_check(self) -> LLMResponse:
        """机械化执行代码合规检查（不需要 LLM）。"""
        page_name = self._slug_to_page_name(self.page)
        po_file = ZJSN_TEST / "page" / f"{self.module}_page" / f"{page_name}Page.py"
        test_file = ZJSN_TEST / "script" / self.module / f"test_{self._page_slug_to_underscore(self.page)}.py"

        issues = []

        for fpath in [po_file, test_file]:
            if not fpath.exists():
                continue
            content = fpath.read_text(encoding="utf-8")
            is_po_file = "Page.py" in fpath.name
            is_test_file = fpath.name.startswith("test_")

            for label, pattern, should_find in CODE_REDLINE_CHECKS:
                # 继承 BasePage 检查仅适用于 PageObject 文件
                if "BasePage" in label and not is_po_file:
                    continue

                found = bool(re.search(pattern, content, re.MULTILINE))
                if found != should_find:
                    if should_find:
                        issues.append(f"{fpath.name}: 缺少 {label}（应包含 {pattern}）")
                    else:
                        # 找到具体违规行
                        for match in re.finditer(pattern, content, re.MULTILINE):
                            line_no = content[:match.start()].count("\n") + 1
                            matched_text = match.group().strip()[:60]
                            # print 检查：跳过 `def step(text):` 这种函数定义误匹配
                            if "print" in label and "def " in matched_text:
                                continue
                            issues.append(f"{fpath.name}:{line_no}: {label}（禁止模式: {matched_text}）")

        lines = []
        if issues:
            lines.append(f"FAIL: 代码合规检查发现 {len(issues)} 个问题:")
            for issue in issues:
                lines.append(f"  - {issue}")
        else:
            lines.append("PASS: 代码合规检查通过，无违规项。")

        # ★ U8: 持久化检查报告到 artifacts/code-review/
        self._persist_consistency_report(lines, issues)

        return LLMResponse(
            content="\n".join(lines),
            model="mechanical",
            finish_reason="stop",
            token_usage={"input": 0, "output": 0},
        )

    def _persist_consistency_report(self, lines: list[str], issues: list[str]) -> None:
        """将代码合规检查报告写入 artifacts/code-review/<module>/<page>/。"""
        try:
            report_dir = WORKSTUDY / "governance" / "artifacts" / "code-review" / self.module / self.page
            report_dir.mkdir(parents=True, exist_ok=True)
            report_path = report_dir / "consistency-check.md"
            timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
            report_content = f"# Code Consistency Check — {self.module}/{self.page}\n\n"
            report_content += f"**Time**: {timestamp}\n"
            report_content += f"**Module**: {self.module}\n"
            report_content += f"**Page**: {self.page}\n"
            report_content += f"**Issues**: {len(issues)}\n\n"
            for line in lines:
                report_content += f"{line}\n"
            report_path.write_text(report_content, encoding="utf-8")
        except Exception as e:
            self._log(f"  [warn] Failed to persist consistency report: {e}")

    def _act_llm_consistency_review(self) -> LLMResponse:
        """★ #6: LLM 对抗性审查 — 深度检查定位器稳定性、等待策略、断言充分性。

        与 mechanical grep 互补:
          - mechanical: 8 条红线硬检查 (0 tokens)
          - review: 定位器质量/等待策略/断言合理性 (~2K tokens)
        """
        page_name = self._slug_to_page_name(self.page)
        po_file = ZJSN_TEST / "page" / f"{self.module}_page" / f"{page_name}Page.py"
        test_file = ZJSN_TEST / "script" / self.module / f"test_{self._page_slug_to_underscore(self.page)}.py"

        # 收集待审查代码
        code_snippets = []
        for fpath in [po_file, test_file]:
            if fpath.exists():
                content = fpath.read_text(encoding="utf-8")
                code_snippets.append(f"### {fpath.name}\n```python\n{content[:3000]}\n```")

        if not code_snippets:
            return LLMResponse(
                content="PASS: 无代码文件可审查（文件不存在）",
                model="mechanical",
                finish_reason="stop",
                token_usage={"input": 0, "output": 0},
            )

        # 构建审查 prompt
        review_prompt = f"""你是自动化测试代码规范审查专家。对以下代码进行**对抗性深度审查**。

## 审查维度（grep 无法检测的问题）

1. **定位器稳定性**: CSS Selector 是否过于依赖动态类名？是否优先使用测试 id/data-testid？定位器是否可能在 Vue 重渲染后失效？
2. **等待策略**: 是否正确使用 wait_vue_stable？是否存在隐式等待依赖？弹窗/下拉框是否有显式等待？
3. **断言充分性**: 断言是否只检查表面文本而忽略数据正确性？分页/搜索后是否验证结果变化？
4. **Element Plus 坑位**: el-dialog 是否处理了 Teleport？el-select 选项是否在 body 下？el-cascader 是否有联动加载等待？
5. **异常处理**: 清理/重置操作是否有 try/finally？弹窗关闭失败是否有 fallback？

## 待审查代码

{chr(10).join(code_snippets)}

## 输出格式

```
### 深度审查报告

| # | 维度 | 严重度 | 位置 | 问题 | 建议修复 |
|---|------|--------|------|------|---------|

**总体评分**: X/10
**关键风险**: ...
```
"""
        try:
            response = run_skill(
                skill_id="automation/code-consistency-checker",
                user_input=review_prompt,
                provider=self.provider,
                context_vars=self._build_context_vars(),
            )
            # 持久化审查报告
            self._persist_review_report(response.content if response else "")
            return response or LLMResponse(
                content="REVIEW_FAILED: LLM 调用返回空",
                model="unknown",
                finish_reason="error",
                token_usage={"input": 0, "output": 0},
            )
        except Exception as e:
            self._log(f"  [warn] LLM review failed: {e}")
            return LLMResponse(
                content=f"REVIEW_ERROR: {str(e)[:200]}",
                model="error",
                finish_reason="error",
                token_usage={"input": 0, "output": 0},
            )

    def _persist_review_report(self, content: str) -> None:
        """将 LLM 审查报告写入 artifacts/code-review/<module>/<page>/。"""
        try:
            report_dir = WORKSTUDY / "governance" / "artifacts" / "code-review" / self.module / self.page
            report_dir.mkdir(parents=True, exist_ok=True)
            report_path = report_dir / "consistency-review-llm.md"
            timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
            report_content = f"# LLM Adversarial Code Review — {self.module}/{self.page}\n\n"
            report_content += f"**Time**: {timestamp}\n"
            report_content += f"**Module**: {self.module}\n"
            report_content += f"**Page**: {self.page}\n\n"
            report_content += content
            report_path.write_text(report_content, encoding="utf-8")
            self._log(f"  [review] Report persisted: {report_path}")
        except Exception as e:
            self._log(f"  [warn] Failed to persist review report: {e}")

    # ── 4. Observe（观察）────────────────────────────────────────

    def observe(self, skill_id: str, response: LLMResponse) -> Observation:
        """
        验证 Skill 产出质量。

        检查维度:
          - 文件存在性（必需产出文件是否生成）
          - 代码红线（grep 8 条规则）
          - LLM 响应是否异常
        """
        obs = Observation(
            skill_id=skill_id,
            raw_output_preview=response.content[:200] if response.content else "",
            token_usage=response.token_usage,
        )

        # 检查 LLM 响应异常
        if response.finish_reason == "error":
            obs.status = "fail"
            obs.summary = response.content[:200]
            obs.suggestion = "retry"
            obs.quality_issues.append(f"LLM 调用失败: {response.content[:100]}")
            return obs

        # 机械化 / LLM review Skill 的特殊处理
        if skill_id in ("automation/code-consistency-checker", "automation/code-consistency-checker:review"):
            is_review = skill_id.endswith(":review")
            if is_review:
                # LLM 审查：通过无"严重"级问题即视为 pass
                has_critical = any(
                    kw in response.content for kw in ["严重", "critical", "CRITICAL", "阻塞"]
                )
                obs.status = "fail" if has_critical else "pass"
                obs.suggestion = "continue"  # 审查不阻塞流程
                obs.summary = f"[LLM Review] {'发现严重问题' if has_critical else '无严重问题'}"
                obs.quality_issues = [
                    line.strip("- ").strip()
                    for line in response.content.split("\n")
                    if "严重" in line or "critical" in line.lower()
                ][:10]
                # ★ 审查报告已在 _act_llm_consistency_review 中持久化
                obs.artifacts_found = [
                    f"artifacts/code-review/{self.module}/{self.page}/consistency-review-llm.md"
                ]
            elif "PASS:" in response.content or "✅" in response.content:
                obs.status = "pass"
                obs.suggestion = "continue"
            else:
                # 机械检查发现违规——报告但继续（重试不会改变确定性结果）
                obs.status = "fail"
                obs.suggestion = "continue"  # 不是 "retry"——机械检查是确定性的
                for line in response.content.split("\n"):
                    if "FAIL:" in line or "❌" in line or "  - " in line:
                        obs.quality_issues.append(line.strip("- ").strip())
            if not is_review:
                obs.summary = response.content[:300]
            return obs

        # 检查产出文件
        rules = _ALL_ARTIFACT_RULES.get(skill_id, [])
        if rules:
            all_pass = True
            for rule in rules:
                path = self._resolve_path(rule.glob_pattern)

                if rule.check_type in ("exists_non_empty", "exists"):
                    if path.exists() and path.stat().st_size > 0:
                        obs.artifacts_found.append(str(path))
                    else:
                        if rule.required:
                            obs.artifacts_missing.append(f"{rule.label}: {path}")
                            all_pass = False
                        else:
                            # 可选检查失败只是警告
                            obs.quality_issues.append(f"[警告] {rule.label}: {path} 不存在或为空")

                elif rule.check_type == "grep_pass" and path.exists():
                    content = path.read_text(encoding="utf-8")
                    found = bool(re.search(rule.grep_pattern, content, re.MULTILINE))
                    if found != rule.grep_should_find:
                        label = rule.label or rule.grep_pattern
                        if rule.required:
                            obs.quality_issues.append(f"{label}: 检查未通过")
                            all_pass = False
                        else:
                            obs.quality_issues.append(f"[警告] {label}: 检查未通过")

            if all_pass and obs.artifacts_found:
                obs.status = "pass"
                obs.suggestion = "continue"
                obs.summary = f"产出 {len(obs.artifacts_found)} 个文件，验证通过"
            elif obs.artifacts_missing:
                obs.status = "fail"
                obs.suggestion = "retry"
                obs.summary = f"缺少 {len(obs.artifacts_missing)} 个必需产出"
            elif obs.quality_issues:
                obs.status = "partial"
                obs.suggestion = "retry"
                obs.summary = f"产出存在，但有 {len(obs.quality_issues)} 个质量问题"
            else:
                obs.status = "pass"
                obs.suggestion = "continue"
                obs.summary = "验证通过"
        else:
            # 无明确定义验证规则的 Skill——基本通过
            if response.content and len(response.content) > 50:
                obs.status = "pass"
                obs.suggestion = "continue"
                obs.summary = f"LLM 响应 {len(response.content)} 字符"
            else:
                obs.status = "partial"
                obs.suggestion = "retry"
                obs.summary = "LLM 响应过短"

        return obs

    # ── 5. Update（更新状态）──────────────────────────────────────

    def update(self, skill_id: str, observation: Observation) -> None:
        """根据观察结果更新 Agent 状态。"""
        observation_recorded = observation
        self.state.step += 1
        self.state.current_skill = skill_id
        self.state.observations.append(observation_recorded)

        if observation.status == "pass":
            self.state.completed_skills.append(skill_id)
            # 清除该 Skill 的重试计数
            self.state.retry_counts.pop(skill_id, None)
            # 保存产出摘要到 memory
            self.state.memory["prev_output"] = observation.summary

        elif observation.status in ("fail", "partial"):
            retries = self.state.retry_counts.get(skill_id, 0)
            self.state.retry_counts[skill_id] = retries + 1
            if skill_id not in self.state.completed_skills:
                self.state.failed_skills[skill_id] = observation.summary

        elif observation.status == "skipped":
            self.state.completed_skills.append(skill_id)

        # 发射里程碑事件
        self._maybe_emit_event(skill_id, observation)

    def _maybe_emit_event(self, skill_id: str, observation: Observation) -> None:
        """在关键里程碑发射事件到 Event Bus。

        P1-ACTIVATION (2026-06-15): 从 3 个硬编码 milestone 扩展到覆盖所有 Phase 的关键 Skill。
        每个 SOP Phase 至少 1 个 Skill 可触发 AgentCompleted。
        """
        milestones = [
            # Project Init
            "project/project-context-manager",
            # Requirement
            "requirements/module-modeling",
            "requirements/requirement-analysis",
            # Test Design
            "test-design/page-analysis",
            "test-design/risk-modeling",
            "test-design/testcase-design",
            # Automation
            "automation/tech-analysis",
            "automation/auto-strategy",
            "automation/page-object-generator",
            "automation/test-script-generator",
            "automation/code-consistency-checker",
            # Execute & Debug
            "execution/allure-report-analyzer",
            # Bug Analysis
            "diagnosis/bug-analysis",
            # Report
            "reporting/report-generator",
            # Knowledge
            "knowledge/knowledge-manager",
            "knowledge/completeness-check",
        ]
        if skill_id in milestones and observation.status == "pass":
            try:
                from aitest.event_bus import emit
                emit("AgentCompleted", agent=self.agent_name, module=self.module,
                     skill=skill_id, status="success")
            except Exception as e:
                from aitest.error_logger import log_error
                log_error("agent_runner._maybe_emit_event", "emit_agent_completed", e,
                          {"agent": self.agent_name, "module": self.module, "skill": skill_id})

    def _emit_cache_summary(self) -> None:
        """
        ★ P1 可观测性: Agent 结束时发射 cache_summary 追踪事件。

        汇总本 Agent 运行期间所有缓存的命中率。
        """
        try:
            from aitest.trace import TraceEvent, write_trace_event, TraceContext

            # ContextInjector 缓存统计
            injector_stats = _shared_injector.get_cache_stats()

            # Skill Prompt 缓存统计 (lru_cache)
            from aitest.llm.skill_loader import _load_skill_cached, _load_registry
            skill_cache_info = _load_skill_cached.cache_info()
            registry_cache_info = _load_registry.cache_info()

            # Preflight 缓存统计
            from aitest.graphs.sop_graph import _preflight_cache_hits as pf_hits, _preflight_cache_total as pf_total

            metadata = {
                "file_cache": injector_stats["file_cache"],
                "rag_cache": injector_stats["rag_cache"],
                "skill_prompt_cache": {
                    "hits": skill_cache_info.hits,
                    "misses": skill_cache_info.misses,
                    "rate": round(skill_cache_info.hits / (skill_cache_info.hits + skill_cache_info.misses), 3)
                    if (skill_cache_info.hits + skill_cache_info.misses) > 0 else None,
                },
                "registry_cache": {
                    "hits": registry_cache_info.hits,
                    "misses": registry_cache_info.misses,
                },
                "preflight_cache": {
                    "hits": pf_hits,
                    "total": pf_total,
                    "rate": round(pf_hits / pf_total, 3) if pf_total > 0 else None,
                },
            }

            event = TraceEvent.create(
                event_type="cache_summary",
                skill_id="",
                run_id=TraceContext.get_run_id() or self.run_id,
                agent_name=self.agent_name,
                metadata=metadata,
            )
            write_trace_event(event)
        except Exception:
            pass  # 统计失败不影响主流程

    # ── 主循环 ───────────────────────────────────────────────────

    def run(self) -> AgentState:
        """
        执行 Agent 主循环: Perceive → Plan → Act → Observe → Update

        循环直到:
          - 所有 Skill 完成
          - 达到最大步数
          - Agent 决定中止
        """
        self._log(f"🤖 Agent: {self.agent_name} | Provider: {self.provider}")
        self._log(f"  目标: {self.state.goal}")
        self._log(f"  Skill 链: {' → '.join(self.skills)}")
        self._log(f"  最大步数: {self.state.max_steps}")
        self._log("-" * 60)

        skill_index = 0  # 当前 Skill 在 skill_chain 中的位置

        while not self.state.done and self.state.step < self.state.max_steps:
            # ── 1. Perceive ──
            current_skill = self.skills[skill_index] if skill_index < len(self.skills) else ""
            perception = self.perceive(current_skill) if current_skill else {}

            # ── 2. Plan ──
            plan_result = self.plan(skill_index, perception)

            if plan_result["action"] == "done":
                self.state.done = True
                self.state.success = True
                self.state.termination_reason = "all_skills_completed"
                self._log("✅ 所有 Skill 已完成")
                break

            if plan_result["action"] == "abort":
                self.state.done = True
                self.state.success = False
                self.state.termination_reason = f"agent_aborted: {plan_result['reason']}"
                self._log(f"🛑 Agent 中止: {plan_result['reason']}")
                break

            if plan_result["action"] == "skip":
                skill_id = plan_result["skill_id"]
                self._log(f"  ⏭️ [{skill_index + 1}/{len(self.skills)}] {skill_id} — {plan_result['reason']}")
                obs = Observation(skill_id=skill_id, status="skipped",
                                  summary=plan_result["reason"], suggestion="continue")
                self.update(skill_id, obs)
                skill_index += 1
                continue

            # ── 3. Act ──
            skill_id = plan_result["skill_id"]
            is_retry = plan_result["action"] == "retry"

            if is_retry:
                retry_n = self.state.retry_counts.get(skill_id, 1)
                self._log(f"  🔄 [{skill_index + 1}/{len(self.skills)}] {skill_id} — 重试 #{retry_n}...")
            else:
                self._log(f"  ▶️  [{skill_index + 1}/{len(self.skills)}] {skill_id}...")

            response = self.act(skill_id)

            if not is_retry and response.finish_reason != "error":
                elapsed = response.token_usage.get("elapsed_seconds", 0)
                tokens_in = response.token_usage.get("input", 0)
                tokens_out = response.token_usage.get("output", 0)
                self._log(f"✅ {elapsed:.1f}s | {tokens_in}+{tokens_out} tokens")

            # ── 4. Observe ──
            observation = self.observe(skill_id, response)

            # ── 5. Update ──
            self.update(skill_id, observation)

            # 根据观察决定下一步
            if observation.suggestion == "retry":
                # 不增加 skill_index——下次循环 Plan 阶段会处理重试
                pass
            elif observation.suggestion == "skip":
                skill_index += 1
            else:  # "continue"
                skill_index += 1

            # 如果所有 Skill 都已处理
            if skill_index >= len(self.skills):
                # 检查是否所有 Skill 都通过
                all_pass = all(
                    s in self.state.completed_skills
                    for s in self.skills
                )
                self.state.done = True
                self.state.success = all_pass
                self.state.termination_reason = (
                    "all_skills_completed" if all_pass
                    else "some_skills_failed"
                )

        # ── 循环结束 ──
        if self.state.step >= self.state.max_steps and not self.state.done:
            self.state.done = True
            self.state.success = False
            self.state.termination_reason = "max_steps_reached"

        self._log("-" * 60)
        completed = len(self.state.completed_skills)
        failed = len(self.state.failed_skills)
        total_steps = self.state.step
        self._log(
            f"🏁 Agent 结束: {completed} 完成 / {failed} 失败 / "
            f"{total_steps} 步 | {self.state.termination_reason}"
        )

        # ★ P1 可观测性: 发射 cache_summary 追踪事件
        self._emit_cache_summary()

        return self.state

    # ── 交互式主循环 ───────────────────────────────────────────────

    def run_interactive(self) -> Generator[AgentEvent, None, AgentState]:
        """
        执行 Agent 主循环（交互式版本）。

        与 run() 的区别:
          - Skill 执行使用 stream_complete()，逐字 yield skill_chunk
          - 决策点 yield interaction_required，阻塞等待 send_interaction()
          - 全程 yield AgentEvent，供 Chat UI 消费

        yield AgentEvent 各种类型，最后 return AgentState。
        """
        total_skills = len(self.skills)
        yield AgentEvent(
            type="agent_start",
            skill_id=self.agent_name,
            content=f"开始执行 {self.agent_name}",
            progress={"step": 0, "total": total_skills},
        )

        skill_index = 0

        while not self.state.done and self.state.step < self.state.max_steps:
            # ── 1. Perceive ──
            current_skill = self.skills[skill_index] if skill_index < len(self.skills) else ""
            perception = self.perceive(current_skill) if current_skill else {}
            yield AgentEvent(type="perceive", skill_id=current_skill,
                             content=f"检查前置产物: {current_skill}",
                             progress={"step": skill_index + 1, "total": total_skills})

            # ── 2. Plan ──
            plan_result = self.plan(skill_index, perception)
            yield AgentEvent(
                type="plan_result",
                skill_id=plan_result.get("skill_id", ""),
                content=f"决策: {plan_result.get('action', '?')} — {plan_result.get('reason', '')}",
                progress={"step": skill_index + 1, "total": total_skills},
            )

            action = plan_result["action"]

            if action == "done":
                self.state.done = True
                self.state.success = True
                self.state.termination_reason = "all_skills_completed"
                yield AgentEvent(type="agent_message", content="所有 Skill 已完成")
                break

            if action == "abort":
                self.state.done = True
                self.state.success = False
                self.state.termination_reason = f"agent_aborted: {plan_result['reason']}"
                yield AgentEvent(type="agent_message",
                                 content=f"Agent 中止: {plan_result['reason']}",
                                 error=plan_result.get("reason", ""))
                break

            if action == "skip":
                skill_id = plan_result["skill_id"]
                obs = Observation(skill_id=skill_id, status="skipped",
                                  summary=plan_result["reason"], suggestion="continue")
                self.update(skill_id, obs)
                skill_index += 1
                yield AgentEvent(type="observation", skill_id=skill_id,
                                 status="skipped", summary=plan_result["reason"],
                                 progress={"step": skill_index, "total": total_skills})
                continue

            # ── 3. Act（流式）──
            skill_id = plan_result["skill_id"]
            is_retry = action == "retry"

            yield AgentEvent(
                type="skill_start",
                skill_id=skill_id,
                content=f"{'重试' if is_retry else '执行'} {skill_id}",
                progress={"step": skill_index + 1, "total": total_skills},
            )

            # 流式执行 Skill
            stream_response = self._act_stream(skill_id)
            if stream_response is None:
                # 机械化 Skill（如 code-consistency-checker）—— 直接调 complete()
                response = self.act(skill_id)
                yield AgentEvent(
                    type="skill_end",
                    skill_id=skill_id,
                    content=response.content[:300] if response.content else "",
                    token_usage=response.token_usage,
                )
            else:
                # 流式 LLM Skill
                response_text = ""
                for se in stream_response:
                    if se.type == "content_chunk":
                        response_text += se.content
                        yield AgentEvent(type="skill_chunk", skill_id=skill_id,
                                         content=se.content, stream_event=se)
                    elif se.type == "content_end":
                        pass
                    elif se.type == "done":
                        response = LLMResponse(
                            content=response_text,
                            token_usage=se.token_usage,
                            model="",
                            finish_reason=se.finish_reason or "stop",
                        )
                        yield AgentEvent(
                            type="skill_end",
                            skill_id=skill_id,
                            content=response_text[:300],
                            token_usage=se.token_usage,
                        )
                    elif se.type == "error":
                        response = LLMResponse(
                            content=f"[Error] {se.error_message}",
                            finish_reason="error",
                        )
                        yield AgentEvent(type="skill_end", skill_id=skill_id,
                                         error=se.error_message)

            # ── 4. Observe ──
            observation = self.observe(skill_id, response)
            yield AgentEvent(
                type="observation",
                skill_id=skill_id,
                observation=observation,
                status=observation.status,
                summary=observation.summary,
            )

            if observation.quality_issues:
                for issue in observation.quality_issues[:5]:
                    yield AgentEvent(type="observation_issue", skill_id=skill_id,
                                     content=issue)

            # ── 交互式暂停：有质量问题时让用户决定 ──
            if observation.suggestion in ("retry", "abort") and observation.status != "pass":
                import uuid as _uuid
                iid = f"int-{_uuid.uuid4().hex[:8]}"
                retries = self.state.retry_counts.get(skill_id, 0)
                options = ["retry", "skip", "abort"]
                yield AgentEvent(
                    type="interaction_required",
                    interaction_id=iid,
                    interaction_type="approve_retry",
                    interaction_prompt=(
                        f"Skill `{skill_id}` 状态: {observation.status}\n"
                        f"摘要: {observation.summary[:200]}\n"
                        f"重试次数: {retries}/{self.MAX_RETRIES}\n"
                        f"质量问题: {len(observation.quality_issues)} 个\n\n"
                        f"选择下一步操作:"
                    ),
                    interaction_options=options,
                    skill_id=skill_id,
                    observation=observation,
                    status=observation.status,
                    summary=observation.summary,
                )

                # 阻塞等待用户输入
                try:
                    user_cmd = self._interaction_queue.get(timeout=300)  # 5 分钟超时
                    user_cmd = user_cmd.strip().lower()
                except queue.Empty:
                    user_cmd = "skip"  # 超时默认跳过

                if user_cmd in ("abort", "a", "quit", "q"):
                    observation.suggestion = "abort"
                    self.state.termination_reason = "user_aborted"
                elif user_cmd in ("skip", "s"):
                    observation.suggestion = "skip"
                elif user_cmd in ("retry", "r"):
                    observation.suggestion = "retry"
                # else "continue" / 回车 → 保持原 suggestion

            # ── 5. Update ──
            self.update(skill_id, observation)

            # 根据观察推进
            if observation.suggestion == "retry":
                pass  # 不推进 skill_index
            else:
                skill_index += 1

            if skill_index >= len(self.skills):
                all_pass = all(s in self.state.completed_skills for s in self.skills)
                self.state.done = True
                self.state.success = all_pass
                self.state.termination_reason = (
                    "all_skills_completed" if all_pass else "some_skills_failed"
                )

        # ── 循环结束 ──
        if self.state.step >= self.state.max_steps and not self.state.done:
            self.state.done = True
            self.state.success = False
            self.state.termination_reason = "max_steps_reached"

        completed = len(self.state.completed_skills)
        failed = len(self.state.failed_skills)
        yield AgentEvent(
            type="agent_end",
            status="pass" if self.state.success else "fail",
            summary=f"{completed} 完成 / {failed} 失败 / {self.state.step} 步",
            progress={"step": total_skills, "total": total_skills},
            content=f"Agent 结束: {self.state.termination_reason}",
        )

        self._emit_cache_summary()
        return self.state

    def _act_stream(self, skill_id: str) -> Optional[Generator[StreamEvent, None, LLMResponse]]:
        """
        流式执行一个 Skill。

        机械化 Skill（code-consistency-checker）返回 None（调用方回退到 act()）。
        其他 Skill 返回 stream_complete() 生成器。
        """
        if skill_id in ("automation/code-consistency-checker", "automation/code-consistency-checker:review"):
            return None  # 机械化 / LLM review，走 act() → complete()

        context_vars = self._build_context_vars()
        user_input = self._build_user_input(skill_id)

        # P0-1 (2026-06-15): 设置 skill_version 到 TraceContext
        # _act_stream 绕过 run_skill()，需独立设置版本上下文
        try:
            from aitest.llm.skill_loader import resolve_skill_version
            from aitest.trace import TraceContext
            ver_info = resolve_skill_version(skill_id)
            TraceContext.set(
                run_id=TraceContext.get_run_id(),
                agent_name=self.agent_name,
                skill_version=ver_info.resolved_version,
            )
        except Exception:
            pass

        # 加载 Skill prompt
        try:
            system_prompt = load_skill(skill_id)
        except FileNotFoundError:
            return None

        system_prompt = _shared_injector.inject(skill_id, system_prompt, context_vars)
        system_prompt = _shared_adapter.adapt(system_prompt, self.provider)

        compat = check_provider_compatibility(skill_id, self.provider)
        if not compat["compatible"]:
            return None

        try:
            llm = get_provider(self.provider)
            return llm.stream_complete(
                system_prompt=system_prompt,
                user_prompt=user_input,
                max_tokens=8192,
            )
        except Exception:
            return None


# ══════════════════════════════════════════════════════════════════════════
#  run_agent() — 兼容旧接口，内部委托给 AgentLoop
# ══════════════════════════════════════════════════════════════════════════

def run_agent(
    agent_name: str,
    provider: str = "claude",
    verbose: bool = True,
    **kwargs,
) -> dict:
    """
    执行一个 Agent（多个 Skill 串行编排）——兼容旧接口。

    内部委托给 AgentLoop.run()。
    """
    agent = AgentLoop(agent_name, provider=provider, verbose=verbose, **kwargs)
    state = agent.run()
    return state.to_dict()


def list_agents() -> list[str]:
    """列出所有可用的 Agent 名称（含测试 + 开发）。"""
    return sorted(set(list(AGENT_SKILL_MAP.keys()) + list(DEV_AGENT_SKILL_MAP.keys())))


def list_dev_agents() -> list[str]:
    """列出所有开发 Agent 名称。"""
    return sorted(DEV_AGENT_SKILL_MAP.keys())

"""
LangGraph State 定义 — 所有图的共享类型。

SOPState TypedDict 流经每个 LangGraph 节点。
使用 Annotated[list, operator.add] reducer 实现多节点累积。
"""

from typing import TypedDict, Optional, List, Dict, Any, Annotated, Literal
from dataclasses import dataclass, field
from enum import Enum
import operator


# ══════════════════════════════════════════════════════════════════════════
#  Enums
# ══════════════════════════════════════════════════════════════════════════

SOPMode = Literal[
    "full", "resume", "status",
    "from-requirement", "from-test-design", "from-automation"
]

PhaseName = Literal[
    "Preflight",
    "Project Init",
    "Requirement",
    "Test Design",
    "Automation",
    "Execute & Debug",
    "Bug Analysis",
    "Data Sanitization",
    "Report",
    "Knowledge",
]

AgentName = Literal[
    "project-agent",
    "requirement-agent",
    "test-design-agent",
    "automation-agent",
    "execution-agent",
    "bug-analysis-agent",
    "report-agent",
    "knowledge-agent",
]

class GateLevel(Enum):
    """SOP 三层门禁。"""
    L1_ORCHESTRATOR = 1   # Phase 级前后检查
    L2_AGENT = 2          # Agent 边界检查
    L3_VALIDATOR = 3      # Python validator 调用


# ── P1-6: Bounded list reducers — 防止 SOPState 字段无限累积 ──

_SKILL_OBS_MAX = 100
_GATE_RESULTS_MAX = 50


def _bounded_skill_obs(current: list, update: list) -> list:
    """保留最近 _SKILL_OBS_MAX 条 skill_observations。"""
    combined = current + update
    return combined[-_SKILL_OBS_MAX:] if len(combined) > _SKILL_OBS_MAX else combined


def _bounded_gate_results(current: list, update: list) -> list:
    """保留最近 _GATE_RESULTS_MAX 条 gate_results。"""
    combined = current + update
    return combined[-_GATE_RESULTS_MAX:] if len(combined) > _GATE_RESULTS_MAX else combined


# ══════════════════════════════════════════════════════════════════════════
#  Dataclasses
# ══════════════════════════════════════════════════════════════════════════

@dataclass
class GateResult:
    """单次门禁检查结果。"""
    level: GateLevel
    phase: str
    ok: bool
    message: str = ""
    details: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict:
        return {
            "level": self.level.name,
            "phase": self.phase,
            "ok": self.ok,
            "message": self.message,
            "details": self.details,
        }


@dataclass
class SkillObservation:
    """单个 Skill 执行后的观察结果。"""
    skill_id: str
    status: str = "pending"            # pass | fail | partial | skipped
    artifacts_found: List[str] = field(default_factory=list)
    artifacts_missing: List[str] = field(default_factory=list)
    quality_issues: List[str] = field(default_factory=list)
    summary: str = ""
    suggestion: str = "continue"       # continue | retry | skip | abort
    token_usage: Dict[str, Any] = field(default_factory=dict)
    raw_output_preview: str = ""

    def to_dict(self) -> dict:
        return {
            "skill_id": self.skill_id,
            "status": self.status,
            "artifacts_found": self.artifacts_found,
            "artifacts_missing": self.artifacts_missing,
            "quality_issues": self.quality_issues,
            "summary": self.summary,
            "suggestion": self.suggestion,
            "token_usage": self.token_usage,
        }


@dataclass
class PageResult:
    """单个页面的处理结果。"""
    page_slug: str
    status: str = "pending"            # pending | running | completed | failed
    phases_completed: List[PhaseName] = field(default_factory=list)
    artifacts: Dict[str, str] = field(default_factory=dict)  # phase → path
    errors: List[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "page_slug": self.page_slug,
            "status": self.status,
            "phases_completed": list(self.phases_completed),
            "artifacts": self.artifacts,
            "errors": self.errors,
        }


# ══════════════════════════════════════════════════════════════════════════
#  Main SOPState TypedDict
# ══════════════════════════════════════════════════════════════════════════

# 规范 Phase 顺序（用于 route_next_phase 决策）
CANONICAL_PHASES: list[PhaseName] = [
    "Project Init",
    "Requirement",
    "Test Design",
    "Automation",
    "Execute & Debug",
    "Bug Analysis",
    "Data Sanitization",
    "Report",
    "Knowledge",
]

# Mode → skip_phases 映射
MODE_SKIP_MAP: dict[SOPMode, list[PhaseName]] = {
    "full": [],
    "resume": [],
    "status": [],
    "from-requirement": ["Project Init"],
    "from-test-design": ["Project Init", "Requirement"],
    "from-automation": ["Project Init", "Requirement", "Test Design"],
}

# Agent → Phase 映射
AGENT_PHASE_MAP: dict[AgentName, PhaseName] = {
    "project-agent": "Project Init",
    "requirement-agent": "Requirement",
    "test-design-agent": "Test Design",
    "automation-agent": "Automation",
    "execution-agent": "Execute & Debug",
    "bug-analysis-agent": "Bug Analysis",
    "report-agent": "Report",
    "knowledge-agent": "Knowledge",
}


# P2-4: AgentResult — 封装 Agent 执行结果，避免污染顶层状态
@dataclass
class AgentResult:
    """单个 Agent 的执行结果，存储在 agent_outputs[agent_name] 中。"""
    agent_name: str
    success: bool = False
    goal: str = ""
    module: str = ""
    page: str = ""
    step: int = 0
    completed_skills: List[str] = field(default_factory=list)
    failed_skills: Dict[str, str] = field(default_factory=dict)
    retry_counts: Dict[str, int] = field(default_factory=dict)
    observations: List[Dict[str, Any]] = field(default_factory=list)
    termination_reason: str = ""
    execution_failed: bool = False        # P2-4: execution-agent 特有标志

    def to_dict(self) -> dict:
        return {
            "agent_name": self.agent_name,
            "success": self.success,
            "goal": self.goal,
            "module": self.module,
            "page": self.page,
            "step": self.step,
            "completed_skills": self.completed_skills,
            "failed_skills": self.failed_skills,
            "retry_counts": self.retry_counts,
            "observations": self.observations,
            "termination_reason": self.termination_reason,
            "execution_failed": self.execution_failed,
        }


class SOPState(TypedDict):
    """
    SOP 编排的完整状态，流经所有 LangGraph 节点。

    P2-4 分层: 顶层仅含编排级状态(Phase/Page)。
    Agent 内部状态 (skills/retries/observations) 封装在 agent_outputs[agent_name] 中。

    使用 Annotated[list, operator.add] 的字段会自动跨节点累积。
    """

    # ── 运行时标识 ──
    module: str
    pages: List[str]                      # 待处理的 page slug 列表
    mode: SOPMode
    provider: str                         # claude | openai | ollama
    run_id: str

    # ── Phase 状态机 (编排层) ──
    current_phase: PhaseName
    completed_phases: Annotated[List[PhaseName], operator.add]
    failed_phases: Annotated[List[PhaseName], operator.add]
    skip_phases: List[PhaseName]          # mode 决定的跳过列表

    # ── Per-page 迭代 (编排层) ──
    current_page_index: int               # 0-based，驱动 test-design/automation 的页面循环
    per_page_results: Annotated[List[Dict[str, Any]], operator.add]

    # ── Agent 输出 (编排 → Agent 接口) ──
    # agent_outputs[agent_name] = AgentResult.to_dict()
    # Agent 内部状态 (skills/retries/observations) 封装在此，不污染顶层
    agent_outputs: Dict[str, Any]         # agent_name → AgentResult (dict)
    artifact_map: Dict[str, List[str]]    # phase → 产物文件路径列表
    skill_observations: Annotated[List[Dict[str, Any]], _bounded_skill_obs]

    # ── Bug-analysis 自动循环 ──
    bug_cycle_count: int
    bug_cycle_max: int
    fix_approved: Optional[bool]          # None=等待中, True=已批准, False=已拒绝

    # ── Human-in-the-loop ──
    interrupt_requested: bool
    human_input: Optional[str]

    # ── HITL 扩展 (P1-3): 自动化策略 + 测试用例审批 ──
    auto_strategy_approved: Optional[bool]   # None=等待中/未检查, True=已批准, False=已拒绝
    test_cases_approved: Optional[bool]      # None=未检查/等待中, True=已批准, False=已拒绝

    # ── 门禁检查 ──
    gate_results: Annotated[List[Dict[str, Any]], _bounded_gate_results]

    # ── 错误状态 ──
    fatal_error: Optional[str]
    status: str                           # running | completed | failed | paused


# ══════════════════════════════════════════════════════════════════════════
#  Helper: create initial state
# ══════════════════════════════════════════════════════════════════════════

def create_initial_state(
    module: str,
    pages: List[str],
    mode: SOPMode = "full",
    provider: str = "claude",
    run_id: str = "",
    bug_cycle_max: int = 3,
) -> dict:
    """
    创建 SOPGraph.invoke() 的初始状态字典。

    参数:
        module:  模块名 (e.g. "equipment")
        pages:   页面 slug 列表 (e.g. ["alarm-config"])
        mode:    运行模式
        provider: LLM provider
        run_id:  可选运行 ID（不提供时自动生成）
        bug_cycle_max: Bug 分析最大循环次数

    返回:
        完整的初始状态字典
    """
    import time

    if not run_id:
        run_id = f"sop-{module}-{int(time.time())}"

    return {
        "module": module,
        "pages": pages,
        "mode": mode,
        "provider": provider,
        "run_id": run_id,

        "current_phase": "Preflight",
        "completed_phases": [],
        "failed_phases": [],
        "skip_phases": MODE_SKIP_MAP.get(mode, []),

        "current_page_index": 0,
        "per_page_results": [],

        "agent_outputs": {},
        "artifact_map": {},
        "skill_observations": [],

        "bug_cycle_count": 0,
        "bug_cycle_max": bug_cycle_max,
        "fix_approved": None,

        "interrupt_requested": False,
        "human_input": None,

        "auto_strategy_approved": None,      # P1-3 HITL: None=等待审批
        "test_cases_approved": None,         # P1-3 HITL: None=未检查

        "gate_results": [],

        "fatal_error": None,
        "status": "running",
    }

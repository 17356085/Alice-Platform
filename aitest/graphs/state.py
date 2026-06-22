"""
LangGraph State 定义 — 所有图的共享类型。

SOPState TypedDict 流经每个 LangGraph 节点。
使用 Annotated[list, operator.add] reducer 实现多节点累积。
"""

from typing import TypedDict, Optional, List, Dict, Any, Annotated, Literal
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
import operator


# ══════════════════════════════════════════════════════════════════════════
#  路径工具 — 消除 state_auditor._module_dir() / sop_graph 的重复路径构造
# ══════════════════════════════════════════════════════════════════════════

_PATH_BASE = Path(__file__).resolve().parent.parent.parent
_CONTEXT_MODULES = _PATH_BASE / "governance" / "context" / "projects" / "web-automation" / "modules"


def get_module_dir(module: str) -> Path:
    """模块治理文档目录 (governance/context/.../modules/<module>)。"""
    return _CONTEXT_MODULES / module


def get_page_dir(module: str, page: str) -> Path:
    """页面治理文档目录 (governance/context/.../modules/<module>/pages/<page>)。"""
    return _CONTEXT_MODULES / module / "pages" / page


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


class CommonSOPStage(Enum):
    """
    P1 Architecture Review (C02): 共通 SOP 阶段抽象。

    将 Test SOP (9 phase) 和 Dev SOP (10 phase) 映射到 4 个共通阶段，
    解决架构评审发现的 SOP 模式不对称问题。

    用途:
      - 跨 SOP 治理检查（统一门禁规则）
      - Architecture Review Agent 评审基线
      - Knowledge Agent 跨 SOP 知识归类
    """
    PLAN = "planning"        # 规划: 项目/需求分析
    EXECUTE = "executing"    # 执行: 设计/编码/测试生成
    VERIFY = "verifying"     # 验证: 审查/测试/调试
    CLOSE = "closing"        # 收尾: 报告/构建/知识沉淀


# Test SOP phase → CommonSOPStage
TEST_PHASE_STAGE_MAP: dict[str, CommonSOPStage] = {
    "Preflight":        CommonSOPStage.PLAN,
    "Project Init":     CommonSOPStage.PLAN,
    "Requirement":      CommonSOPStage.PLAN,
    "Test Design":      CommonSOPStage.EXECUTE,
    "Automation":       CommonSOPStage.EXECUTE,
    "Execute & Debug":  CommonSOPStage.VERIFY,
    "Bug Analysis":     CommonSOPStage.VERIFY,
    "Data Sanitization": CommonSOPStage.CLOSE,
    "Report":           CommonSOPStage.CLOSE,
    "Knowledge":        CommonSOPStage.CLOSE,
}

# Dev SOP phase → CommonSOPStage
DEV_PHASE_STAGE_MAP: dict[str, CommonSOPStage] = {
    "Plan":             CommonSOPStage.PLAN,
    "Requirements":     CommonSOPStage.PLAN,
    "Architecture":     CommonSOPStage.EXECUTE,
    "Component Design": CommonSOPStage.EXECUTE,
    "Frontend Impl":    CommonSOPStage.EXECUTE,
    "Backend Impl":     CommonSOPStage.EXECUTE,
    "Code Review":      CommonSOPStage.VERIFY,
    "Dev Test":         CommonSOPStage.VERIFY,
    "Debug & Fix":      CommonSOPStage.VERIFY,
    "Build":            CommonSOPStage.CLOSE,
}


def get_common_stage(phase: str, sop_type: str = "test") -> CommonSOPStage:
    """返回任意 SOP phase 对应的共通阶段。sop_type: 'test' | 'dev'."""
    if sop_type == "dev":
        return DEV_PHASE_STAGE_MAP.get(phase, CommonSOPStage.EXECUTE)
    return TEST_PHASE_STAGE_MAP.get(phase, CommonSOPStage.EXECUTE)


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


def _unique_list(current: list, update: list) -> list:
    """去重追加：update 中已存在于 current 或 update 前部的元素被跳过。"""
    seen = set(current)
    new_items = []
    for x in update:
        if x not in seen:
            new_items.append(x)
            seen.add(x)
    return current + new_items


def _merge_agent_outputs(current: dict, update: dict) -> dict:
    """深度合并 agent_outputs，update 的键覆盖 current 的同名键。"""
    merged = dict(current)
    merged.update(update)
    return merged


def _merge_dict(current: dict, update: dict) -> dict:
    """深度合并字典（用于 artifact_map 等）。"""
    merged = dict(current)
    merged.update(update)
    return merged


def _pick_last(current, update):
    """选取最后一次写入的值（通用 last-write-wins reducer）。"""
    return update


# 向后兼容别名
_pick_last_bool = _pick_last
_pick_last_str = _pick_last


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

# ── 产物硬门禁 ──
MAX_PHASE_RETRY_ROUNDS: int = 2

# 产物路径（与 _PATH_BASE / _CONTEXT_MODULES 对齐）
_ZJSN_TEST = _PATH_BASE / "ZJSN_Test-master526"
_KPI_REPORTS = _PATH_BASE / "governance" / "kpi" / "reports"
_KPI_TESTCASES = _PATH_BASE / "governance" / "kpi" / "testcases"
_EXECUTION_REPORTS = _PATH_BASE / "governance" / "artifacts" / "execution-reports"


def _check_test_design_artifacts(module: str, pages: list[str]) -> list[tuple[bool, str, str]]:
    """Check per-page Test Design artifacts: TEST_CASES.md, TEST_DESIGN.md, PAGE_CONTEXT.md."""
    results = []
    for page in pages:
        page_dir = get_page_dir(module, page)
        for fname in ["TEST_CASES.md", "TEST_DESIGN.md", "PAGE_CONTEXT.md"]:
            fpath = page_dir / fname
            ok = fpath.exists() and fpath.stat().st_size > 0
            results.append((ok, str(fpath), f"{page}/{fname}"))
    return results


def _check_automation_artifacts(module: str, pages: list[str]) -> list[tuple[bool, str, str]]:
    """Check per-module Automation artifacts: *Page.py + test_*.py exist."""
    results = []
    po_dir = _ZJSN_TEST / "page" / f"{module}_page"
    test_dir = _ZJSN_TEST / "script" / module
    has_po = po_dir.exists() and any(po_dir.glob("*Page.py"))
    has_test = test_dir.exists() and any(test_dir.glob("test_*.py"))
    results.append((has_po, str(po_dir), f"PageObject (*Page.py) in page/{module}_page"))
    results.append((has_test, str(test_dir), f"Test scripts (test_*.py) in script/{module}"))
    return results


def _check_report_artifacts(module: str, pages: list[str]) -> list[tuple[bool, str, str]]:
    """Check execution report .md exists."""
    pattern = f"TEST_EXECUTION_{module.upper()}_*.md"
    found = list(_EXECUTION_REPORTS.glob(pattern)) if _EXECUTION_REPORTS.exists() else []
    ok = len(found) > 0
    results = [(ok, str(_EXECUTION_REPORTS / pattern), f"执行报告 ({pattern})")]
    return results


def _check_knowledge_artifacts(module: str, pages: list[str]) -> list[tuple[bool, str, str]]:
    """Check per-page Excel + .md test case files exist."""
    results = []
    for page in pages:
        xlsx_path = _KPI_REPORTS / module / f"测试报告-{module}-{page}.xlsx"
        md_path = _KPI_TESTCASES / module / f"testcases-{module}-{page}.md"
        results.append((xlsx_path.exists(), str(xlsx_path), f"{page}/测试报告.xlsx"))
        results.append((md_path.exists(), str(md_path), f"{page}/testcases.md"))
    return results


# Phase → 强制产物检查器列表
# 仅包含硬要求产物。软要求（BUSINESS_SCENARIOS.md, RISK_MODEL.md）不在此列。
MANDATORY_ARTIFACTS: dict[PhaseName, list] = {
    "Test Design": [_check_test_design_artifacts],
    "Automation": [_check_automation_artifacts],
    "Report": [_check_report_artifacts],
    "Knowledge": [_check_knowledge_artifacts],
}


def validate_phase_artifacts(phase: str, module: str, pages: list[str]) -> tuple[bool, list[tuple[str, str]]]:
    """Check mandatory artifacts for a phase exist on disk.

    Returns (all_ok, [(label, path), ...]) for missing artifacts.
    Returns (True, []) if phase has no mandatory artifacts.
    """
    checkers = MANDATORY_ARTIFACTS.get(phase, [])
    if not checkers:
        return True, []
    missing: list[tuple[str, str]] = []
    for checker in checkers:
        results = checker(module, pages)
        for ok, path, label in results:
            if not ok:
                missing.append((label, path))
    return len(missing) == 0, missing


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
    completed_phases: Annotated[List[PhaseName], _unique_list]
    failed_phases: Annotated[List[PhaseName], _unique_list]
    skip_phases: List[PhaseName]          # mode 决定的跳过列表

    # ── Per-page 迭代 (编排层) ──
    current_page_index: int               # 0-based，驱动 test-design/automation 的页面循环
    bsc_retry_count: int                  # 质量门禁 BSC 打回重试计数（独立字段，不被 agent loop 覆盖）
    per_page_results: Annotated[List[Dict[str, Any]], operator.add]

    # ── Agent 输出 (编排 → Agent 接口) ──
    # agent_outputs[agent_name] = AgentResult.to_dict()
    # Agent 内部状态 (skills/retries/observations) 封装在此，不污染顶层
    agent_outputs: Annotated[Dict[str, Any], _merge_agent_outputs]  # agent_name → AgentResult (dict)
    artifact_map: Annotated[Dict[str, List[str]], _merge_dict]  # phase → 产物文件路径列表
    skill_observations: Annotated[List[Dict[str, Any]], _bounded_skill_obs]

    # ── Bug-analysis 自动循环 ──
    bug_cycle_count: int
    bug_cycle_max: int
    fix_approved: Annotated[Optional[bool], _pick_last_bool]  # None=等待中, True=已批准, False=已拒绝

    # ── Human-in-the-loop ──
    interrupt_requested: bool
    human_input: Annotated[Optional[str], _pick_last]

    # ── HITL 扩展 (P1-3): 自动化策略 + 测试用例审批 ──
    auto_strategy_approved: Annotated[Optional[bool], _pick_last_bool]  # None=等待中/未检查, True=已批准, False=已拒绝
    test_cases_approved: Annotated[Optional[bool], _pick_last_bool]  # None=未检查/等待中, True=已批准, False=已拒绝

    # ── 质量门禁重试 ──
    force_retry_phase: Optional[str]          # 非 None 时强制路由到指定 phase（绕过 operator.add 只增不减限制）
    phase_retry_count: int                    # 当前 phase 的重试计数（产物硬门禁用，独立于 bsc_retry_count）

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
        "bsc_retry_count": 0,
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

        "force_retry_phase": None,           # 质量门禁重试: None=无重试, str=目标 phase
        "phase_retry_count": 0,               # 产物硬门禁重试计数

        "gate_results": [],

        "fatal_error": None,
        "status": "running",
    }

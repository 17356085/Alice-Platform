"""
TLO Lifecycle State — 测试生命周期状态机 (LangGraph 子图)。

8 阶段生命周期:
    Stage 1: 需求分析 (Requirement Analyst)
    Stage 2: 策略制定 (Test Strategy Agent)
    Stage 3: 用例设计 (Test Designer — Spec Pipeline 4-stage)
    Stage 4: 自动化开发 (Automation Developer)
    Stage 5: 环境准备 (Environment Preparer)
    Stage 6: 测试执行 (Execution Agent)
    Stage 7: 失败分析 (Failure Analyst → QA Loop)
    Stage 8: 报告生成 (Report Agent)
    Stage 9: 回归推荐 (Regression Advisor)

质量门禁:
    Gate 3→4: Spec Critic score ≥ 60
    Gate 6→7: Execution failed → trigger QA Loop (max 3 rounds)
    Gate 7→8: All failures resolved or escalated

复用现有 LangGraph checkpoint (SQLite) + HITL interrupt 机制。
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import TypedDict, Optional, List, Dict, Any, Annotated, Literal
import operator
from pathlib import Path


# ═══════════════════════════════════════════════════════════════
#  TLO Lifecycle Stage Enum
# ═══════════════════════════════════════════════════════════════

class LifecycleStage(Enum):
    """TLO 测试生命周期 9 阶段 (含回归推荐)。"""
    REQUIREMENT = ("1", "需求分析", "requirement-agent")
    STRATEGY = ("2", "策略制定", "test-design-agent")
    DESIGN = ("3", "用例设计", "test-designer")
    DESIGN_GATE = ("3-gate", "用例质量门禁", None)
    AUTOMATION = ("4", "自动化开发", "automation-agent")
    ENV_PREP = ("5", "环境准备", "environment-preparer")
    EXECUTION = ("6", "测试执行", "execution-agent")
    FAILURE_ANALYSIS = ("7", "失败分析", "bug-analysis-agent")
    QA_LOOP = ("7-loop", "QA Loop", None)
    REPORT = ("8", "报告生成", "report-agent")
    REGRESSION = ("9", "回归推荐", "regression-advisor")

    def __init__(self, num: str, label: str, agent_id: Optional[str]):
        self.num = num
        self.label = label
        self.agent_id = agent_id

    @property
    def is_gate(self) -> bool:
        return self.agent_id is None

    @property
    def next_stage(self) -> Optional["LifecycleStage"]:
        """Return next stage in lifecycle."""
        stages = list(LifecycleStage)
        idx = stages.index(self)
        return stages[idx + 1] if idx + 1 < len(stages) else None

    @classmethod
    def from_label(cls, label: str) -> Optional["LifecycleStage"]:
        for s in cls:
            if s.label == label:
                return s
        return None


# ═══════════════════════════════════════════════════════════════
#  TLO State (LangGraph compatible)
# ═══════════════════════════════════════════════════════════════

TLOPhaseLiteral = Literal[
    "requirement", "strategy", "design", "design_gate",
    "automation", "env_prep", "execution",
    "failure_analysis", "qa_loop", "report", "regression"
]


class LifecycleState(TypedDict, total=False):
    """
    TLO 生命周期状态 — 流经 LangGraph 节点。

    与现有 SOPState 兼容，可复用 checkpoint + HITL 基础设施。
    """
    # ── 生命周期基础 ──
    module: str
    current_stage: str                     # LifecycleStage.label
    current_stage_idx: int                 # 0-10
    stage_history: Annotated[list[str], operator.add]

    # ── 模块上下文 ──
    pages: list[str]
    target_url: str
    provider: str                          # claude | deepseek | google

    # ── 各阶段产出 ──
    requirement_summary: str               # Stage 1: Requirement Analyst 产出
    test_strategy: str                     # Stage 2: Test Strategy Agent 产出 (Smoke/Regression/...)
    test_spec: str                         # Stage 3: Test Designer → TEST_SPEC.md
    critic_score: int                      # Stage 3-gate: Critic score (0-100)
    automation_artifacts: list[str]        # Stage 4: PageObject + test files
    env_ready: bool                        # Stage 5: Environment check result
    execution_results: dict                # Stage 6: pytest results

    # ── QA Loop (Stage 7) ──
    failures: list[str]                    # Failed test IDs
    qa_loop_rounds: int                    # Current QA Loop round
    qa_loop_max_rounds: int                # Max QA Loop rounds (default 3)
    qa_loop_findings: list[dict]           # QAFinding.to_dict()
    qa_loop_status: str                    # passed | failed | escalated

    # ── 输出 ──
    report_path: str                       # Stage 8: Report file path
    regression_recommendations: list[str]  # Stage 9: Regression scope
    completed: bool

    # ── 治理追踪 ──
    run_id: str
    started_at: str
    errors: Annotated[list[str], operator.add]
    warnings: Annotated[list[str], operator.add]


# ═══════════════════════════════════════════════════════════════
#  State Factory
# ═══════════════════════════════════════════════════════════════

def create_initial_lifecycle_state(
    module: str,
    pages: list[str] = None,
    provider: str = "claude",
    max_qa_rounds: int = 3,
) -> LifecycleState:
    """
    创建 TLO 生命周期初始状态。

    Args:
        module: 模块名称 (equipment, personnel, ...)
        pages: 页面列表 (如未指定，从 SOP_STATUS 自动发现)
        provider: LLM Provider
        max_qa_rounds: QA Loop 最大重试轮数
    """
    from datetime import datetime
    import uuid

    if pages is None:
        pages = _discover_pages(module)

    return LifecycleState(
        module=module,
        current_stage=LifecycleStage.REQUIREMENT.label,
        current_stage_idx=0,
        stage_history=[],
        pages=pages,
        target_url="https://aiwechatminidemo.cimc-digital.com/",
        provider=provider,
        requirement_summary="",
        test_strategy="",
        test_spec="",
        critic_score=0,
        automation_artifacts=[],
        env_ready=False,
        execution_results={},
        failures=[],
        qa_loop_rounds=0,
        qa_loop_max_rounds=max_qa_rounds,
        qa_loop_findings=[],
        qa_loop_status="pending",
        report_path="",
        regression_recommendations=[],
        completed=False,
        run_id=f"tlo-{module}-{datetime.now().strftime('%y%m%d-%H%M%S')}-{uuid.uuid4().hex[:6]}",
        started_at=datetime.now().isoformat(),
        errors=[],
        warnings=[],
    )


def _discover_pages(module: str) -> list[str]:
    """从 SOP_STATUS 自动发现模块页面列表。"""
    import json
    sop_dir = Path(__file__).resolve().parent.parent.parent / "governance" / "artifacts" / "sop-status"
    status_file = sop_dir / f"SOP_STATUS_{module}.json"
    if status_file.exists():
        data = json.loads(status_file.read_text(encoding="utf-8"))
        return data.get("pages_processed", [])
    return []


# ═══════════════════════════════════════════════════════════════
#  Stage Router — 决定下一步
# ═══════════════════════════════════════════════════════════════

def tlo_route_next_stage(state: LifecycleState) -> str:
    """
    TLO 生命周期条件路由。

    决定当前阶段完成后进入哪个阶段。
    处理条件分支:
      - 无页面 → 跳至 report
      - Critic score < 60 → 打回 design
      - 无失败 → 跳过 failure_analysis → report
      - QA Loop 未完成 → 继续 loop
    """
    stage = LifecycleStage.from_label(state.get("current_stage", ""))

    if stage is None:
        return "requirement"

    # Quality gate: 3→4 requires critic_score ≥ 60
    if stage == LifecycleStage.DESIGN_GATE:
        score = state.get("critic_score", 0)
        if score < 60:
            return "design"  # back to Test Designer
        return "automation"

    # After execution: check for failures
    if stage == LifecycleStage.EXECUTION:
        failures = state.get("failures", [])
        if failures:
            return "failure_analysis"
        return "report"  # no failures, skip to report

    # After failure analysis: enter QA Loop
    if stage == LifecycleStage.FAILURE_ANALYSIS:
        return "qa_loop"

    # QA Loop routing
    if stage == LifecycleStage.QA_LOOP:
        status = state.get("qa_loop_status", "")
        if status == "passed":
            return "report"
        rounds = state.get("qa_loop_rounds", 0)
        max_rounds = state.get("qa_loop_max_rounds", 3)
        if rounds >= max_rounds:
            # Max rounds exhausted, escalate and proceed
            return "report"
        return "failure_analysis"  # continue loop: analyze → fix → re-run

    # Skip env_prep if no pages configured
    if stage == LifecycleStage.AUTOMATION:
        if not state.get("pages"):
            return "report"
        return "env_prep"

    # Normal sequential flow
    next_s = stage.next_stage
    if next_s:
        return next_s.label.lower().replace(" ", "_")

    # Terminal
    state["completed"] = True
    return "__end__"


# ═══════════════════════════════════════════════════════════════
#  Lifecycle Progress Calculator
# ═══════════════════════════════════════════════════════════════

@dataclass
class LifecycleProgress:
    """Kanban 可用的生命周期进度快照。"""
    module: str
    current_stage: str
    current_stage_num: int
    total_stages: int = 9
    completed_stages: list[str] = field(default_factory=list)
    percent: float = 0.0
    qa_loop_active: bool = False
    qa_loop_round: int = 0


def get_progress(state: LifecycleState) -> LifecycleProgress:
    """从 LifecycleState 计算进度快照 (用于 Kanban UI)。"""
    stage = LifecycleStage.from_label(state.get("current_stage", ""))
    history = state.get("stage_history", [])
    num = int(stage.num.split("-")[0]) if stage else 0

    return LifecycleProgress(
        module=state.get("module", "unknown"),
        current_stage=stage.label if stage else "unknown",
        current_stage_num=num,
        total_stages=9,
        completed_stages=history,
        percent=round(num / 9 * 100, 1),
        qa_loop_active=(stage == LifecycleStage.QA_LOOP if stage else False),
        qa_loop_round=state.get("qa_loop_rounds", 0),
    )


# ═══════════════════════════════════════════════════════════════
#  Skip Map (对标 state_dev.py DEV_MODE_SKIP_MAP)
# ═══════════════════════════════════════════════════════════════

TLO_MODE_SKIP_MAP: dict[str, set[str]] = {
    "from-requirement": {"requirement"},           # 从策略制定开始
    "from-strategy": {"requirement", "strategy"},  # 从用例设计开始
    "from-design": {"requirement", "strategy", "design"},  # 从自动化开始
    "from-automation": {"requirement", "strategy", "design", "automation"},
    "execution-only": {"requirement", "strategy", "design", "automation", "env_prep"},
    "analysis-only": {},  # 全阶段
}

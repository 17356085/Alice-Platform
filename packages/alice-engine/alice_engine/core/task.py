"""Agent 数据结构 — 状态、观察、事件、产物规则。

从 agent_runner.py 抽取，独立于 LLM 执行逻辑。
"""
from dataclasses import dataclass, field
from typing import Optional, Literal


# ═══════════════════════════════════════════════════════════
#  输出验证规则
# ═══════════════════════════════════════════════════════════

@dataclass
class ArtifactRule:
    """Skill 产出的验证规则。"""
    glob_pattern: str          # 文件 glob 模式
    check_type: str = "exists_non_empty"  # exists | exists_non_empty | grep_pass | import_ok | pytest_collect
    grep_pattern: str = ""    # grep 应匹配到的内容
    grep_should_find: bool = True
    required: bool = True
    label: str = ""


AUTOMATION_ARTIFACT_RULES: dict[str, list["ArtifactRule"]] = {
    "automation/page-object-generator": [
        ArtifactRule(glob_pattern="*Page.py", label="Page Object file"),
        ArtifactRule(
            glob_pattern="*Page.py",
            check_type="grep_pass",
            grep_pattern=r"class \w+\(BasePage\):",
            label="Inherit BasePage",
        ),
        ArtifactRule(
            glob_pattern="*Page.py",
            check_type="grep_pass",
            grep_pattern=r"//\*\[@id=",
            grep_should_find=False,
            label="No absolute XPath",
        ),
        ArtifactRule(
            glob_pattern="*Page.py",
            check_type="grep_pass",
            grep_pattern=r"time\.sleep\(",
            grep_should_find=False,
            label="No hard sleep",
        ),
    ],
    "automation/test-script-generator": [
        ArtifactRule(glob_pattern="test_*.py", label="Pytest script"),
        ArtifactRule(
            glob_pattern="test_*.py",
            check_type="grep_pass",
            grep_pattern=r"def test_",
            label="Has pytest test functions",
        ),
        ArtifactRule(
            glob_pattern="test_*.py",
            check_type="grep_pass",
            grep_pattern=r"time\.sleep\(",
            grep_should_find=False,
            label="No hard sleep",
        ),
    ],
    "automation/code-consistency-checker": [],
}
DEV_ARTIFACT_RULES: dict[str, list["ArtifactRule"]] = {}


# 默认产物规则 — 平台层可覆盖
# v3.1: 添加验证和 setter，防止未填充时静默跳过检查
_ALL_ARTIFACT_RULES: dict[str, list[ArtifactRule]] = {
    **AUTOMATION_ARTIFACT_RULES,
    **DEV_ARTIFACT_RULES,
}
_ARTIFACT_RULES_POPULATED = True

def set_artifact_rules(rules: dict[str, list[ArtifactRule]]) -> None:
    """设置产物规则。平台层调用此函数填充规则。"""
    global _ALL_ARTIFACT_RULES, _ARTIFACT_RULES_POPULATED
    _ALL_ARTIFACT_RULES = dict(rules)
    _ARTIFACT_RULES_POPULATED = True

def is_artifact_rules_populated() -> bool:
    """检查产物规则是否已填充。"""
    return _ARTIFACT_RULES_POPULATED

# 默认红线检查
CODE_REDLINE_CHECKS: list[tuple[str, str, bool]] = [
    ("继承 BasePage", r"class \w+\(BasePage\):", True),
    ("绝对 XPath", r"//\*\[@id=", False),
    ("time.sleep 硬等待", r"time\.sleep\(", False),
    ("print 调试", r"^[^#]*\bprint\(", False),
    ("手动 URL 硬编码", r'get\("https?://', False),
]


# ═══════════════════════════════════════════════════════════
#  数据结构
# ═══════════════════════════════════════════════════════════

@dataclass
class Observation:
    """Agent 执行一步 Skill 后的观察结果。"""
    skill_id: str
    status: str = "pending"        # pass | fail | partial | skipped | correct_failure | wrong_failure
    artifacts_found: list[str] = field(default_factory=list)
    artifacts_missing: list[str] = field(default_factory=list)
    quality_issues: list[str] = field(default_factory=list)
    safety_flags: list[dict] = field(default_factory=list)  # [{severity, rule, detail}]
    summary: str = ""
    suggestion: str = "continue"   # continue | retry | skip | abort
    raw_output_preview: str = ""
    raw_output_full: str = ""  # ★ Full LLM response for artifact persistence
    token_usage: dict = field(default_factory=dict)
    timestamp: str = ""
    latency_ms: int = 0
    model_name: str = ""
    run_id: str = ""
    failure_category: str = ""     # prompt | tool_desc | schema | context_pollution | retrieval | env_permission

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
    provider: str = None
    step: int = 0
    max_steps: int = 12
    current_skill: str = ""
    completed_skills: list[str] = field(default_factory=list)
    failed_skills: dict = field(default_factory=dict)
    retry_counts: dict = field(default_factory=dict)
    observations: list[Observation] = field(default_factory=list)
    artifacts: dict = field(default_factory=dict)
    memory: dict = field(default_factory=dict)
    done: bool = False
    success: bool = False
    termination_reason: str = ""
    # ── Task FSM state ──
    task_state: str = "backlog"  # Matches TaskState enum values

    def to_dict(self) -> dict:
        return {
            "agent_name": self.agent_name, "goal": self.goal,
            "module": self.module, "page": self.page, "provider": self.provider,
            "step": self.step, "max_steps": self.max_steps,
            "current_skill": self.current_skill,
            "completed_skills": self.completed_skills,
            "failed_skills": self.failed_skills, "retry_counts": self.retry_counts,
            "observations": [
                {"skill_id": o.skill_id, "status": o.status,
                 "artifacts_found": o.artifacts_found, "artifacts_missing": o.artifacts_missing,
                 "quality_issues": o.quality_issues, "safety_flags": o.safety_flags,
                 "summary": o.summary, "suggestion": o.suggestion,
                 "token_usage": o.token_usage, "timestamp": o.timestamp,
                 "latency_ms": o.latency_ms, "model_name": o.model_name, "run_id": o.run_id,
                 "failure_category": o.failure_category}
                for o in self.observations
            ],
            "memory": self.memory, "artifacts": self.artifacts,
            "done": self.done, "success": self.success,
            "termination_reason": self.termination_reason,
            "task_state": self.task_state,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "AgentState":
        """Restore a JSON checkpoint produced by :meth:`to_dict`.

        The restored state is intentionally data-only. Runtime handles such as
        providers, MCP clients, and abort events are recreated by AgentLoop.
        Unknown/missing fields are tolerated so checkpoints written by older
        workers remain recoverable.
        """
        if not isinstance(data, dict):
            raise TypeError("AgentState checkpoint must be a mapping")

        state = cls(
            agent_name=str(data.get("agent_name", "")),
            goal=str(data.get("goal", "")),
            module=str(data.get("module", "")),
            page=str(data.get("page", "")),
            provider=data.get("provider"),
            max_steps=int(data.get("max_steps", 12) or 12),
        )
        state.step = int(data.get("step", 0) or 0)
        state.current_skill = str(data.get("current_skill", "") or "")
        state.completed_skills = list(data.get("completed_skills", []) or [])
        state.failed_skills = dict(data.get("failed_skills", {}) or {})
        state.retry_counts = dict(data.get("retry_counts", {}) or {})
        state.memory = dict(data.get("memory", {}) or {})
        state.artifacts = dict(data.get("artifacts", {}) or {})
        state.done = bool(data.get("done", False))
        state.success = bool(data.get("success", False))
        state.termination_reason = str(data.get("termination_reason", "") or "")
        state.task_state = str(data.get("task_state", "backlog") or "backlog")

        observations = []
        for raw in data.get("observations", []) or []:
            if not isinstance(raw, dict):
                continue
            observations.append(
                Observation(
                    skill_id=str(raw.get("skill_id", "")),
                    status=str(raw.get("status", "pending")),
                    artifacts_found=list(raw.get("artifacts_found", []) or []),
                    artifacts_missing=list(raw.get("artifacts_missing", []) or []),
                    quality_issues=list(raw.get("quality_issues", []) or []),
                    safety_flags=list(raw.get("safety_flags", []) or []),
                    summary=str(raw.get("summary", "") or ""),
                    suggestion=str(raw.get("suggestion", "continue") or "continue"),
                    raw_output_preview=str(raw.get("raw_output_preview", "") or ""),
                    raw_output_full=str(raw.get("raw_output_full", "") or ""),
                    token_usage=dict(raw.get("token_usage", {}) or {}),
                    timestamp=str(raw.get("timestamp", "") or ""),
                    latency_ms=int(raw.get("latency_ms", 0) or 0),
                    model_name=str(raw.get("model_name", "") or ""),
                    run_id=str(raw.get("run_id", "") or ""),
                    failure_category=str(raw.get("failure_category", "") or ""),
                )
            )
        state.observations = observations
        return state


AgentEventType = Literal[
    "agent_start", "agent_end",
    "perceive", "plan", "plan_result",
    "skill_start", "skill_chunk", "skill_end",
    "observation", "observation_issue",
    "interaction_required",
    "phase_complete", "agent_message",
    "sop_start", "sop_phase", "sop_complete",
]


@dataclass
class AgentEvent:
    """run_interactive() 产生的单个事件。interaction_required 事件暂停执行，等待外部输入。

    v3.1: 明确字段定义，ui_projection.py 通过这些字段访问事件数据。
    """
    type: AgentEventType
    skill_id: str = ""
    content: str = ""
    stream_event: Optional = None
    observation: Optional[Observation] = None
    interaction_id: str = ""
    interaction_type: str = ""
    interaction_prompt: str = ""
    interaction_options: list = field(default_factory=list)
    status: str = ""
    summary: str = ""
    progress: dict = field(default_factory=dict)
    token_usage: dict = field(default_factory=dict)
    error: str = ""


# v3.1: AgentEvent Protocol — 定义 ui_projection.py 等消费者期望的字段
# 这是 AgentEvent 的"接口契约"，任何产生 AgentEvent 的代码必须满足
from typing import Protocol, runtime_checkable

@runtime_checkable
class AgentEventProtocol(Protocol):
    """AgentEvent 的 Protocol 定义。ui_projection.py 等消费者依赖这些字段。"""

    type: AgentEventType
    skill_id: str
    content: str
    status: str
    summary: str
    progress: dict
    token_usage: dict
    error: str
    interaction_id: str
    interaction_type: str
    interaction_prompt: str
    interaction_options: list

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


AUTOMATION_ARTIFACT_RULES = {
    "automation/tech-analysis": [
        ArtifactRule(glob_pattern="{module_dir}/pages/{page}/TECH_ANALYSIS.md", label="TECH_ANALYSIS.md"),
    ],
    "automation/auto-strategy": [
        ArtifactRule(glob_pattern="{module_dir}/pages/{page}/AUTO_STRATEGY.md", label="AUTO_STRATEGY.md"),
    ],
    "automation/page-object-generator": [
        ArtifactRule(glob_pattern="ZJSN_Test-master526/page/{module}_page/{PageName}Page.py", label="PageObject 文件"),
        ArtifactRule(glob_pattern="ZJSN_Test-master526/page/{module}_page/{PageName}Page.py",
                     check_type="grep_pass", grep_pattern=r"class \w+\(BasePage\):", label="继承 BasePage"),
        ArtifactRule(glob_pattern="ZJSN_Test-master526/page/{module}_page/{PageName}Page.py",
                     check_type="grep_pass", grep_pattern=r"//\*\[@id=", grep_should_find=False,
                     label="禁止绝对 XPath", required=False),
        ArtifactRule(glob_pattern="ZJSN_Test-master526/page/{module}_page/{PageName}Page.py",
                     check_type="grep_pass", grep_pattern=r"time\.sleep\(", grep_should_find=False,
                     label="禁止 time.sleep"),
        ArtifactRule(glob_pattern="ZJSN_Test-master526/page/{module}_page/{PageName}Page.py",
                     check_type="grep_pass", grep_pattern=r"^[^#]*\bprint\(", grep_should_find=False,
                     label="禁止 print 调试"),
    ],
    "automation/test-script-generator": [
        ArtifactRule(glob_pattern="ZJSN_Test-master526/script/{module}/test_{page_underscore}.py", label="测试脚本文件"),
        ArtifactRule(glob_pattern="ZJSN_Test-master526/script/{module}/test_{page_underscore}.py",
                     check_type="grep_pass", grep_pattern=r"def test_", label="包含 test_ 函数"),
        ArtifactRule(glob_pattern="ZJSN_Test-master526/script/{module}/test_{page_underscore}.py",
                     check_type="grep_pass", grep_pattern=r"time\.sleep\(", grep_should_find=False,
                     label="禁止 time.sleep"),
        ArtifactRule(glob_pattern="ZJSN_Test-master526/script/{module}/test_{page_underscore}.py",
                     check_type="grep_pass", grep_pattern=r"^[^#]*\bprint\(", grep_should_find=False,
                     label="禁止 print 调试", required=False),
        ArtifactRule(glob_pattern="ZJSN_Test-master526/script/{module}/conftest.py",
                     label="conftest.py", required=False),
    ],
    "automation/code-consistency-checker": [],
}

DEV_ARTIFACT_RULES = {
    "architecture/project-scanner": [
        ArtifactRule(glob_pattern="{module_dir}/PROJECT_STRUCTURE.md", label="PROJECT_STRUCTURE.md"),
    ],
    "architecture/tech-stack-decider": [
        ArtifactRule(glob_pattern="{module_dir}/TECH_STACK.md", label="TECH_STACK.md"),
    ],
    "architecture/component-tree-designer": [
        ArtifactRule(glob_pattern="{module_dir}/COMPONENT_TREE.md", label="COMPONENT_TREE.md"),
    ],
    "architecture/api-contract-designer": [
        ArtifactRule(glob_pattern="{module_dir}/API_CONTRACTS.md", label="API_CONTRACTS.md"),
    ],
    "frontend/vue-component-generator": [
        ArtifactRule(glob_pattern="{module_dir}/src/components/{PageName}.vue", label="Vue 组件文件"),
        ArtifactRule(glob_pattern="{module_dir}/src/components/{PageName}.vue",
                     check_type="grep_pass", grep_pattern=r"<script setup lang=\"ts\">",
                     label="Composition API"),
        ArtifactRule(glob_pattern="{module_dir}/src/components/{PageName}.vue",
                     check_type="grep_pass", grep_pattern=r": any", grep_should_find=False,
                     label="禁止 any 类型"),
    ],
    "backend/fastapi-router-generator": [
        ArtifactRule(glob_pattern="{module_dir}/routers/{page}.py", label="FastAPI Router 文件"),
        ArtifactRule(glob_pattern="{module_dir}/routers/{page}.py",
                     check_type="grep_pass", grep_pattern=r"async def", label="async def 端点"),
    ],
    "backend/pydantic-schema-generator": [
        ArtifactRule(glob_pattern="{module_dir}/schemas/{page}.py", label="Pydantic Schema 文件"),
        ArtifactRule(glob_pattern="{module_dir}/schemas/{page}.py",
                     check_type="grep_pass", grep_pattern=r"model_config\s*=", label="Pydantic v2 model_config"),
    ],
    "backend/sqlalchemy-model-generator": [
        ArtifactRule(glob_pattern="{module_dir}/models/{page}.py", label="SQLAlchemy Model 文件"),
        ArtifactRule(glob_pattern="{module_dir}/models/{page}.py",
                     check_type="grep_pass", grep_pattern=r"mapped_column", label="SQLAlchemy 2.0 mapped_column"),
    ],
    "backend/backend-consistency-checker": [],
    "frontend/frontend-lint-checker": [],
}

_ALL_ARTIFACT_RULES = {**AUTOMATION_ARTIFACT_RULES, **DEV_ARTIFACT_RULES}

CODE_REDLINE_CHECKS = [
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
    status: str = "pending"        # pass | fail | partial | skipped
    artifacts_found: list[str] = field(default_factory=list)
    artifacts_missing: list[str] = field(default_factory=list)
    quality_issues: list[str] = field(default_factory=list)
    summary: str = ""
    suggestion: str = "continue"   # continue | retry | skip | abort
    raw_output_preview: str = ""
    token_usage: dict = field(default_factory=dict)
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
    failed_skills: dict = field(default_factory=dict)
    retry_counts: dict = field(default_factory=dict)
    observations: list[Observation] = field(default_factory=list)
    artifacts: dict = field(default_factory=dict)
    memory: dict = field(default_factory=dict)
    done: bool = False
    success: bool = False
    termination_reason: str = ""

    def to_dict(self) -> dict:
        return {
            "agent_name": self.agent_name, "goal": self.goal,
            "module": self.module, "page": self.page, "provider": self.provider,
            "step": self.step, "completed_skills": self.completed_skills,
            "failed_skills": self.failed_skills, "retry_counts": self.retry_counts,
            "observations": [
                {"skill_id": o.skill_id, "status": o.status,
                 "artifacts_found": o.artifacts_found, "artifacts_missing": o.artifacts_missing,
                 "quality_issues": o.quality_issues, "summary": o.summary, "suggestion": o.suggestion,
                 "token_usage": o.token_usage, "timestamp": o.timestamp,
                 "latency_ms": o.latency_ms, "model_name": o.model_name, "run_id": o.run_id}
                for o in self.observations
            ],
            "memory": self.memory, "artifacts": self.artifacts,
            "done": self.done, "success": self.success,
            "termination_reason": self.termination_reason,
        }


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
    """run_interactive() 产生的单个事件。interaction_required 事件暂停执行，等待外部输入。"""
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

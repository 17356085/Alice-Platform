# [LAYER:Core/Executor] 从 aitest/agents/agent_runner.py 搬入
"""Agent Runner — Agent 执行循环核心。

P0 重构 (2026-06-12): 从顺序 for 循环升级为真正的 Agent 循环。
P1 重构 (2026-06-17): 拆分为 runner_state / skill_executor / agent_runner 三文件。
v1.0 (2026-06-23): 集成 ReliableProvider + ContextWindowMonitor + PromptInjectionGuard

用法:
    from alice_engine.core.executor import AgentLoop, run_agent, list_agents
    from alice_engine.core.task import Observation, AgentState, AgentEvent
    from alice_engine.core.agent_definitions import FALLBACK_AGENT_SKILL_MAP as AGENT_SKILL_MAP, run_skill

    agent = AgentLoop("automation-agent", module="equipment", page="alarm-config")
    state = agent.run()
"""
import os
import re
import sys
import time
import queue
from pathlib import Path
from collections.abc import Generator
from typing import Optional
import io
import threading

from alice_engine.providers.base import LLMResponse, LLMProvider; from alice_engine.providers import get_provider
from alice_engine.runtime.core.retry import ReliableProvider, get_reliable_provider, UsageTracker  # ★ v1.0
from alice_engine.runtime.core.context_window import (  # ★ v1.0
    ContextWindowMonitor, SessionCompactor, build_continuation_prompt,
    ContextWindowExceededError, WindowStatus, ContinuationResult,  # ★ Task 5
)
from alice_engine.core.skill_loader import SkillLoader
from alice_engine.core.skill_registry import (
    get_skill_requirements,
    check_provider_compatibility,
)
from alice_engine.behavior import resolve_governance_pack_path

from alice_engine.core.task import (
    Observation, AgentState, AgentEvent, AgentEventType,
    ArtifactRule, _ALL_ARTIFACT_RULES, CODE_REDLINE_CHECKS,
)
from alice_engine.core.agent_definitions import AgentDefinitions, FALLBACK_AGENT_SKILL_MAP
from alice_engine.core.output_persistence import (
    save_skill_output, extract_code_block, extract_yaml_block,
)
from alice_engine.core.consistency_checks import (
    run_mechanical_consistency_check, run_llm_consistency_review,
)
from alice_engine.core.runtime_context_builder import RuntimeContextBuilder
from alice_engine.core.runtime_lifecycle import (
    MCPClientLifecycle,
    ProviderRuntimeLifecycle,
    ReplayStepSink,
)
from alice_engine.core.session_orchestrator import SessionLoopOrchestrator
from alice_engine.core.runtime_environment import (
    current_context_modules,
    current_llm_provider,
    current_workstudy,
)
from alice_engine.runtime.core.security import PromptInjectionGuard  # ★ v1.0
from alice_engine.events import EventType, get_bus  # ★ v3.0: SDK 内事件系统

# ── v3.2: 导入拆分后的辅助模块 ─────────────────────────────────────
from alice_engine.core.executor_utils import (
    get_logger,
    get_project_dir,
    get_test_project_root,
    config,
    TraceContext,
    get_tracer,
)
from alice_engine.core.agent_helpers import (
    get_agent_skill_map,
    get_dev_agent_skill_map,
    get_agent_definition,
    run_skill,
    list_agents,
    list_dev_agents,
)

# Backward compatibility — expose at module level
AGENT_SKILL_MAP = get_agent_skill_map()
DEV_AGENT_SKILL_MAP = get_dev_agent_skill_map()


# ══════════════════════════════════════════════════════════════════════════
#  AgentLoop — 真正的 Agent 执行循环 (Perceive → Plan → Act → Observe)
# ══════════════════════════════════════════════════════════════════════════

# [LAYER:Core/Executor] AgentLoop — 核心执行循环 (将拆分为 engine/executor.py + engine/task.py + engine/planner.py + engine/state_machine.py)
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
        _log.info(f"成功: {state.success}, 步骤: {state.step}")
        for obs in state.observations:
            _log.info(f"  {obs.skill_id}: {obs.status}")
    """

    MAX_RETRIES = 3          # 单个 Skill 最大重试次数
    MAX_CONTINUATIONS = 5    # ★ v1.0: 最大 continuation 次数 (参考 Aperant)

    # ══════════════════════════════════════════════════════════════════════════
    #  SECTION 1: INITIALIZATION — 初始化 + 配置 + 属性
    # ══════════════════════════════════════════════════════════════════════════

    # [LAYER:Mixed] __init__ — 混合 Core(Task)/Runtime(Config,Retry)/Adapter(LLM)
    def __init__(
        self,
        agent_name: str,
        provider: str = None,
        verbose: bool = True,
        skill_subset: list = None,
        deep_review: bool = True,
        focused_context: str = None,
        token_budget: int = None,
        use_worktree: bool = False,
        use_reliable_provider: bool = True,    # ★ v1.0: 启用 ReliableProvider
        use_window_monitor: bool = True,       # ★ v1.0: 启用 ContextWindowMonitor
        model: str = None,                     # ★ v1.0: 模型名 (用于窗口限制查询)
        **context,
    ):
        # [LAYER:Runtime/Config] P0: Resolve provider dynamically
        if provider is None:
            provider = config.resolve_llm_provider()

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
        self._skill_subset = skill_subset
        self.deep_review = deep_review
        self._focused_context = focused_context
        self.token_budget = token_budget or 30000
        self._review_triggered = False
        self._interaction_queue: queue.Queue = queue.Queue()
        self.use_worktree = use_worktree

        # [LAYER:Runtime/ErrorHandling] ★ v1.0: Structured logging
        self._logger = get_logger("agent_loop")
        self._worktree_ctx = None

        # [LAYER:Core/Task] ★ v2.6: Abort signal
        self._abort = threading.Event()

        # ★ v3.0: Cleanup attributes — initialized here so _finalize_session
        # is always safe to call (even if _run_single_session fails early).
        # H3 fix: was previously only set inside _run_single_session.
        self._mcp_clients: list = []
        self._mcp_tools: dict = {}
        self._wt_mgr = None
        self._worktree_ctx = None

        # [LAYER:Runtime/Retry] ★ v1.0: Reliability + Context Window
        self._use_reliable = use_reliable_provider
        self._use_window = use_window_monitor
        self._reliable_provider: Optional[ReliableProvider] = None
        self._window_monitor: Optional[ContextWindowMonitor] = None
        self._session_compactor = SessionCompactor()
        self._continuation_count = 0
        self._session_messages: list[dict] = []
        self._replay_recorder = context.get("replay_recorder")
        self._provider_lifecycle = ProviderRuntimeLifecycle(
            agent_name=agent_name,
            log_fn=self._log,
            resolve_agent_definition_fn=get_agent_definition,
            resolve_model_for_tier_fn=config.resolve_model_for_tier,
            resolve_provider_model_fn=self._resolve_model_for_provider,
            get_reliable_provider_fn=get_reliable_provider,
            context_window_monitor_cls=ContextWindowMonitor,
        )
        self._mcp_lifecycle = MCPClientLifecycle(
            agent_name=agent_name,
            log_fn=self._log,
        )
        self._replay_sink = ReplayStepSink(recorder=self._replay_recorder)
        self._session_orchestrator = None

        # [LAYER:Adapter/LLM] ★ v2.0: Capability Router (lazy init)
        self._capability_router = None
        self._use_tool_calling = True  # 默认启用 tool calling

        provider_runtime = self._provider_lifecycle.initialize(
            provider=provider,
            requested_model=model,
            use_reliable_provider=self._use_reliable,
            use_window_monitor=self._use_window,
        )
        provider = provider_runtime["provider"]
        model = provider_runtime["model"]
        self.provider = provider
        self._model_tier = provider_runtime["model_tier"]
        self._reliable_provider = provider_runtime["reliable_provider"]
        self._window_monitor = provider_runtime["window_monitor"]

        # [LAYER:Core/Task] Goal 构建 + AgentState 创建
        module = context.get("module", "")
        page = context.get("page", "")
        goal = context.get("goal", "")

        if not goal:
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
        TraceContext.set(run_id=run_id, agent_name=agent_name,
                         skill_version=TraceContext.get_skill_version())

        self.state = AgentState(
            agent_name=agent_name,
            goal=goal,
            module=module,
            page=page,
            provider=provider,
            max_steps=context.get("max_steps", len(self.skills) * 2),
        )
        self._runtime_context_builder = RuntimeContextBuilder(
            state=self.state,
            module=module,
            page=page,
            goal=goal,
            focused_context=self._focused_context,
            token_budget=self.token_budget,
            log_fn=self._log,
        )
        if self._replay_recorder is not None:
            self.state.memory["replay_session_id"] = getattr(self._replay_recorder, "session_id", "")

    # [LAYER:Core/Executor] HITL 交互
    def send_interaction(self, response: str) -> None:
        """供外部（Chat API）调用，向暂停中的 run_interactive() 发送用户输入。"""
        self._interaction_queue.put(response)

    def cancel(self) -> None:
        """正式公开的取消接口，替代外层直接访问 _abort。"""
        self._abort.set()

    # ── 属性 ──────────────────────────────────────────────────────

    # [LAYER:Core/Task] 任务属性
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

    # ══════════════════════════════════════════════════════════════════════════
    #  SECTION 2: HELPERS — 辅助方法 + 路径解析 + 事件发射
    # ══════════════════════════════════════════════════════════════════════════

    # [LAYER:Runtime/Config] 模型名解析
    @staticmethod
    def _resolve_model_for_provider(provider: str) -> str:
        """根据 provider 名称推断默认模型名（用于 ContextWindowMonitor 查窗口限制）。"""
        from alice_engine.core.skill_registry import get_default_model
        return get_default_model(provider)

    # [LAYER:Adapter/LLM] Capability Router 初始化
    def _get_capability_router(self):
        """★ v2.0: 延迟初始化 CapabilityRouter + ★ v0.4 Capability Enforcement。"""
        if self._capability_router is None and self._use_tool_calling:
            from alice_engine.platform_bridge import create_capability_router
            self._capability_router = create_capability_router()
            if self._capability_router is None:
                self._use_tool_calling = False
        return self._capability_router

    def _init_mcp_clients(self) -> None:
        """Connect MCP clients once per session and cache their tool directory."""
        self._mcp_lifecycle.agent_name = self.agent_name
        self._mcp_clients, self._mcp_tools = self._mcp_lifecycle.connect()

    def _build_runtime_context(self) -> dict:
        """Assemble memory / knowledge context onto the official execution mainline."""
        self._runtime_context_builder.module = self.module
        self._runtime_context_builder.page = self.page
        self._runtime_context_builder.goal = self.state.goal
        return self._runtime_context_builder.build_runtime_context()

    # [LAYER:Adapter/Event] 事件发射
    def _emit_obs(self, event_type: EventType, data: dict = None) -> None:
        """★ v3.0: 发射观测事件到 ObservationBus。"""
        try:
            get_bus().emit(
                event_type, data or {},
                agent_name=self.agent_name,
                module=self.module,
                page=self.page,
            )
        except Exception:
            pass  # 事件发射失败不影响主流程

    # [LAYER:Runtime/ErrorLogging] 日志
    def _log(self, msg: str) -> None:
        if self.verbose:
            self._logger.info(msg)

    # [LAYER:Runtime/Paths] 路径工具函数
    def _slug_to_page_name(self, slug: str) -> str:
        """alarm-config → AlarmConfig, unit-management → UnitManagement"""
        return "".join(part.capitalize() for part in slug.replace("-", " ").split())

    def _page_slug_to_underscore(self, slug: str) -> str:
        """alarm-config → alarm_config"""
        return slug.replace("-", "_")

    def _resolve_artifact_path(self, pattern: str) -> str:
        """将 glob pattern 中的变量替换为实际值。"""
        page_name = self._slug_to_page_name(self.page)
        # Fallback: when page is empty (dev SOP self-build), use module name
        if not page_name and self.module:
            page_name = self._slug_to_page_name(self.module)
        page_slug = self.page or self.module
        resolved = pattern
        # 开发 Agent 使用 dev-platform 上下文路径
        if self.agent_name in DEV_AGENT_SKILL_MAP:
                module_dir = str(_get_governance_root() / "context" / "projects" / "dev-platform")
        else:
            module_dir = str(current_context_modules() / self.module)
        resolved = resolved.replace("{module_dir}", module_dir)
        resolved = resolved.replace("{module}", self.module)
        resolved = resolved.replace("{page}", page_slug)
        resolved = resolved.replace("{PageName}", page_name)
        resolved = resolved.replace("{page_underscore}", self._page_slug_to_underscore(page_slug))
        # Replace {test_project_root} with actual test project root (from project.yaml)
        zjsn = get_test_project_root()
        if zjsn:
            resolved = resolved.replace("{test_project_root}", str(zjsn))
        return resolved

    def _resolve_path(self, pattern: str) -> Path:
        """将 pattern 解析为绝对路径。"""
        resolved = self._resolve_artifact_path(pattern)
        # If path is relative (starts with project name), resolve from WORKSTUDY
        workstudy = get_project_dir()
        if not Path(resolved).is_absolute() and not resolved.startswith(str(workstudy)):
            resolved = str(workstudy / resolved)
        return Path(resolved)

    # ══════════════════════════════════════════════════════════════════════════
    #  SECTION 3: CONTEXT BUILDING — 上下文构建 + 用户输入
    # ══════════════════════════════════════════════════════════════════════════

    # [LAYER:Mixed] _build_context_vars — 基础部分 Core(Planner), ContextBuilder 部分 Adapter(Knowledge)
    def _build_context_vars(self, extra: dict = None) -> dict:
        """构建传递给 run_skill 的上下文变量。

        无-PRD 模式: 注入 Page Object / 测试脚本 / 治理文档的文件路径，
        context_injector 的 SKILL_CONTEXT_MAP 使用这些路径读取并注入文件内容。
        """
        self._runtime_context_builder.module = self.module
        self._runtime_context_builder.page = self.page
        self._runtime_context_builder.goal = self.state.goal
        self._runtime_context_builder.focused_context = self._focused_context
        self._runtime_context_builder.token_budget = self.token_budget
        return self._runtime_context_builder.build_context_vars(extra)

    # [LAYER:Core/Planner] Skill 用户输入构建
    def _build_user_input(self, skill_id: str) -> str:
        """根据当前状态构造 Skill 的用户输入。

        无-PRD 模式: 将 PO/Test 代码内容直接注入 user prompt，
        使 LLM 无法忽视真实代码（user prompt 约束力 > system prompt）。
        """
        parts = []
        if self.module:
            parts.append(f"模块: {self.module}")
        if self.page:
            parts.append(f"页面: {self.page}")
        if self.state.memory.get("task_description"):
            parts.append(f"任务: {self.state.memory['task_description']}")

        # ── 无-PRD 模式: 注入代码内容到 user prompt ──
        # requirement + test-design + automation 都需要真实代码上下文
        # v3.1: 从 FALLBACK_AGENT_SKILL_MAP 动态获取，而非硬编码
        _CODE_SKILL_CATEGORIES = tuple(
            k.replace("-agent", "") for k in FALLBACK_AGENT_SKILL_MAP.keys()
            if k.endswith("-agent") and k not in ("project-agent", "knowledge-agent", "report-agent", "bug-analysis-agent", "execution-agent")
        )
        if any(c in skill_id for c in _CODE_SKILL_CATEGORIES) and self.module and self.page:
            page_name = self._slug_to_page_name(self.page)
            page_underscore = self._page_slug_to_underscore(self.page)
            zjsn = get_test_project_root()
            if zjsn:
                # Read PO file
                po_path = zjsn / "page" / f"{self.module}_page" / f"{page_name}Page.py"
                if po_path.exists():
                    try:
                        po_content = po_path.read_text(encoding="utf-8")
                        parts.append(f"\n## Page Object 代码 ({page_name}Page.py)\n```python\n{po_content[:6000]}\n```")
                    except Exception:
                        pass  # PO file optional — skip silently
                # Read test file
                test_path = zjsn / "script" / self.module / f"test_{page_underscore}.py"
                if test_path.exists():
                    try:
                        test_content = test_path.read_text(encoding="utf-8")
                        parts.append(f"\n## 测试脚本 (test_{page_underscore}.py)\n```python\n{test_content[:4000]}\n```")
                    except Exception:
                        pass  # test file optional — skip silently
            # Read PAGE_CONTEXT if it exists (from requirement phase)
            page_ctx = current_context_modules() / self.module / "pages" / self.page / "PAGE_CONTEXT.md"
            if page_ctx.exists():
                try:
                    ctx_content = page_ctx.read_text(encoding="utf-8")
                    # ★ v1.0: 使用 PromptInjectionGuard 替代 HTML 注释式"防护"
                    parts.append(
                        f"\n## 页面上下文 (PAGE_CONTEXT.md)\n"
                        f"{PromptInjectionGuard.safe_user_input(ctx_content, source='PAGE_CONTEXT.md')}"
                    )
                except Exception:
                    pass

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

    # ══════════════════════════════════════════════════════════════════════════
    #  SECTION 4: PERCEIVE-PLAN-ACT-OBSERVE-UPDATE — 核心执行循环
    # ══════════════════════════════════════════════════════════════════════════

    # ── 1. Perceive（感知）───────────────────────────────────────

    # [LAYER:Core/Planner] 环境感知
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

    # [LAYER:Core/Planner] 规划委托
    def plan(self, skill_index: int, perception: dict) -> dict:
        """委托给 plan_engine 模块。"""
        from alice_engine.core.planner import plan_next_action
        return plan_next_action(
            skill_index, perception, self.skills, self.state,
            logger_fn=self._log)

    # ── 3. Act（执行）────────────────────────────────────────────

    # [LAYER:Mixed] act — 核心执行 Core(Executor), 窗口更新 Runtime(ContextWindow)
    def act(self, skill_id: str) -> LLMResponse:
        """
        执行一个 Skill——调用 LLM 完成具体任务 + 自动保存产出到文件。

        v1.0: 集成 ReliableProvider + ContextWindowMonitor。
        如果是机械化 Skill（如 code-consistency-checker），直接运行本地脚本。
        如果是 review 模式（code-consistency-checker:review），运行 LLM 对抗性审查。
        """
        # ★ #6: LLM 深度审查模式
        if skill_id == "automation/code-consistency-checker:review":
            return self._act_llm_consistency_review()

        # 机械化 Skill 走本地脚本
        if skill_id == "automation/code-consistency-checker":
            return self._act_mechanical_consistency_check()

        context_vars = self._build_context_vars()
        user_input = self._build_user_input(skill_id)

        # ★ v1.0: 窗口检查 (在调用 LLM 前)
        if self._window_monitor:
            status = self._window_monitor.check()
            if status == WindowStatus.HARD:
                raise ContextWindowExceededError(
                    f"Context at {self._window_monitor.usage_ratio:.1%}: "
                    f"{self._window_monitor.current_tokens:,}/{self._window_monitor.limit:,}",
                    current_tokens=self._window_monitor.current_tokens,
                    limit=self._window_monitor.limit,
                )
            if status == WindowStatus.WARN:
                self._log(f"[WARN] {self._window_monitor.status_summary()}")

        # ★ v2.0: 获取 CapabilityRouter（延迟初始化）
        router = self._get_capability_router()

        # ★ v1.0/v2.0: ReliableProvider + Tool Calling
        if self._reliable_provider:
            response = run_skill(
                skill_id=skill_id,
                user_input=user_input,
                provider=self.provider,
                context_vars=context_vars,
                reliable_provider=self._reliable_provider,
                capability_router=router,          # ★ v2.0
                agent_name=self.agent_name,        # ★ v2.0
                mcp_tools=getattr(self, "_mcp_tools", {}),
                mcp_clients=getattr(self, "_mcp_clients", []),
            )
        else:
            response = run_skill(
                skill_id=skill_id,
                user_input=user_input,
                provider=self.provider,
                context_vars=context_vars,
                capability_router=router,          # ★ v2.0
                agent_name=self.agent_name,        # ★ v2.0
                mcp_tools=getattr(self, "_mcp_tools", {}),
                mcp_clients=getattr(self, "_mcp_clients", []),
            )

        # ★ v1.0: 更新窗口 token 计数
        usage = getattr(response, "usage", {}) or {}
        if self._window_monitor and usage:
            self._window_monitor.add_usage(
                usage.get("input", 0),
                usage.get("output", 0),
            )

        # 记录消息历史 (供 continuation 摘要)
        if self._use_window:
            self._session_messages.append({"role": "user", "content": user_input[:500]})
            self._session_messages.append({"role": "assistant", "content": response.content[:500]})

        # API 模式下 LLM 无法自己写文件——AgentLoop 自动保存产出
        if response.finish_reason != "error" and response.content:
            self._save_skill_output(skill_id, response.content)

        return response

    # [LAYER:Core/Executor] 产出保存
    def _save_skill_output(self, skill_id: str, content: str) -> str:
        """将 LLM 输出保存到对应的文件路径。委托给 output_persistence 模块。"""
        return save_skill_output(skill_id, content, self.module, self.page,
                                 self.agent_name, logger_fn=self._log)

    @staticmethod
    def _extract_yaml_block(text: str) -> str:
        return extract_yaml_block(text)

    @staticmethod
    def _extract_code_block(text: str, language: str = "python") -> str:
        return extract_code_block(text, language)

    # [LAYER:Core/Executor] 机械化 Skill 执行
    def _act_mechanical_consistency_check(self) -> LLMResponse:
        """机械化执行代码合规检查（不需要 LLM）。委托给 consistency_checks 模块。"""
        return run_mechanical_consistency_check(
            self.module, self.page, CODE_REDLINE_CHECKS, logger=self._log)

    def _persist_consistency_report(self, lines: list[str], issues: list[str]) -> None:
        """委托给 output_persistence.persist_consistency_report。"""
        from alice_engine.core.output_persistence import persist_consistency_report
        persist_consistency_report(self.module, self.page, lines, issues)

    # [LAYER:Core/Executor] LLM 对抗性审查
    def _act_llm_consistency_review(self) -> LLMResponse:
        """LLM 对抗性审查。委托给 consistency_checks 模块。"""
        return run_llm_consistency_review(
            self.module, self.page, self.provider,
            build_context_vars=self._build_context_vars,
            run_skill_fn=run_skill)

    def _persist_review_report(self, content: str) -> None:
        """委托给 output_persistence.persist_review_report。"""
        from alice_engine.core.output_persistence import persist_review_report
        persist_review_report(self.module, self.page, content)

    # [LAYER:Core/Executor] 产物持久化
    def _persist_skill_artifact(self, skill_id: str, content: str) -> str:
        """Save skill output to expected artifact file immediately.

        Resolves the artifact rule's glob_pattern via _resolve_path() to
        determine the EXACT filepath that observe() will check. This
        guarantees the artifact check finds the file — preventing retry loops.
        """
        if not content or not self.module:
            return ""
        try:
            from pathlib import Path
            import re
            from alice_engine.core.task import _ALL_ARTIFACT_RULES

            # 获取当前 context modules 值（运行时更新）
            context_modules = current_context_modules()

            # Priority 1: Use artifact rule glob_pattern for exact path match
            rules = _ALL_ARTIFACT_RULES.get(skill_id, [])
            filepath = None
            for rule in rules:
                if rule.required:
                    filepath = self._resolve_path(rule.glob_pattern)
                    break

            # Priority 2: Static fallback for skills without artifact rules
            # v3.1: 使用 output_persistence 的映射，消除硬编码
            if filepath is None:
                from alice_engine.core.output_persistence import _skill_to_filename, _SKILL_TO_PAGE_ARTIFACT
                filename = _skill_to_filename(skill_id)

                # 如果是页面级产物且有 page 参数，保存到页面目录
                if skill_id in _SKILL_TO_PAGE_ARTIFACT and self.page:
                    parent_dir = context_modules / self.module / "pages" / self.page
                elif self.agent_name in DEV_AGENT_SKILL_MAP:
                    parent_dir = _get_governance_root() / "context" / "projects" / "dev-platform"
                else:
                    parent_dir = context_modules / self.module
                parent_dir.mkdir(parents=True, exist_ok=True)
                filepath = parent_dir / filename

            filepath.parent.mkdir(parents=True, exist_ok=True)

            # Extract meaningful content from LLM response by file type
            content_md = content
            ext = filepath.suffix.lower()
            if ext in ('.md', '.yaml', '.yml'):
                md_match = re.search(r'```(?:markdown|md|yaml|yml)?\s*\n(.*?)```', content, re.DOTALL)
                if md_match:
                    content_md = md_match.group(1).strip()
            elif ext == '.py':
                py_match = re.search(r'```(?:python|py)\s*\n(.*?)```', content, re.DOTALL)
                if py_match:
                    content_md = py_match.group(1).strip()
            elif ext == '.json':
                json_match = re.search(r'```(?:json)\s*\n(.*?)```', content, re.DOTALL)
                if json_match:
                    content_md = json_match.group(1).strip()

            filepath.write_text(content_md, encoding="utf-8")
            return str(filepath)
        except Exception as e:
            self._log(f"[warn] artifact persist failed: {e}")
            return ""

    # ── 4. Observe（观察）────────────────────────────────────────

    # [LAYER:Mixed] observe — 基础 Core(StateMachine), 安全检查 Runtime(Security)
    def observe(self, skill_id: str, response: LLMResponse) -> Observation:
        """
        验证 Skill 产出质量。

        检查维度:
          - 文件存在性（必需产出文件是否生成）
          - 代码红线（grep 8 条规则）
          - LLM 响应是否异常
          - 🔴 运行时安全检查（敏感信息泄露、高风险操作）
        """
        obs = Observation(
            skill_id=skill_id,
            raw_output_preview=response.content[:500] if response.content else "",
            raw_output_full=response.content or "",  # ★ Full content for artifact persistence
            token_usage=getattr(response, "usage", {}) or {},
        )

        # ★ P0: 运行时安全检查
        # v3.1: safety_auditor 未在 alice_engine 中实现，跳过
        pass

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

        # ★ P1: 失败归因 — 当 status 为 fail/partial 时自动分类
        if obs.status in ("fail", "partial") and obs.raw_output_preview:
            # v3.1: failure_attributor 未在 alice_engine 中实现，使用默认分类
            obs.failure_category = "unknown"

        return obs

    # ── 5. Update（更新状态）──────────────────────────────────────

    # [LAYER:Core/StateMachine] 状态更新
    def update(self, skill_id: str, observation: Observation) -> None:
        """委托给 state_updater 模块。"""
        from alice_engine.core.state_machine import update_agent_state
        update_agent_state(self.state, skill_id, observation,
                          agent_name=self.agent_name, module=self.module, logger=self._log)

    # ── Cache Summary ────────────────────────────────────────────

    # [LAYER:Adapter/Event] 缓存统计事件
    def _emit_cache_summary(self) -> None:
        """v3.1: emit_cache_summary 未在 alice_engine 中实现，跳过。"""
        pass

    # ══════════════════════════════════════════════════════════════════════════
    #  SECTION 5: SESSION MANAGEMENT — 会话管理 + Continuation
    # ══════════════════════════════════════════════════════════════════════════

    # [LAYER:Runtime/ContextWindow] 上下文续传
    def _do_continuation(self) -> None:
        """执行上下文窗口 continuation。

        压缩对话历史 → 构建 continuation prompt → 重置监控器。
        参考 Aperant continuation.ts:165-182。
        """
        self._continuation_count += 1
        self._log(f"[CONTINUE] Session continuation #{self._continuation_count}...")

        # 1. 压缩对话历史
        summary = self._session_compactor.compact(
            self._session_messages,
            agent_memory=self.state.memory,
        )

        # 2. 构建 continuation prompt
        continuation_msg = build_continuation_prompt(summary, self._continuation_count)

        # 3. 重置状态
        self._session_messages = [{"role": "user", "content": continuation_msg}]
        if self._window_monitor:
            self._window_monitor = ContextWindowMonitor(
                model=self._window_monitor.model,
                model_limit=self._window_monitor.limit,
            )
            self._window_monitor.add_message("user", continuation_msg[:3000])

        # 4. 注入摘要为 focused context (使 Agent 能快速理解上下文)
        self._focused_context = continuation_msg

        self._log(f"  摘要: {len(summary)} chars | 窗口已重置")

    # ── 主循环 ───────────────────────────────────────────────────

    # [LAYER:Core/Executor] 主循环 (含 continuation 包装)
    def run(self) -> AgentState:
        """
        执行 Agent 主循环: Perceive → Plan → Act → Observe → Update

        v1.0: 带 continuation 支持。当上下文窗口超限时自动摘要续跑。
        参考 Aperant continuation.ts runContinuableSession()。

        循环直到:
          - 所有 Skill 完成
          - 达到最大步数
          - Agent 决定中止
          - 达到最大 continuation 次数
        """
        pass  # telemetry removed
        otel = get_tracer()

        self._session_start = time.time()  # ★ v1.1: for operational metrics
        self._session_finalized = False

        # ★ v1.0: Continuation loop (参考 Aperant: 最多 5 次)
        # ★ Task 5 (P1): ContinuationResult tracking added
        cr = ContinuationResult()
        try:
            while True:
                try:
                    with otel.start_as_current_span(f"agent.{self.agent_name}") as span:
                        span.set_attribute("agent_name", self.agent_name)
                        span.set_attribute("provider", self.provider)
                        span.set_attribute("module", self.module or "")
                        span.set_attribute("page", self.page or "")
                        result = self._run_single_session()
                        # Merge continuation stats into state memory for reporting
                        if cr.was_continued:
                            self.state.memory["continuation"] = {
                                "count": cr.continuation_count,
                                "total_tokens": cr.total_tokens,
                            }
                            self._log(f"[CONTINUE] {cr.summary()}")
                        return result
                except ContextWindowExceededError:
                    if self._continuation_count >= self.MAX_CONTINUATIONS:
                        self._log(f"[CONTINUE] Max continuations ({self.MAX_CONTINUATIONS}) reached. Stopping.")
                        self.state.done = True
                        self.state.success = False
                        self.state.termination_reason = "max_continuations_reached"
                        return self.state
                    cr.continuation_count += 1
                    if self._window_monitor:
                        cr.cumulative_input_tokens += self._window_monitor._cumulative_input
                        cr.cumulative_output_tokens += self._window_monitor._cumulative_output
                    cr.total_tokens = cr.cumulative_input_tokens + cr.cumulative_output_tokens
                    self._do_continuation()
        finally:
            if not self._session_finalized:
                self._finalize_session()

    # ══════════════════════════════════════════════════════════════════════════
    #  SECTION 6: FINALIZATION — 会话清理 + 资源释放
    # ══════════════════════════════════════════════════════════════════════════

    # [LAYER:Mixed] _finalize_session — 日志/清理 Core(Executor), 指标 Runtime(Metrics)
    def _finalize_session(self) -> None:
        """Cleanup after session ends — always called (normal + exception paths).

        Handles: logging, event emission, worktree cleanup, MCP close,
        artifact lineage, metrics. Best-effort per step — failure in one
        does not prevent subsequent steps.
        Idempotent — safe to call multiple times.
        """
        if getattr(self, "_session_finalized", False):
            return
        self._session_finalized = True

        completed = len(self.state.completed_skills)
        failed = len(self.state.failed_skills)
        total_steps = self.state.step
        self._log(
            f"🏁 Agent 结束: {completed} 完成 / {failed} 失败 / "
            f"{total_steps} 步 | {self.state.termination_reason}"
        )

        self._emit_cache_summary()

        # Emit agent completion event
        self._emit_obs(EventType.AGENT_COMPLETE, {
            "completed": completed, "failed": failed, "steps": total_steps,
            "termination": self.state.termination_reason,
        })

        # Online monitor metrics
        # v3.1: online_monitor 未在 alice_engine 中实现，跳过
        pass

        # Worktree cleanup — merge on success, keep for inspection on failure
        _wt_mgr = getattr(self, "_wt_mgr", None)
        _worktree_ctx = getattr(self, "_worktree_ctx", None)
        if _wt_mgr and _worktree_ctx:
            try:
                has_writes = any(
                    s in self.state.completed_skills
                    for s in self.skills
                    if "automation" in s or "code" in s or "generator" in s or "page-object" in s
                )
                if self.state.success and has_writes:
                    _worktree_ctx.mark_success()
                _wt_mgr.merge_and_cleanup(_worktree_ctx)
                self._log(
                    f"🔓 Worktree: {'merged ✅' if _worktree_ctx.success else 'kept for inspection'}"
                    f" — {_worktree_ctx.name}"
                )
            except Exception as e:
                self._log(f"⚠️ Worktree cleanup error: {e}")

        # MCP client cleanup — close connections
        _mcp_clients = getattr(self, "_mcp_clients", [])
        if _mcp_clients:
            self._mcp_lifecycle.close_all(_mcp_clients)

        # Artifact lineage
        # v3.1: artifact_lineage 未在 alice_engine 中实现，跳过
        pass

        # Operational metrics
        # v3.1: operational_metrics 未在 alice_engine 中实现，跳过 daemon thread
        pass

    # ══════════════════════════════════════════════════════════════════════════
    #  SECTION 7: MAIN LOOP — 单次会话主循环
    # ══════════════════════════════════════════════════════════════════════════

    # [LAYER:Core/Executor] 单次会话主循环
    def _run_single_session(self) -> AgentState:
        """执行单次 Agent session（不带 continuation 包装）。

        TODO (H3): Wrap method body in try-finally to guarantee worktree/MCP
        cleanup on exception. Current: cleanup only on normal return path.
        Requires re-indenting ~200 lines — deferred to dedicated refactor PR.
        """
        # 🆕 TLO: Worktree 隔离
        self._wt_mgr = None
        if self.use_worktree:
            # v3.1: WorktreeManager 未在 alice_engine 中实现，跳过
            self.use_worktree = False

        # ── Task 6 (P1): MCP Client — connect to external tools ──
        self._init_mcp_clients()

        self._log(f"🤖 Agent: {self.agent_name} | Provider: {self.provider}")
        self._log(f"  目标: {self.state.goal}")
        self._log(f"  Skill 链: {' → '.join(self.skills)}")
        self._log(f"  最大步数: {self.state.max_steps}")
        if self._continuation_count > 0:
            self._log(f"  🔄 Continuation #{self._continuation_count}")
        self._log("-" * 60)

        skill_index = 0
        self._session_orchestrator = SessionLoopOrchestrator(
            state=self.state,
            skills=self.skills,
            agent_name=self.agent_name,
            module=self.module,
            page=self.page,
            provider=self.provider,
            abort_event=getattr(self, "_abort", None),
            replay_sink=self._replay_sink,
            replay_recorder=self._replay_recorder,
            perceive_fn=self.perceive,
            plan_fn=self.plan,
            act_fn=self.act,
            observe_fn=self.observe,
            update_fn=self.update,
            persist_skill_artifact_fn=self._persist_skill_artifact,
            emit_obs_fn=self._emit_obs,
            log_fn=self._log,
            retry_counts=self.state.retry_counts,
            completed_skills_getter=lambda: self.state.completed_skills,
        )

        while not self.state.done and self.state.step < self.state.max_steps:
            iteration = self._session_orchestrator.run_iteration(skill_index)
            skill_index = iteration.next_skill_index
            if not iteration.should_continue:
                break

        self._session_orchestrator.apply_max_steps_termination()

        self._finalize_session()
        return self.state

    # ── 交互式主循环 ───────────────────────────────────────────────

    # [LAYER:Core/Executor] 交互式主循环
    def run_interactive(self):
        """v3.1: 交互式执行 — 生成 AgentEvent 流。

        实现简单版本：执行 run() 并将结果转换为 AgentEvent 流。
        完整的 interactive_runner 实现在 aitest/agents/interactive_runner.py。
        """
        yield AgentEvent(type="agent_start", agent_name=self.agent_name, content="Starting...")
        try:
            state = self.run()
            yield AgentEvent(
                type="agent_end",
                status="pass" if state.success else "fail",
                content=f"Completed: {state.step} steps",
                summary=f"Steps: {state.step}",
            )
        except Exception as e:
            yield AgentEvent(type="agent_end", status="fail", error=str(e))



# ══════════════════════════════════════════════════════════════════════════
#  run_agent() — 兼容旧接口，内部委托给 AgentLoop
# ══════════════════════════════════════════════════════════════════════════

# [LAYER:Core/Executor] 兼容旧接口
def run_agent(
    agent_name: str,
    provider: str = None,
    verbose: bool = True,
    **kwargs,
) -> dict:
    """
    执行一个 Agent（多个 Skill 串行编排）——兼容旧接口。

    内部委托给 AgentLoop.run()。
    """
    if provider is None:
        provider = config.resolve_llm_provider()
    agent = AgentLoop(agent_name, provider=provider, verbose=verbose, **kwargs)
    state = agent.run()
    return state.to_dict()


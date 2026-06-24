"""Agent Runner — Agent 执行循环核心。

P0 重构 (2026-06-12): 从顺序 for 循环升级为真正的 Agent 循环。
P1 重构 (2026-06-17): 拆分为 runner_state / skill_executor / agent_runner 三文件。
v1.0 (2026-06-23): 集成 ReliableProvider + ContextWindowMonitor + PromptInjectionGuard

用法:
    from aitest.agents.agent_runner import AgentLoop, run_agent, list_agents
    from aitest.agents.runner_state import Observation, AgentState, AgentEvent
    from aitest.agents.skill_executor import AGENT_SKILL_MAP, run_skill

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

# Fix Windows GBK encoding for emoji output
if hasattr(sys.stdout, 'buffer'):
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

from aitest.llm.provider import LLMResponse, StreamEvent, get_provider
from aitest.llm.reliable_provider import ReliableProvider, get_reliable_provider, get_usage_tracker  # ★ v1.0
from aitest.llm.context_window import (  # ★ v1.0
    ContextWindowMonitor, SessionCompactor, build_continuation_prompt,
    ContextWindowExceededError, WindowStatus,
)
from aitest.llm.skill_loader import load_skill
from aitest.llm.skill_registry import (
    get_skill_requirements,
    check_provider_compatibility,
)

from aitest.agents.runner_state import (
    Observation, AgentState, AgentEvent, AgentEventType,
    ArtifactRule, _ALL_ARTIFACT_RULES, CODE_REDLINE_CHECKS,
)
from aitest.agents.skill_executor import (
    AGENT_SKILL_MAP, DEV_AGENT_SKILL_MAP, _ALL_SKILL_MAP,
    run_skill, _shared_injector, _shared_adapter,
    get_agent_definition, GOVERNANCE,
)
from aitest.agents.output_persistence import (
    save_skill_output, extract_code_block, extract_yaml_block,
)
from aitest.agents.consistency_checks import (
    run_mechanical_consistency_check, run_llm_consistency_review,
)
from aitest.infra.security import PromptInjectionGuard  # ★ v1.0
from aitest.platform.observation_bus import get_bus, EventType  # ★ v3.0

# ── 路径配置 ──────────────────────────────────────────────────────────
from aitest.platform.paths import get_workstudy, get_test_project_root, get_context_modules, get_project_dir
WORKSTUDY = get_workstudy()
CONTEXT_MODULES = get_context_modules()  # resolves from active project


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

    MAX_RETRIES = 3          # 单个 Skill 最大重试次数
    MAX_CONTINUATIONS = 5    # ★ v1.0: 最大 continuation 次数 (参考 Aperant)

    def __init__(
        self,
        agent_name: str,
        provider: str = "claude",
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

        # ★ v1.0: Structured logging
        from aitest.infra.logging import get_logger
        self._logger = get_logger("agent_loop").bind(
            agent=agent_name,
            module=context.get("module", ""),
            page=context.get("page", ""),
        )
        self._worktree_ctx = None

        # ★ v1.0: Reliability + Context Window
        self._use_reliable = use_reliable_provider
        self._use_window = use_window_monitor
        self._reliable_provider: Optional[ReliableProvider] = None
        self._window_monitor: Optional[ContextWindowMonitor] = None
        self._session_compactor = SessionCompactor()
        self._continuation_count = 0
        self._session_messages: list[dict] = []

        # ★ v2.0: Capability Router (lazy init)
        self._capability_router = None
        self._use_tool_calling = True  # 默认启用 tool calling

        # ★ v0.5: Phase-Aware Model Tier — 从 agent 定义读取 tier 并解析模型
        self._model_tier = "balanced"
        try:
            agent_def = get_agent_definition(agent_name)
            self._model_tier = agent_def.get("model_tier", "balanced")
        except Exception:
            pass
        if model is None:
            from aitest.config import config
            tier_cfg = config.resolve_model_for_tier(self._model_tier, provider)
            model = tier_cfg["model"]
            if tier_cfg["provider"] != provider:
                provider = tier_cfg["provider"]

        # 初始化可靠性 Provider
        if self._use_reliable:
            self._reliable_provider = get_reliable_provider(primary=provider)

        # 初始化窗口监控器
        if self._use_window:
            from aitest.llm.context_window import MODEL_CONTEXT_LIMITS
            resolved_model = model or self._resolve_model_for_provider(provider)
            self._window_monitor = ContextWindowMonitor(model=resolved_model)

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
        from aitest.infra.trace import TraceContext
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

    @staticmethod
    def _resolve_model_for_provider(provider: str) -> str:
        """根据 provider 名称推断默认模型名（用于 ContextWindowMonitor 查窗口限制）。"""
        defaults = {
            "claude": "claude-sonnet-4-6",
            "openai": "gpt-4o-mini",
            "deepseek": "deepseek-chat",
            "ollama": "qwen3-14b",
        }
        return defaults.get(provider, "claude-sonnet-4-6")

    def _get_capability_router(self):
        """★ v2.0: 延迟初始化 CapabilityRouter + ★ v0.4 Capability Enforcement。"""
        if self._capability_router is None and self._use_tool_calling:
            try:
                from aitest.platform.capability_router import get_router
                self._capability_router = get_router()

                # ★ v0.4: 加载 Agent → Capability 映射并注入 Router
                from aitest.agents.skill_executor import get_agent_definition, GOVERNANCE
                import yaml
                agents_yaml = GOVERNANCE / "agents" / "agent-definitions.yaml"
                if agents_yaml.exists():
                    data = yaml.safe_load(agents_yaml.read_text(encoding="utf-8"))
                    mapping = {}
                    for name, cfg in data.get("agents", {}).items():
                        caps = cfg.get("capabilities", [])
                        if caps:
                            mapping[name] = caps
                    if mapping:
                        self._capability_router.set_agent_capabilities(mapping)
            except Exception:
                self._use_tool_calling = False  # 降级：不使用 tool calling
        return self._capability_router

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

    def _log(self, msg: str) -> None:
        if self.verbose:
            self._logger.info("agent_log", msg=msg)

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
        # Replace {test_project_root} with actual test project root (from project.yaml)
        zjsn = get_test_project_root()
        if zjsn:
            resolved = resolved.replace("{test_project_root}", str(zjsn))
        return resolved

    def _resolve_path(self, pattern: str) -> Path:
        """将 pattern 解析为绝对路径。"""
        resolved = self._resolve_artifact_path(pattern)
        # If path is relative (starts with project name), resolve from WORKSTUDY
        if not Path(resolved).is_absolute() and not resolved.startswith(str(WORKSTUDY)):
            resolved = str(WORKSTUDY / resolved)
        return Path(resolved)

    def _build_context_vars(self, extra: dict = None) -> dict:
        """构建传递给 run_skill 的上下文变量。

        无-PRD 模式: 注入 Page Object / 测试脚本 / 治理文档的文件路径，
        context_injector 的 SKILL_CONTEXT_MAP 使用这些路径读取并注入文件内容。
        """
        vars_ = {
            "module": self.module,
            "page": self.page,
        }
        # 将 memory 中的关键信息注入
        if self.state.memory.get("prev_output"):
            vars_["prev_output"] = str(self.state.memory["prev_output"])[:3000]
        if self.state.memory.get("tech_analysis_summary"):
            vars_["tech_analysis_summary"] = self.state.memory["tech_analysis_summary"]

        # ── 无-PRD 模式: 注入文件路径供 context_injector 使用 ──
        if self.module:
            page_name = self._slug_to_page_name(self.page) if self.page else ""
            page_underscore = self._page_slug_to_underscore(self.page) if self.page else ""
            zjsn = get_test_project_root()

            # PROJECT_CONTEXT 路径
            project_ctx = get_project_dir() / "PROJECT_CONTEXT.md"
            if project_ctx.exists():
                vars_["project_context_path"] = str(project_ctx)

            # Page Object 路径 (from test project root)
            if zjsn:
                po_path = zjsn / "page" / f"{self.module}_page" / f"{page_name}Page.py"
                if page_name and po_path.exists():
                    vars_["po_path"] = str(po_path)

                # 测试脚本路径
                test_path = zjsn / "script" / self.module / f"test_{page_underscore}.py"
                if page_underscore and test_path.exists():
                    vars_["test_path"] = str(test_path)

                # Page Object 目录（用于 module-modeling 发现页面）
                po_dir = zjsn / "page" / f"{self.module}_page"
                if po_dir.exists():
                    vars_["po_dir"] = str(po_dir)

                # 测试脚本目录
                test_dir = zjsn / "script" / self.module
                if test_dir.exists():
                    vars_["test_dir"] = str(test_dir)

            # 页面目录（治理文档目标路径）
            page_dir = CONTEXT_MODULES / self.module / "pages" / self.page
            if self.page:
                vars_["page_dir"] = str(page_dir)

        # ContextAgent 精准 context —— 优先级高于 SKILL_CONTEXT_MAP 文件读取
        if self._focused_context:
            vars_["focused_context"] = self._focused_context

        # ★ P2 RAG: Token 预算估算
        # 粗估：已使用 token 从 trace 中获取，或用步数估算
        # 简单做法：根据 step 预估已消耗（每 step ~2k token）
        estimated_used = self.state.step * 2000
        estimated_remaining = max(1000, self.token_budget - estimated_used)
        vars_["token_budget_remaining"] = estimated_remaining

        if extra:
            vars_.update(extra)
        return vars_

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
        _CODE_SKILL_CATEGORIES = ("requirement", "test-design", "automation")
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
                        pass
                # Read test file
                test_path = zjsn / "script" / self.module / f"test_{page_underscore}.py"
                if test_path.exists():
                    try:
                        test_content = test_path.read_text(encoding="utf-8")
                        parts.append(f"\n## 测试脚本 (test_{page_underscore}.py)\n```python\n{test_content[:4000]}\n```")
                    except Exception:
                        pass
            # Read PAGE_CONTEXT if it exists (from requirement phase)
            page_ctx = CONTEXT_MODULES / self.module / "pages" / self.page / "PAGE_CONTEXT.md"
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
        """委托给 plan_engine 模块。"""
        from aitest.agents.plan_engine import plan_next_action
        return plan_next_action(
            skill_index, perception, self.skills, self.state,
            self.deep_review, self._review_triggered, self.MAX_RETRIES,
            self.provider, logger=self._log)

    # ── 3. Act（执行）────────────────────────────────────────────

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
            )
        else:
            response = run_skill(
                skill_id=skill_id,
                user_input=user_input,
                provider=self.provider,
                context_vars=context_vars,
                capability_router=router,          # ★ v2.0
                agent_name=self.agent_name,        # ★ v2.0
            )

        # ★ v1.0: 更新窗口 token 计数
        if self._window_monitor and response.token_usage:
            self._window_monitor.add_usage(
                response.token_usage.get("input", 0),
                response.token_usage.get("output", 0),
            )

        # 记录消息历史 (供 continuation 摘要)
        if self._use_window:
            self._session_messages.append({"role": "user", "content": user_input[:500]})
            self._session_messages.append({"role": "assistant", "content": response.content[:500]})

        # API 模式下 LLM 无法自己写文件——AgentLoop 自动保存产出
        if response.finish_reason != "error" and response.content:
            self._save_skill_output(skill_id, response.content)

        return response

    def _save_skill_output(self, skill_id: str, content: str) -> str:
        """将 LLM 输出保存到对应的文件路径。委托给 output_persistence 模块。"""
        return save_skill_output(skill_id, content, self.module, self.page,
                                 self.agent_name, logger=self._log)

    @staticmethod
    def _extract_yaml_block(text: str) -> str:
        return extract_yaml_block(text)

    @staticmethod
    def _extract_code_block(text: str, language: str = "python") -> str:
        return extract_code_block(text, language)

    def _act_mechanical_consistency_check(self) -> LLMResponse:
        """机械化执行代码合规检查（不需要 LLM）。委托给 consistency_checks 模块。"""
        return run_mechanical_consistency_check(
            self.module, self.page, CODE_REDLINE_CHECKS, logger=self._log)

    def _persist_consistency_report(self, lines: list[str], issues: list[str]) -> None:
        """委托给 output_persistence.persist_consistency_report。"""
        from aitest.agents.output_persistence import persist_consistency_report
        persist_consistency_report(self.module, self.page, lines, issues)

    def _act_llm_consistency_review(self) -> LLMResponse:
        """LLM 对抗性审查。委托给 consistency_checks 模块。"""
        return run_llm_consistency_review(
            self.module, self.page, self.provider,
            build_context_vars=self._build_context_vars,
            run_skill_fn=run_skill)

    def _persist_review_report(self, content: str) -> None:
        """委托给 output_persistence.persist_review_report。"""
        from aitest.agents.output_persistence import persist_review_report
        persist_review_report(self.module, self.page, content)

    # ── 4. Observe（观察）────────────────────────────────────────

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
            raw_output_preview=response.content[:200] if response.content else "",
            token_usage=response.token_usage,
        )

        # ★ P0: 运行时安全检查
        try:
            from aitest.audit_engine.safety_auditor import check_output_safety
            safety_flags = check_output_safety(response.content or "", skill_id)
            if safety_flags:
                obs.safety_flags = safety_flags
                # 高严重度 flag 升级建议
                if any(f["severity"] == "critical" for f in safety_flags):
                    obs.quality_issues.append(
                        f"🔴 安全告警: {[f['detail'] for f in safety_flags if f['severity'] == 'critical']}"
                    )
        except Exception:
            pass  # 安全检查失败不应阻塞 Agent 执行

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
            try:
                from aitest.audit_engine.failure_attributor import attribute_failure
                obs.failure_category = attribute_failure(obs, response.content or "")
            except Exception:
                pass

        return obs

    # ── 5. Update（更新状态）──────────────────────────────────────

    def update(self, skill_id: str, observation: Observation) -> None:
        """委托给 state_updater 模块。"""
        from aitest.agents.state_updater import update_agent_state
        update_agent_state(self.state, skill_id, observation,
                          agent_name=self.agent_name, logger=self._log)

    # ── Cache Summary ────────────────────────────────────────────

    def _emit_cache_summary(self) -> None:
        """委托给 state_updater.emit_cache_summary（P1 可观测性）。"""
        try:
            from aitest.agents.state_updater import emit_cache_summary
            emit_cache_summary(
                shared_injector=_shared_injector,
                shared_adapter=_shared_adapter,
                logger=self._log,
            )
        except Exception:
            pass

    # ── Continuation ──────────────────────────────────────────────

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
        from aitest.infra.telemetry import get_tracer
        otel = get_tracer()

        self._session_start = time.time()  # ★ v1.1: for operational metrics

        # ★ v1.0: Continuation loop (参考 Aperant: 最多 5 次)
        while True:
            try:
                with otel.start_as_current_span(f"agent.{self.agent_name}") as span:
                    span.set_attribute("agent_name", self.agent_name)
                    span.set_attribute("provider", self.provider)
                    span.set_attribute("module", self.module or "")
                    span.set_attribute("page", self.page or "")
                    return self._run_single_session()
            except ContextWindowExceededError:
                if self._continuation_count >= self.MAX_CONTINUATIONS:
                    self._log(f"[CONTINUE] Max continuations ({self.MAX_CONTINUATIONS}) reached. Stopping.")
                    self.state.done = True
                    self.state.success = False
                    self.state.termination_reason = "max_continuations_reached"
                    return self.state
                self._do_continuation()

    def _run_single_session(self) -> AgentState:
        """执行单次 Agent session（不带 continuation 包装）。"""
        # 🆕 TLO: Worktree 隔离
        wt_mgr = None
        if self.use_worktree:
            from aitest.infra.worktree_manager import WorktreeManager
            wt_mgr = WorktreeManager()
            self._worktree_ctx = wt_mgr.create(
                name=None,
                agent=self.agent_name,
            )
            self._log(f"🔒 Worktree: {self._worktree_ctx.path}")
            self._log(f"   分支: {self._worktree_ctx.branch} (from {self._worktree_ctx.base_branch})")

        self._log(f"🤖 Agent: {self.agent_name} | Provider: {self.provider}")
        self._log(f"  目标: {self.state.goal}")
        self._log(f"  Skill 链: {' → '.join(self.skills)}")
        self._log(f"  最大步数: {self.state.max_steps}")
        if self._continuation_count > 0:
            self._log(f"  🔄 Continuation #{self._continuation_count}")
        self._log("-" * 60)

        skill_index = 0

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

            if plan_result["action"] == "confirm_required":
                skill_id = plan_result["skill_id"]
                self._log(f"  ⏸️  HITL: 等待确认执行 '{skill_id}' "
                         f"(risk={plan_result.get('risk_level', 'high')})")
                try:
                    from aitest.agents.plan_engine import confirm_skill
                    confirm_skill(skill_id, self.module)
                    self._log(f"  ✅ 已确认 '{skill_id}'，继续执行")
                except Exception:
                    pass
                plan_result = self.plan(skill_index, perception)
                if plan_result["action"] in ("confirm_required", "done", "abort"):
                    continue

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
                self._emit_obs(EventType.SKILL_RETRY, {"skill_id": skill_id, "attempt": retry_n})
            else:
                self._log(f"  ▶️  [{skill_index + 1}/{len(self.skills)}] {skill_id}...")
                self._emit_obs(EventType.SKILL_START, {"skill_id": skill_id})

            response = self.act(skill_id)

            if not is_retry and response.finish_reason != "error":
                elapsed = response.token_usage.get("elapsed_seconds", 0)
                tokens_in = response.token_usage.get("input", 0)
                tokens_out = response.token_usage.get("output", 0)
                self._log(f"✅ {elapsed:.1f}s | {tokens_in}+{tokens_out} tokens")
                self._emit_obs(EventType.SKILL_COMPLETE, {
                    "skill_id": skill_id, "elapsed": elapsed,
                    "tokens_in": tokens_in, "tokens_out": tokens_out,
                })
            elif response.finish_reason == "error":
                self._emit_obs(EventType.SKILL_FAILED, {
                    "skill_id": skill_id, "error": response.content[:200],
                })

            # ── 4. Observe ──
            observation = self.observe(skill_id, response)

            # ── 5. Update ──
            self.update(skill_id, observation)

            self.state.step += 1

            if observation.suggestion == "retry":
                pass
            elif observation.suggestion == "skip":
                skill_index += 1
            else:
                skill_index += 1

            if skill_index >= len(self.skills):
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

        self._emit_cache_summary()

        # ★ v3.0: Emit agent completion event
        self._emit_obs(EventType.AGENT_COMPLETE, {
            "completed": completed, "failed": failed, "steps": total_steps,
            "termination": self.state.termination_reason,
        })

        try:
            from aitest.audit_engine.online_monitor import collect_run_metrics, OnlineMonitor
            metrics = collect_run_metrics(self.state)
            OnlineMonitor().record_run(self.module, metrics)
        except Exception:
            pass

        # 🆕 TLO: Worktree cleanup — 成功则合并，失败则保留供检查
        if wt_mgr and self._worktree_ctx:
            has_writes = any(
                s in self.state.completed_skills
                for s in self.skills
                if "automation" in s or "code" in s or "generator" in s or "page-object" in s
            )
            if self.state.success and has_writes:
                self._worktree_ctx.mark_success()
            wt_mgr.merge_and_cleanup(self._worktree_ctx)
            self._log(
                f"🔓 Worktree: {'merged ✅' if self._worktree_ctx.success else 'kept for inspection'}"
                f" — {self._worktree_ctx.name}"
            )

        # ★ v1.5: Record artifact lineage
        if self.module and self.page and self.state.success:
            try:
                from aitest.platform.artifact_lineage import record_artifact, PHASE_ARTIFACTS
                phase_info = PHASE_ARTIFACTS.get(self.agent_name, {})
                for artifact in phase_info.get("produces", []):
                    record_artifact(
                        self.context.get("project", "default"), self.module, self.page,
                        artifact,
                        generated_by=self.agent_name,
                        depends_on=phase_info.get("depends_on", []),
                    )
            except Exception:
                pass

        # ★ v1.1: Record operational metrics
        try:
            from aitest.platform.operational_metrics import get_collector
            mc = get_collector()
            duration = time.time() - self._session_start if hasattr(self, '_session_start') else 0
            tokens = self.state.usage.get("total_tokens", 0) if hasattr(self.state, 'usage') else 0
            tokens_in = self.state.usage.get("input_tokens", 0) if hasattr(self.state, 'usage') else 0
            tokens_out = self.state.usage.get("output_tokens", 0) if hasattr(self.state, 'usage') else 0
            mc.record_agent_run(
                self.agent_name,
                duration_s=max(duration, 0.1),
                tokens_in=tokens_in,
                tokens_out=tokens_out,
                success=self.state.success,
            )
            mc.record_workflow(self.module or "unknown", self.state.success)
            if not self.state.success:
                mc.record_recovery(self.agent_name, recovered=False)
            mc.persist()
        except Exception:
            pass  # metrics never block execution

        return self.state

    # ── 交互式主循环 ───────────────────────────────────────────────

    def run_interactive(self):
        """委托给 interactive_runner 模块。"""
        from aitest.agents.interactive_runner import run_interactive_loop
        return run_interactive_loop(self)



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

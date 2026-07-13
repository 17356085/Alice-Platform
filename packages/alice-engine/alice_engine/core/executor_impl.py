"""Executor Implementation — Skill 执行核心逻辑。

从 executor.py (AgentLoop) 拆出。负责:
  - perceive(): 环境感知（artifact 幂等性检查）
  - act(): 调用 LLM 执行 Skill + 窗口管理 + 产出保存
  - persist / continuation / finalize: 资源管理

与 state_updater.py 不互相引用，只通过 AgentLoop 编排。
"""

import logging
import os
import re
import threading
import time
from pathlib import Path
from typing import Any, Callable, Optional

from alice_engine.providers.base import LLMResponse
from alice_engine.runtime.core.context_window import (
    ContextWindowMonitor, SessionCompactor, build_continuation_prompt,
    ContextWindowExceededError, WindowStatus,
)
from alice_engine.core.task import (
    Observation, AgentState, ArtifactRule, _ALL_ARTIFACT_RULES, CODE_REDLINE_CHECKS,
)
from alice_engine.core.output_persistence import save_skill_output
from alice_engine.core.consistency_checks import (
    run_mechanical_consistency_check, run_llm_consistency_review,
)
from alice_engine.runtime.core.security import PromptInjectionGuard
from alice_engine.events import EventType

logger = logging.getLogger(__name__)

# ── 路径工具（共用模块）─────────────────────────────────────────────
from alice_engine.core.path_utils import (
    slug_to_page_name, page_slug_to_underscore,
    resolve_artifact_path, resolve_path,
    _WORKSTUDY, _CONTEXT_MODULES, _GOVERNANCE,
    get_test_project_root, _get_project_dir,
)


# ══════════════════════════════════════════════════════════════════════════
#  SkillExecutor
# ══════════════════════════════════════════════════════════════════════════

class SkillExecutor:
    """执行 Skill 的核心逻辑，从 AgentLoop 迁出。

    不持有 AgentLoop 引用——所有依赖通过构造函数注入。
    与 state_updater.py 不互相引用。
    """

    def __init__(
        self,
        agent_name: str,
        module: str,
        page: str,
        provider: str,
        state: AgentState,
        reliable_provider: Any = None,
        window_monitor: Optional[ContextWindowMonitor] = None,
        session_messages: Optional[list] = None,
        focused_context: Optional[str] = None,
        token_budget: int = 30000,
        abort_event: Optional[threading.Event] = None,
        dev_agent_map: Optional[set] = None,
        emit_obs: Optional[Callable] = None,
        log_fn: Optional[Callable] = None,
        run_skill_fn: Optional[Callable] = None,
    ):
        self.agent_name = agent_name
        self.module = module
        self.page = page
        self.provider = provider
        self.state = state
        self._reliable_provider = reliable_provider
        self._window_monitor = window_monitor
        self._session_messages = session_messages if session_messages is not None else []
        self._focused_context = focused_context
        self.token_budget = token_budget
        self._abort = abort_event
        self._dev_agent_map = dev_agent_map or set()
        self._emit_obs = emit_obs or (lambda *a, **kw: None)
        self._log = log_fn or (lambda msg: None)
        self._run_skill = run_skill_fn or _default_run_skill

    # ── 路径辅助（委托模块级函数）────────────────────────────────────

    def _resolve_path(self, pattern: str) -> Path:
        return resolve_path(pattern, self.module, self.page, self.agent_name, self._dev_agent_map)

    # ── 上下文构建 ──────────────────────────────────────────────────

    def build_context_vars(self, extra: dict = None) -> dict:
        """构建传递给 run_skill 的上下文变量。"""
        vars_ = {
            "module": self.module,
            "page": self.page,
        }
        if self.state.memory.get("prev_output"):
            vars_["prev_output"] = str(self.state.memory["prev_output"])[:3000]
        if self.state.memory.get("tech_analysis_summary"):
            vars_["tech_analysis_summary"] = self.state.memory["tech_analysis_summary"]

        if self.module:
            page_name = slug_to_page_name(self.page) if self.page else ""
            page_underscore = page_slug_to_underscore(self.page) if self.page else ""
            zjsn = get_test_project_root()

            project_ctx = _get_project_dir() / "PROJECT_CONTEXT.md"
            if project_ctx.exists():
                vars_["project_context_path"] = str(project_ctx)

            if zjsn:
                po_path = zjsn / "page" / f"{self.module}_page" / f"{page_name}Page.py"
                if page_name and po_path.exists():
                    vars_["po_path"] = str(po_path)

                test_path = zjsn / "script" / self.module / f"test_{page_underscore}.py"
                if page_underscore and test_path.exists():
                    vars_["test_path"] = str(test_path)

                po_dir = zjsn / "page" / f"{self.module}_page"
                if po_dir.exists():
                    vars_["po_dir"] = str(po_dir)

                test_dir = zjsn / "script" / self.module
                if test_dir.exists():
                    vars_["test_dir"] = str(test_dir)

            page_dir = _CONTEXT_MODULES / self.module / "pages" / self.page
            if self.page:
                vars_["page_dir"] = str(page_dir)

        if self._focused_context:
            vars_["focused_context"] = self._focused_context

        estimated_used = self.state.step * 2000
        estimated_remaining = max(1000, self.token_budget - estimated_used)
        vars_["token_budget_remaining"] = estimated_remaining

        zjsn = get_test_project_root()
        if zjsn and not vars_.get("builder_context"):
            try:
                from alice_engine.core.context_builder import build_context
                builder_ctx = build_context(
                    module=self.module,
                    project_root=zjsn,
                    page=self.page,
                    task_description=self.state.goal,
                )
                vars_["builder_context"] = builder_ctx
                self._log(
                    f"  🔍 ContextBuilder: {builder_ctx.source_count} files, "
                    f"{len(builder_ctx.patterns)} patterns, "
                    f"memory={'yes' if builder_ctx.memory_hints else 'no'}"
                )
            except Exception as e:
                self._log(f"[warn] context discovery skipped: {e}")

        if extra:
            vars_.update(extra)
        return vars_

    # ── Perceive ────────────────────────────────────────────────────

    def perceive(self, skill_id: str) -> dict:
        """感知当前环境——为即将执行的 Skill 收集上下文。"""
        info = {
            "skill_id": skill_id,
            "existing_files": [],
            "skip_candidate": False,
        }

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

    # ── Act ─────────────────────────────────────────────────────────

    def act(self, skill_id: str, user_input: str) -> LLMResponse:
        """执行一个 Skill——调用 LLM + 窗口管理 + 产出保存。"""
        if skill_id == "automation/code-consistency-checker:review":
            return self._act_llm_consistency_review()
        if skill_id == "automation/code-consistency-checker":
            return self._act_mechanical_consistency_check()

        context_vars = self.build_context_vars()

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

        if self._reliable_provider:
            response = self._run_skill(
                skill_id=skill_id, user_input=user_input,
                provider=self.provider, context_vars=context_vars,
                reliable_provider=self._reliable_provider,
                agent_name=self.agent_name,
            )
        else:
            response = self._run_skill(
                skill_id=skill_id, user_input=user_input,
                provider=self.provider, context_vars=context_vars,
                agent_name=self.agent_name,
            )

        if self._window_monitor and response.usage:
            self._window_monitor.add_usage(
                response.usage.get("input", 0),
                response.usage.get("output", 0),
            )

        self._session_messages.append({"role": "user", "content": user_input[:500]})
        self._session_messages.append({"role": "assistant", "content": response.content[:500]})

        if response.finish_reason != "error" and response.content:
            save_skill_output(
                skill_id, response.content, self.module, self.page,
                self.agent_name, logger=self._log,
            )

        return response

    # ── 机械化 / LLM 审查 ──────────────────────────────────────────

    def _act_mechanical_consistency_check(self) -> LLMResponse:
        return run_mechanical_consistency_check(
            self.module, self.page, CODE_REDLINE_CHECKS, logger=self._log)

    def _act_llm_consistency_review(self) -> LLMResponse:
        return run_llm_consistency_review(
            self.module, self.page, self.provider,
            build_context_vars=self.build_context_vars,
            run_skill_fn=self._run_skill)

    # ── Artifact 持久化 ────────────────────────────────────────────

    def persist_skill_artifact(self, skill_id: str, content: str) -> str:
        """立即将 Skill 产出写入 artifact 文件。"""
        if not content or not self.module:
            return ""
        try:
            rules = _ALL_ARTIFACT_RULES.get(skill_id, [])
            filepath = None
            for rule in rules:
                if rule.required:
                    filepath = self._resolve_path(rule.glob_pattern)
                    break

            if filepath is None:
                skill_name = skill_id.split("/")[-1] if "/" in skill_id else skill_id
                filename = skill_name.upper().replace("-", "_") + ".md"
                if self.agent_name in self._dev_agent_map:
                    parent_dir = _GOVERNANCE / "context" / "projects" / "dev-platform"
                else:
                    parent_dir = _CONTEXT_MODULES / self.module
                parent_dir.mkdir(parents=True, exist_ok=True)
                filepath = parent_dir / filename

            filepath.parent.mkdir(parents=True, exist_ok=True)

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

    # ── Continuation ────────────────────────────────────────────────

    def do_continuation(self, continuation_count: int) -> int:
        """执行上下文窗口 continuation。返回新的 continuation_count。"""
        continuation_count += 1
        self._log(f"[CONTINUE] Session continuation #{continuation_count}...")

        compactor = SessionCompactor()
        summary = compactor.compact(
            self._session_messages,
            agent_memory=self.state.memory,
        )

        continuation_msg = build_continuation_prompt(summary, continuation_count)

        self._session_messages.clear()
        self._session_messages.append({"role": "user", "content": continuation_msg})
        if self._window_monitor:
            self._window_monitor = ContextWindowMonitor(
                model=self._window_monitor.model,
                model_limit=self._window_monitor.limit,
            )
            self._window_monitor.add_message("user", continuation_msg[:3000])

        self._focused_context = continuation_msg
        self._log(f"  摘要: {len(summary)} chars | 窗口已重置")
        return continuation_count

    # ── Finalize ────────────────────────────────────────────────────

    def finalize_session(self, state: AgentState, skills: list, session_finalized: bool) -> bool:
        """会话清理。返回新的 session_finalized 状态。"""
        if session_finalized:
            return True

        completed = len(state.completed_skills)
        failed = len(state.failed_skills)
        total_steps = state.step
        self._log(
            f"🏁 Agent 结束: {completed} 完成 / {failed} 失败 / "
            f"{total_steps} 步 | {state.termination_reason}"
        )

        self._emit_obs(EventType.AGENT_COMPLETE, {
            "completed": completed, "failed": failed, "steps": total_steps,
            "termination": state.termination_reason,
        })

        return True


def _default_run_skill(skill_id, user_input, provider=None, context_vars=None, model=None, **kwargs):
    """默认 run_skill 实现（与 executor.py 保持一致）。"""
    from alice_engine.providers import get_provider as _get_provider
    from alice_engine.core.skill_loader import SkillLoader
    from alice_engine.core.skill_executor_impl import SkillExecutorImpl

    loader = SkillLoader(governance_path=_GOVERNANCE)
    provider_kwargs = {"model": model} if model else {}
    prov = _get_provider(provider or "mock", **provider_kwargs)
    executor = SkillExecutorImpl(skill_loader=loader, provider=prov)
    return executor.execute(skill_id, user_input, context_vars=context_vars)

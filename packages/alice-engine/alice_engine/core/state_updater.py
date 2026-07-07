"""State Updater — Observation 构建 + 状态变更。

从 executor.py (AgentLoop) 拆出。负责:
  - observe(): 验证 Skill 产出质量，构建 Observation
  - update(): 委托 state_machine.update_agent_state()

与 executor_impl.py 不互相引用，只通过 AgentLoop 编排。
"""

import logging
import os
import re
from pathlib import Path
from typing import Optional

from alice_engine.providers.base import LLMResponse
from alice_engine.core.task import (
    Observation, AgentState, _ALL_ARTIFACT_RULES,
)
from alice_engine.core.path_utils import resolve_path

logger = logging.getLogger(__name__)


def _log_fn(msg: str) -> None:
    """默认日志函数。"""
    logger.info(msg)


class ObservationBuilder:
    """构建 Observation 的逻辑，从 AgentLoop 迁出。

    不持有 AgentLoop 引用——所有依赖通过构造函数注入。
    与 executor_impl.py 不互相引用。
    """

    def __init__(
        self,
        state: AgentState,
        module: str,
        page: str,
        agent_name: str,
        dev_agent_map: Optional[set] = None,
        log_fn=None,
    ):
        self.state = state
        self.module = module
        self.page = page
        self.agent_name = agent_name
        self._dev_agent_map = dev_agent_map or set()
        self._log = log_fn or _log_fn

    def _resolve_path(self, pattern: str) -> Path:
        return resolve_path(pattern, self.module, self.page, self.agent_name, self._dev_agent_map)

    def observe(self, skill_id: str, response: LLMResponse) -> Observation:
        """验证 Skill 产出质量。

        检查维度:
          - 文件存在性（必需产出文件是否生成）
          - 代码红线（grep 8 条规则）
          - LLM 响应是否异常
          - 运行时安全检查（敏感信息泄露、高风险操作）
        """
        obs = Observation(
            skill_id=skill_id,
            raw_output_preview=response.content[:500] if response.content else "",
            raw_output_full=response.content or "",
            token_usage=response.usage,
        )

        # 安全检查 — v3.1: safety_auditor 未在 alice_engine 中实现，跳过

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
                has_critical = any(
                    kw in response.content for kw in ["严重", "critical", "CRITICAL", "阻塞"]
                )
                obs.status = "fail" if has_critical else "pass"
                obs.suggestion = "continue"
                obs.summary = f"[LLM Review] {'发现严重问题' if has_critical else '无严重问题'}"
                obs.quality_issues = [
                    line.strip("- ").strip()
                    for line in response.content.split("\n")
                    if "严重" in line or "critical" in line.lower()
                ][:10]
                obs.artifacts_found = [
                    f"artifacts/code-review/{self.module}/{self.page}/consistency-review-llm.md"
                ]
            elif "PASS:" in response.content or "✅" in response.content:
                obs.status = "pass"
                obs.suggestion = "continue"
            else:
                obs.status = "fail"
                obs.suggestion = "continue"
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
            if response.content and len(response.content) > 50:
                obs.status = "pass"
                obs.suggestion = "continue"
                obs.summary = f"LLM 响应 {len(response.content)} 字符"
            else:
                obs.status = "partial"
                obs.suggestion = "retry"
                obs.summary = "LLM 响应过短"

        # 失败归因
        if obs.status in ("fail", "partial") and obs.raw_output_preview:
            obs.failure_category = "unknown"

        return obs

    def update(self, skill_id: str, observation: Observation) -> None:
        """委托给 state_machine.update_agent_state()。"""
        from alice_engine.core.state_machine import update_agent_state
        update_agent_state(
            self.state, skill_id, observation,
            agent_name=self.agent_name, module=self.module, logger=self._log,
        )

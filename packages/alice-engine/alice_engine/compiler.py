"""Governance Compiler — skills + SOP + validators → execution graph。

将行为定义编译为可执行的图结构。
Router 负责"找到什么"，Compiler 负责"怎么组合"。

用法:
    from alice_engine.compiler import GovernanceCompiler

    compiler = GovernanceCompiler(router)
    graph = compiler.compile()
    print(graph.phases)
    print(graph.validate())
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from pathlib import Path

from alice_engine.router import GovernanceRouter, ResolvedSkill, Source, Stability

logger = logging.getLogger(__name__)


# ═══════════════════════════════════════════════════════════
#  数据结构
# ═══════════════════════════════════════════════════════════

@dataclass
class PhaseBinding:
    """Phase → skills + agent 绑定。"""
    phase: str
    agent: str
    skills: list[ResolvedSkill] = field(default_factory=list)
    validators: list[str] = field(default_factory=list)

    @property
    def all_skills_found(self) -> bool:
        return all(s.found for s in self.skills)

    @property
    def missing_core(self) -> list[str]:
        return [s.skill_id for s in self.skills
                if not s.found and s.is_core_or_higher]

    @property
    def total_content_chars(self) -> int:
        return sum(len(s.content) for s in self.skills)


@dataclass
class ExecutionGraph:
    """编译后的执行图。"""
    phases: list[PhaseBinding] = field(default_factory=list)
    source: Source = Source.MISSING
    compile_errors: list[str] = field(default_factory=list)

    @property
    def ok(self) -> bool:
        return len(self.compile_errors) == 0 and all(
            p.all_skills_found or not p.missing_core for p in self.phases
        )

    @property
    def total_skills(self) -> int:
        return sum(len(p.skills) for p in self.phases)

    @property
    def total_phases(self) -> int:
        return len(self.phases)

    def phase(self, name: str) -> PhaseBinding | None:
        """按名称查找 phase。"""
        for p in self.phases:
            if p.phase == name:
                return p
        return None

    def summary(self) -> dict:
        """输出编译摘要。"""
        return {
            "phases": self.total_phases,
            "skills": self.total_skills,
            "ok": self.ok,
            "errors": self.compile_errors,
            "phase_details": [
                {
                    "phase": p.phase,
                    "agent": p.agent,
                    "skills": len(p.skills),
                    "all_found": p.all_skills_found,
                    "missing_core": p.missing_core,
                }
                for p in self.phases
            ],
        }


# ═══════════════════════════════════════════════════════════
#  SOP 定义（权威源: workflow/state.py）
# ═══════════════════════════════════════════════════════════

CANONICAL_PHASES = [
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

PHASE_AGENT_MAP = {
    "Project Init": "project-agent",
    "Requirement": "requirement-agent",
    "Test Design": "test-design-agent",
    "Automation": "automation-agent",
    "Execute & Debug": "execution-agent",
    "Bug Analysis": "bug-analysis-agent",
    "Data Sanitization": "execution-agent",
    "Report": "report-agent",
    "Knowledge": "knowledge-agent",
}

PHASE_VALIDATOR_MAP = {
    "Project Init": ["validate_module_context"],
    "Requirement": [],
    "Test Design": ["validate_page_bundle"],
    "Automation": [],
    "Execute & Debug": [],
    "Bug Analysis": [],
    "Data Sanitization": [],
    "Report": [],
    "Knowledge": [],
}


# ═══════════════════════════════════════════════════════════
#  Compiler 核心
# ═══════════════════════════════════════════════════════════

class GovernanceCompiler:
    """将 SOP + skills + validators 编译为执行图。

    用法:
        from alice_engine.router import GovernanceRouter
        from alice_engine.compiler import GovernanceCompiler

        router = GovernanceRouter()
        compiler = GovernanceCompiler(router)
        graph = compiler.compile()
    """

    def __init__(self, router: GovernanceRouter):
        self._router = router

    def compile(self) -> ExecutionGraph:
        """编译完整执行图。

        遍历 CANONICAL_PHASES，为每个 phase:
        1. 找到对应的 agent
        2. 通过 Router 解析 agent 的所有 skills
        3. 绑定 validators

        Returns:
            ExecutionGraph 包含所有 phase 的绑定结果。
        """
        graph = ExecutionGraph()

        for phase in CANONICAL_PHASES:
            agent = PHASE_AGENT_MAP.get(phase)
            if not agent:
                graph.compile_errors.append(f"No agent mapped for phase: {phase}")
                continue

            # 通过 Router 解析 agent 的所有 skills
            agent_result = self._router.resolve_agent_skills(agent)

            # 绑定 validators
            validators = PHASE_VALIDATOR_MAP.get(phase, [])

            binding = PhaseBinding(
                phase=phase,
                agent=agent,
                skills=agent_result.skills,
                validators=validators,
            )
            graph.phases.append(binding)

        # 确定整体来源
        for p in graph.phases:
            for s in p.skills:
                if s.found:
                    graph.source = s.source
                    break
            if graph.source != Source.MISSING:
                break

        logger.info(
            "Governance compiled: %d phases, %d skills, source=%s, errors=%d",
            graph.total_phases, graph.total_skills,
            graph.source.value, len(graph.compile_errors),
        )

        return graph

    def compile_phase(self, phase: str) -> PhaseBinding:
        """编译单个 phase。

        Args:
            phase: Phase 名称 (如 "Test Design")

        Returns:
            PhaseBinding 包含该 phase 的 skill 绑定。
        """
        agent = PHASE_AGENT_MAP.get(phase)
        if not agent:
            return PhaseBinding(
                phase=phase,
                agent="unknown",
                skills=[],
            )

        agent_result = self._router.resolve_agent_skills(agent)
        validators = PHASE_VALIDATOR_MAP.get(phase, [])

        return PhaseBinding(
            phase=phase,
            agent=agent,
            skills=agent_result.skills,
            validators=validators,
        )

    def validate_graph(self, graph: ExecutionGraph) -> dict:
        """校验编译后的图。

        检查:
        1. 每个 phase 的 core skills 是否都找到
        2. 每个 phase 的 agent 是否有至少 1 个 skill
        3. 总体 contract 完整性

        Returns:
            校验报告 dict。
        """
        issues = []

        for phase in graph.phases:
            if not phase.skills:
                issues.append({
                    "phase": phase.phase,
                    "agent": phase.agent,
                    "issue": "no skills bound",
                    "severity": "error",
                })
            elif phase.missing_core:
                issues.append({
                    "phase": phase.phase,
                    "agent": phase.agent,
                    "issue": f"missing core skills: {phase.missing_core}",
                    "severity": "error",
                })

        return {
            "ok": len(issues) == 0,
            "phases": graph.total_phases,
            "skills": graph.total_skills,
            "issues": issues,
        }

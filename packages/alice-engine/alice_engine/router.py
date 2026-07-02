"""Governance Router — AI runtime 的统一调度入口。

所有 skill 请求、agent 解析、contract 校验通过 Router 统一分发。
消除 capability fragmentation，固化 behavior resolution order。

用法:
    from alice_engine.router import GovernanceRouter

    router = GovernanceRouter()

    # 解析 skill
    result = router.resolve_skill("test-design/page-analysis")
    print(result.source)       # "alice-governance"
    print(result.content)      # skill prompt 内容
    print(result.stability)    # "core"

    # 解析 agent 的所有 skills
    results = router.resolve_agent_skills("automation-agent")

    # 校验全部 contract
    report = router.validate_all()
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path

logger = logging.getLogger(__name__)


# ═══════════════════════════════════════════════════════════
#  数据结构
# ═══════════════════════════════════════════════════════════

class Source(Enum):
    """行为包来源（按优先级排序）。"""
    EXTERNAL = "external"           # 用户显式指定的外部路径
    GOVERNANCE = "alice-governance"  # pip install alice-governance
    SUITE = "alice-governance-suite" # pip install alice-governance-suite (dev skills)
    DEFAULT = "governance_default"   # SDK 内置骨架
    MISSING = "missing"              # 未找到


class Stability(Enum):
    """Contract stability 级别。"""
    SYSTEM = "system"          # SDK runtime 必需，缺失 → crash
    CORE = "core"              # 业务必须，缺失 → block
    EXTENDED = "extended"      # 增强能力，缺失 → warn
    EXPERIMENTAL = "experimental"  # 实验性，缺失 → ignore


@dataclass
class ResolvedSkill:
    """Skill 解析结果。"""
    skill_id: str
    source: Source
    content: str = ""
    stability: Stability = Stability.EXTENDED
    contract: dict | None = None
    file_path: Path | None = None
    fallback_chain: list[Source] = field(default_factory=list)

    @property
    def found(self) -> bool:
        return self.source != Source.MISSING

    @property
    def is_core_or_higher(self) -> bool:
        return self.stability in (Stability.SYSTEM, Stability.CORE)


@dataclass
class ResolvedAgent:
    """Agent 解析结果。"""
    agent_name: str
    skills: list[ResolvedSkill] = field(default_factory=list)
    source: Source = Source.MISSING

    @property
    def all_found(self) -> bool:
        return all(s.found for s in self.skills)

    @property
    def missing_core(self) -> list[str]:
        return [s.skill_id for s in self.skills
                if not s.found and s.is_core_or_higher]


@dataclass
class ValidationReport:
    """Contract 校验报告。"""
    total_skills: int = 0
    found: int = 0
    missing: int = 0
    missing_core: list[str] = field(default_factory=list)
    missing_extended: list[str] = field(default_factory=list)
    issues: list[dict] = field(default_factory=list)

    @property
    def ok(self) -> bool:
        return len(self.missing_core) == 0


# ═══════════════════════════════════════════════════════════
#  Router 核心
# ═══════════════════════════════════════════════════════════

class GovernanceRouter:
    """AI runtime 统一调度入口。

    解析优先级:
      1. external_pack（用户显式指定）
      2. alice-governance（pip install alice-governance）
      3. alice-governance-suite（dev skills）
      4. governance_default（SDK 内置骨架）

    用法:
        router = GovernanceRouter()
        result = router.resolve_skill("test-design/page-analysis")
    """

    def __init__(
        self,
        external_pack: str | Path | None = None,
        auto_discover: bool = True,
    ):
        """
        Args:
            external_pack: 外部行为包路径（最高优先级）。
            auto_discover: 是否自动发现已安装的 governance 包。
        """
        self._external_pack = Path(external_pack) if external_pack else None
        self._auto_discover = auto_discover

        # 惰性初始化各层
        self._governance_loader = None
        self._suite_loader = None
        self._default_loader = None
        self._agent_defs = None

        if auto_discover:
            self._init_layers()

    def _init_layers(self):
        """初始化各层 SkillLoader。"""
        from alice_engine.core.skill_loader import SkillLoader

        # 层 1: alice-governance
        gov_path = self._try_import("alice_governance", "get_pack_path")
        if gov_path:
            self._governance_loader = SkillLoader(governance_path=gov_path)
            logger.info("Router: alice-governance loaded from %s", gov_path)

        # 层 2: alice-governance (dev skills + validators)
        dev_path = self._try_import("alice_governance", "get_skills_dev_path")
        if dev_path:
            self._suite_loader = SkillLoader(governance_path=dev_path.parent)
            logger.info("Router: alice-governance dev skills loaded from %s", dev_path)

        # 层 3: governance_default (SDK fallback)
        from alice_engine.behavior import get_default_pack_path
        default_path = get_default_pack_path()
        if default_path.exists():
            self._default_loader = SkillLoader(governance_path=default_path)
            logger.info("Router: governance_default loaded from %s", default_path)

    def _try_import(self, module: str, func: str) -> Path | None:
        """尝试 import 并获取路径。"""
        try:
            import importlib
            mod = importlib.import_module(module)
            path = getattr(mod, func)()
            return Path(path) if path else None
        except (ImportError, AttributeError):
            return None

    # ── Skill 解析 ──────────────────────────────────────────

    def resolve_skill(self, skill_id: str) -> ResolvedSkill:
        """解析单个 skill。

        按优先级遍历各层，返回第一个匹配的结果。

        Args:
            skill_id: Skill ID (如 "test-design/page-analysis")

        Returns:
            ResolvedSkill 包含来源、内容、stability、contract。
        """
        chain = []

        # 优先级 1: 外部 pack
        if self._external_pack:
            result = self._try_load(skill_id, self._external_pack, Source.EXTERNAL)
            if result:
                result.fallback_chain = chain + [Source.EXTERNAL]
                return result
            chain.append(Source.EXTERNAL)

        # 优先级 2: alice-governance
        if self._governance_loader:
            result = self._try_load_from_loader(skill_id, self._governance_loader, Source.GOVERNANCE)
            if result:
                result.fallback_chain = chain + [Source.GOVERNANCE]
                return result
            chain.append(Source.GOVERNANCE)

        # 优先级 3: alice-governance-suite (dev skills)
        if self._suite_loader:
            result = self._try_load_from_loader(skill_id, self._suite_loader, Source.SUITE)
            if result:
                result.fallback_chain = chain + [Source.SUITE]
                return result
            chain.append(Source.SUITE)

        # 优先级 4: governance_default
        if self._default_loader:
            result = self._try_load_from_loader(skill_id, self._default_loader, Source.DEFAULT)
            if result:
                result.fallback_chain = chain + [Source.DEFAULT]
                return result
            chain.append(Source.DEFAULT)

        # 未找到
        return ResolvedSkill(
            skill_id=skill_id,
            source=Source.MISSING,
            fallback_chain=chain,
        )

    def _try_load(self, skill_id: str, pack_path: Path, source: Source) -> ResolvedSkill | None:
        """从指定路径尝试加载 skill。"""
        from alice_engine.core.skill_loader import SkillLoader
        loader = SkillLoader(governance_path=pack_path)
        return self._try_load_from_loader(skill_id, loader, source)

    def _try_load_from_loader(self, skill_id: str, loader, source: Source) -> ResolvedSkill | None:
        """从已有的 SkillLoader 尝试加载。"""
        try:
            content = loader.load(skill_id)
            contract = loader.get_contract(skill_id)
            stability_str = loader.get_stability(skill_id)
            try:
                stability = Stability(stability_str)
            except ValueError:
                stability = Stability.EXTENDED

            return ResolvedSkill(
                skill_id=skill_id,
                source=source,
                content=content,
                stability=stability,
                contract=contract,
            )
        except (FileNotFoundError, Exception):
            return None

    # ── Agent 解析 ──────────────────────────────────────────

    def resolve_agent_skills(self, agent_name: str) -> ResolvedAgent:
        """解析 agent 的所有 skills。

        Args:
            agent_name: Agent 名称 (如 "automation-agent")

        Returns:
            ResolvedAgent 包含所有 skill 的解析结果。
        """
        # 获取 agent 定义
        agent_defs = self._get_agent_definitions()
        skill_ids = agent_defs.get(agent_name, [])

        if not skill_ids:
            return ResolvedAgent(agent_name=agent_name, source=Source.MISSING)

        # 解析每个 skill
        skills = [self.resolve_skill(sid) for sid in skill_ids]

        # 确定 agent 整体来源（取第一个找到的 skill 的来源）
        source = Source.MISSING
        for s in skills:
            if s.found:
                source = s.source
                break

        return ResolvedAgent(
            agent_name=agent_name,
            skills=skills,
            source=source,
        )

    def _get_agent_definitions(self) -> dict[str, list[str]]:
        """获取 agent → skills 映射。"""
        # 尝试从 alice-governance 加载
        if self._governance_loader:
            defs = self._load_agent_yaml(self._governance_loader.governance)
            if defs:
                return defs

        # fallback: SDK 内置
        from alice_engine.core.agent_definitions import FALLBACK_AGENT_SKILL_MAP
        return FALLBACK_AGENT_SKILL_MAP

    def _load_agent_yaml(self, governance_path: Path) -> dict[str, list[str]] | None:
        """从 agent-definitions.yaml 加载映射。"""
        import yaml
        yaml_path = governance_path / "agents" / "agent-definitions.yaml"
        if not yaml_path.exists():
            return None

        try:
            with open(yaml_path, "r", encoding="utf-8") as f:
                data = yaml.safe_load(f)

            result = {}
            agents_data = data.get("agents", {})
            if isinstance(agents_data, dict):
                for key, agent in agents_data.items():
                    # key 是 agent 标识（如 "automation-agent"）
                    skills = agent.get("skills", [])
                    if key and skills:
                        result[key] = skills
            return result if result else None
        except Exception:
            return None

    # ── Contract 校验 ──────────────────────────────────────

    def validate_all(self) -> ValidationReport:
        """校验所有已注册 skill 的 contract。

        Returns:
            ValidationReport 包含缺失 core skill 清单。
        """
        report = ValidationReport()

        # 收集所有已注册的 skill
        all_skills = set()
        for loader in [self._governance_loader, self._default_loader]:
            if loader:
                for s in loader.list_skills():
                    sid = s.get("id", "")
                    if sid and s.get("status") != "deprecated":
                        all_skills.add(sid)

        report.total_skills = len(all_skills)

        # 逐个解析
        for skill_id in sorted(all_skills):
            result = self.resolve_skill(skill_id)
            if result.found:
                report.found += 1
            else:
                report.missing += 1
                if result.stability in (Stability.SYSTEM, Stability.CORE):
                    report.missing_core.append(skill_id)
                else:
                    report.missing_extended.append(skill_id)
                report.issues.append({
                    "skill_id": skill_id,
                    "stability": result.stability.value,
                    "issue": "not found in any layer",
                    "fallback_chain": [s.value for s in result.fallback_chain],
                })

        return report

    # ── 诊断 ──────────────────────────────────────────────

    def diagnose(self) -> dict:
        """诊断当前 Router 状态。"""
        return {
            "external_pack": str(self._external_pack) if self._external_pack else None,
            "governance_available": self._governance_loader is not None,
            "suite_available": self._suite_loader is not None,
            "default_available": self._default_loader is not None,
            "governance_path": str(self._governance_loader.governance) if self._governance_loader else None,
            "default_path": str(self._default_loader.governance) if self._default_loader else None,
        }

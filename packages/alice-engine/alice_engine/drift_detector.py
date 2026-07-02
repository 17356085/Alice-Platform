"""Drift Detector — 检测 governance vs suite vs default 之间的行为漂移。

当同一个 skill 在不同层有不同实现时，会产生"行为漂移"。
Drift Detector 检测并报告这些差异。

用法:
    from alice_engine.drift_detector import DriftDetector

    detector = DriftDetector(router)
    report = detector.detect()
    print(report.drifts)
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from pathlib import Path

from alice_engine.router import GovernanceRouter, Source

logger = logging.getLogger(__name__)


# ═══════════════════════════════════════════════════════════
#  数据结构
# ═══════════════════════════════════════════════════════════

@dataclass
class SkillDrift:
    """单个 skill 的漂移报告。"""
    skill_id: str
    governance_chars: int = 0
    default_chars: int = 0
    ratio: float = 0.0
    governance_stability: str = ""
    default_stability: str = ""
    stability_match: bool = True

    @property
    def has_drift(self) -> bool:
        """是否存在显著漂移（内容差异 > 3x）。"""
        return self.ratio > 3.0 or not self.stability_match

    @property
    def severity(self) -> str:
        if not self.stability_match:
            return "critical"
        if self.ratio > 10:
            return "high"
        if self.ratio > 3:
            return "medium"
        return "low"


@dataclass
class DriftReport:
    """漂移检测报告。"""
    total_skills: int = 0
    drifts: list[SkillDrift] = field(default_factory=list)
    missing_in_governance: list[str] = field(default_factory=list)
    missing_in_default: list[str] = field(default_factory=list)

    @property
    def has_drift(self) -> bool:
        return len(self.drifts) > 0

    @property
    def critical_drifts(self) -> list[SkillDrift]:
        return [d for d in self.drifts if d.severity == "critical"]

    @property
    def high_drifts(self) -> list[SkillDrift]:
        return [d for d in self.drifts if d.severity == "high"]

    def summary(self) -> dict:
        return {
            "total_skills": self.total_skills,
            "drifts": len(self.drifts),
            "critical": len(self.critical_drifts),
            "high": len(self.high_drifts),
            "missing_in_governance": len(self.missing_in_governance),
            "missing_in_default": len(self.missing_in_default),
        }


# ═══════════════════════════════════════════════════════════
#  Detector 核心
# ═══════════════════════════════════════════════════════════

class DriftDetector:
    """检测 governance 层之间的行为漂移。

    比较:
      - alice-governance（完整版）
      - governance_default（骨架版）

    检测:
      - 内容深度差异（ratio > 3x）
      - stability 级别不一致
      - skill 缺失

    用法:
        router = GovernanceRouter()
        detector = DriftDetector(router)
        report = detector.detect()
    """

    def __init__(self, router: GovernanceRouter):
        self._router = router

    def detect(self) -> DriftReport:
        """执行漂移检测。

        Returns:
            DriftReport 包含所有漂移详情。
        """
        report = DriftReport()

        # 收集各层的 skill 列表
        gov_skills = self._get_layer_skills(Source.GOVERNANCE)
        default_skills = self._get_layer_skills(Source.DEFAULT)

        # 合并所有 skill ID
        all_ids = set(gov_skills.keys()) | set(default_skills.keys())
        report.total_skills = len(all_ids)

        for skill_id in sorted(all_ids):
            gov_content = gov_skills.get(skill_id, "")
            default_content = default_skills.get(skill_id, "")

            # 缺失检测
            if not gov_content:
                report.missing_in_governance.append(skill_id)
                continue
            if not default_content:
                report.missing_in_default.append(skill_id)
                continue

            # 内容漂移检测
            gov_len = len(gov_content)
            default_len = len(default_content)
            ratio = gov_len / default_len if default_len > 0 else float('inf')

            # stability 检测
            gov_stability = self._get_stability(skill_id, Source.GOVERNANCE)
            default_stability = self._get_stability(skill_id, Source.DEFAULT)
            stability_match = gov_stability == default_stability

            drift = SkillDrift(
                skill_id=skill_id,
                governance_chars=gov_len,
                default_chars=default_len,
                ratio=ratio,
                governance_stability=gov_stability,
                default_stability=default_stability,
                stability_match=stability_match,
            )

            if drift.has_drift:
                report.drifts.append(drift)

        logger.info(
            "Drift detection: %d skills, %d drifts, %d critical",
            report.total_skills, len(report.drifts), len(report.critical_drifts),
        )

        return report

    @staticmethod
    def _normalize_id(skill_id: str) -> str:
        """标准化 skill ID（去除 category/ 前缀）。

        governance_default 用 "project/project-context-manager"
        governance 用 "project-context-manager"
        统一为后者用于比较。
        """
        return skill_id.split("/")[-1]

    def _get_layer_skills(self, source: Source) -> dict[str, str]:
        """获取指定层的所有 skill 内容（key 为标准化 ID）。"""
        result = {}

        if source == Source.GOVERNANCE:
            loader = self._router._governance_loader
        elif source == Source.DEFAULT:
            loader = self._router._default_loader
        else:
            return result

        if not loader:
            return result

        for s in loader.list_skills():
            sid = s.get("id", "")
            if not sid or s.get("status") == "deprecated":
                continue
            try:
                content = loader.load(sid)
                normalized = self._normalize_id(sid)
                result[normalized] = content
            except Exception:
                pass

        return result

    def _get_stability(self, skill_id: str, source: Source) -> str:
        """获取指定层的 skill stability。"""
        if source == Source.GOVERNANCE:
            loader = self._router._governance_loader
        elif source == Source.DEFAULT:
            loader = self._router._default_loader
        else:
            return "unknown"

        if not loader:
            return "unknown"

        return loader.get_stability(skill_id)

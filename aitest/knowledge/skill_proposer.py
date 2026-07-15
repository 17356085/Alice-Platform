"""Skill Proposer — 技能蒸馏管道。

从 KnowledgeExtractor 提取的高频修复模式中自动蒸馏出新 Skill，
写入 governance/skills/ 并注册到 skill-registry.yaml。

触发条件:
  - 同类 fix 模式出现 ≥3 次（跨不同 run）
  - 修复策略的 confidence ≥ 0.7

产物:
  - governance/skills/auto/{skill_id}.md  (experimental 稳定性)
  - skill-registry.yaml 追加条目

用法:
    from aitest.knowledge.skill_proposer import SkillProposer

    proposer = SkillProposer()
    proposed = proposer.propose_from_patterns(extracted_patterns)
    # proposed = [{"skill_id": "auto-fix-stale-locator-abc123", "file": "...", ...}]

设计决策:
  - 不修改 KnowledgeExtractor 内部逻辑，通过组合模式接入
  - 生成的 Skill 全部标记为 experimental，需人工 promote 到 extended/core
  - skill_id 带 auto- 前缀 + 内容 hash，避免与人工 Skill 冲突
"""

from __future__ import annotations

import hashlib
import logging
import re
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Optional

from aitest.runtime.paths import get_workstudy

_log = logging.getLogger(__name__)

WORKSTUDY = get_workstudy()
# Skill 文件写入目录 (auto-generated skills)
AUTO_SKILLS_DIR = WORKSTUDY / "governance" / "skills" / "auto"
# Registry 文件路径
SKILL_REGISTRY = WORKSTUDY / "governance" / "skills" / "skill-registry.yaml"

# 触发阈值: 同类 fix 模式出现次数
MIN_FIX_COUNT = 3
# 最低置信度
MIN_CONFIDENCE = 0.7


@dataclass
class ProposedSkill:
    """蒸馏出的候选技能。"""
    skill_id: str
    category: str = "auto-generated"
    title: str = ""
    description: str = ""
    trigger_patterns: list[str] = field(default_factory=list)
    fix_strategies: list[str] = field(default_factory=list)
    source_modules: list[str] = field(default_factory=list)
    confidence: float = 0.0
    source_pattern_count: int = 0
    markdown: str = ""
    file_path: str = ""
    registry_entry: dict = field(default_factory=dict)


class SkillProposer:
    """技能蒸馏器 — 从高频修复模式中自动蒸馏出新 Skill。

    工作流:
      1. 接收 KnowledgeExtractor.extract_from_execution() 的输出
      2. 按 failure_type + module 分组，统计同类 fix 出现次数
      3. 超过阈值的 → 生成 Skill Markdown + 注册到 registry

    不直接修改 KnowledgeExtractor，而是作为后处理管道。
    """

    def __init__(
        self,
        min_fix_count: int = MIN_FIX_COUNT,
        min_confidence: float = MIN_CONFIDENCE,
        auto_register: bool = True,
    ):
        self.min_fix_count = min_fix_count
        self.min_confidence = min_confidence
        self.auto_register = auto_register

    def propose_from_patterns(
        self, patterns: list, run_id: str = ""
    ) -> list[ProposedSkill]:
        """从提取的模式中蒸馏候选技能。

        Args:
            patterns: KnowledgeExtractor.extract_from_execution() 的输出
                      (list of ExtractedPattern)
            run_id: 当前运行 ID，用于日志

        Returns:
            蒸馏出的候选技能列表（已写入文件 + 注册到 registry）
        """
        if not patterns:
            return []

        # Step 1: 分组 — 按 (failure_type, module) 聚集 fix 模式
        fix_groups = self._group_fix_patterns(patterns)

        # Step 2: 过滤 — 超过阈值的组才蒸馏
        candidates = []
        for group_key, group in fix_groups.items():
            if len(group) >= self.min_fix_count:
                avg_conf = sum(p.confidence for p in group) / len(group)
                if avg_conf >= self.min_confidence:
                    candidate = self._distill_skill(group_key, group)
                    candidates.append(candidate)

        if not candidates:
            _log.debug(f"[SkillProposer] No patterns meet threshold (run={run_id})")
            return []

        # Step 3: 写入文件 + 注册
        proposed = []
        for c in candidates:
            if self.auto_register:
                self._write_skill_file(c)
                self._register_to_yaml(c)
            proposed.append(c)
            _log.info(
                f"[SkillProposer] Proposed skill: {c.skill_id} "
                f"(from {c.source_pattern_count} patterns, "
                f"modules={c.source_modules})"
            )

        return proposed

    # ── Grouping ──────────────────────────────────────────────────

    def _group_fix_patterns(
        self, patterns: list
    ) -> dict[str, list]:
        """按 (failure_type, module) 分组 fix 模式。"""
        from aitest.knowledge.knowledge_extractor import ExtractedPattern

        groups: dict[str, list] = {}
        for p in patterns:
            if not isinstance(p, ExtractedPattern):
                continue
            # 只关注 fix 和 failure 模式
            if p.pattern_type not in ("fix", "failure"):
                continue
            # 从 summary 中提取 failure_type（格式: "Fix for StaleLocator: ..."）
            failure_type = self._extract_failure_type(p.summary)
            group_key = f"{failure_type}:{p.module}"
            groups.setdefault(group_key, []).append(p)

        return groups

    @staticmethod
    def _extract_failure_type(summary: str) -> str:
        """从 summary 中提取失败类型。"""
        # "Fix for StaleLocator: ..." → "StaleLocator"
        # "[StaleLocator] ..." → "StaleLocator"
        m = re.match(r"(?:Fix for |\[)(\w+)", summary)
        return m.group(1) if m else "Unknown"

    # ── Distillation ──────────────────────────────────────────────

    def _distill_skill(self, group_key: str, patterns: list) -> ProposedSkill:
        """从一组修复模式中蒸馏出一个候选技能。"""
        failure_type, module = group_key.split(":", 1)

        # 聚合信息
        fix_strategies = []
        trigger_patterns = []
        source_modules = set()
        for p in patterns:
            if p.pattern_type == "fix" and p.detail:
                fix_strategies.append(p.detail[:500])
            trigger_patterns.append(p.summary[:200])
            source_modules.add(p.module)
            source_modules.update(p.cross_module_applicable)

        # 去重
        fix_strategies = list(dict.fromkeys(fix_strategies))[:5]
        trigger_patterns = list(dict.fromkeys(trigger_patterns))[:10]

        # 生成 skill_id（内容 hash 避免冲突）
        content_hash = hashlib.md5(
            f"{failure_type}:{module}:{len(patterns)}".encode()
        ).hexdigest()[:8]
        skill_id = f"auto-fix-{failure_type.lower()}-{content_hash}"

        avg_conf = sum(p.confidence for p in patterns) / len(patterns)

        # 生成 Markdown
        markdown = self._render_markdown(
            skill_id=skill_id,
            failure_type=failure_type,
            module=module,
            trigger_patterns=trigger_patterns,
            fix_strategies=fix_strategies,
            source_modules=sorted(source_modules),
            pattern_count=len(patterns),
            avg_confidence=avg_conf,
        )

        # 生成 registry 条目
        registry_entry = self._build_registry_entry(
            skill_id=skill_id,
            markdown=markdown,
            source_modules=sorted(source_modules),
        )

        return ProposedSkill(
            skill_id=skill_id,
            title=f"Auto-fix: {failure_type} ({module})",
            description=f"自动蒸馏的 {failure_type} 修复策略，来源 {len(patterns)} 条修复记录",
            trigger_patterns=trigger_patterns,
            fix_strategies=fix_strategies,
            source_modules=sorted(source_modules),
            confidence=round(avg_conf, 3),
            source_pattern_count=len(patterns),
            markdown=markdown,
            registry_entry=registry_entry,
        )

    # ── Markdown Rendering ────────────────────────────────────────

    def _render_markdown(
        self,
        skill_id: str,
        failure_type: str,
        module: str,
        trigger_patterns: list[str],
        fix_strategies: list[str],
        source_modules: list[str],
        pattern_count: int,
        avg_confidence: float,
    ) -> str:
        """渲染 Skill Markdown 文件内容。"""
        now = datetime.now().strftime("%Y-%m-%d")

        triggers_md = "\n".join(f"- {t}" for t in trigger_patterns)
        fixes_md = "\n".join(f"{i+1}. {f}" for i, f in enumerate(fix_strategies))
        modules_md = ", ".join(source_modules)

        return f"""# Skill: {skill_id}

## 目标
自动修复 **{failure_type}** 类型的测试失败。
由 SkillProposer 从 {pattern_count} 条修复记录中蒸馏（置信度: {avg_confidence:.2f}）。

## 触发条件

当检测到以下模式时自动应用:

{triggers_md}

## 输入

| 项目 | 说明 |
|------|------|
| 失败类型 | `{failure_type}` |
| 来源模块 | {modules_md} |
| 来源模式数 | {pattern_count} |

## 输出

修复后的测试代码 / 定位器 / 断言。

## 修复策略

{fixes_md}

## 规则

1. **自动蒸馏**：本 Skill 由 SkillProposer 自动生成，标记为 experimental
2. **人工审核**：使用前需人工确认修复策略的正确性
3. **晋升路径**：验证 ≥3 次后可 promote 到 extended 稳定性级别
4. **回滚**：如修复策略失效，删除本文件并从 registry 中移除

## 元信息

| 项目 | 值 |
|------|-----|
| 自动生成日期 | {now} |
| 蒸馏来源 | KnowledgeExtractor → SkillProposer |
| 稳定性 | experimental |
| 风险等级 | medium |
"""

    # ── Registry ──────────────────────────────────────────────────

    def _build_registry_entry(
        self, skill_id: str, markdown: str, source_modules: list[str]
    ) -> dict:
        """构建 skill-registry.yaml 条目。"""
        now = datetime.now().strftime("%Y-%m-%d")
        return {
            "id": skill_id,
            "category": "auto-generated",
            "status": "experimental",
            "file": f"skills/auto/{skill_id}.md",
            "current_version": "0.1-exp",
            "versions": [
                {
                    "version": "0.1-exp",
                    "file": f"skills/auto/{skill_id}.md",
                    "released": now,
                    "changelog": f"自动蒸馏 — 来源 {len(source_modules)} 个模块",
                    "status": "experimental",
                }
            ],
            "note": "由 SkillProposer 自动蒸馏生成，需人工审核后使用",
            "risk_level": "medium",
            "needs_confirm": True,
            "contract": {
                "input": ["失败用例", "错误日志"],
                "output": ["修复代码"],
                "stability": "experimental",
            },
        }

    # ── File I/O ──────────────────────────────────────────────────

    def _write_skill_file(self, skill: ProposedSkill) -> str:
        """将 Skill Markdown 写入文件系统。"""
        AUTO_SKILLS_DIR.mkdir(parents=True, exist_ok=True)
        file_path = AUTO_SKILLS_DIR / f"{skill.skill_id}.md"
        file_path.write_text(skill.markdown, encoding="utf-8")
        skill.file_path = str(file_path)
        _log.debug(f"[SkillProposer] Wrote skill file: {file_path}")
        return str(file_path)

    def _register_to_yaml(self, skill: ProposedSkill) -> bool:
        """将条目追加到 skill-registry.yaml。

        使用安全的追加方式：读取现有 YAML → 检查去重 → 追加 → 写回。
        """
        try:
            import yaml
        except ImportError:
            _log.warning("[SkillProposer] PyYAML not installed, skipping registry update")
            return False

        if not SKILL_REGISTRY.exists():
            _log.warning(f"[SkillProposer] Registry not found: {SKILL_REGISTRY}")
            return False

        try:
            with open(SKILL_REGISTRY, "r", encoding="utf-8") as f:
                registry = yaml.safe_load(f) or {}

            skills_list = registry.get("skills", [])

            # 去重检查
            existing_ids = {s.get("id") for s in skills_list}
            if skill.skill_id in existing_ids:
                _log.debug(f"[SkillProposer] Skill already registered: {skill.skill_id}")
                return True

            # 追加
            skills_list.append(skill.registry_entry)
            registry["skills"] = skills_list

            # 写回
            with open(SKILL_REGISTRY, "w", encoding="utf-8") as f:
                yaml.dump(
                    registry,
                    f,
                    default_flow_style=False,
                    allow_unicode=True,
                    sort_keys=False,
                )

            _log.info(f"[SkillProposer] Registered to registry: {skill.skill_id}")
            return True

        except Exception as e:
            _log.warning(f"[SkillProposer] Failed to register {skill.skill_id}: {e}")
            return False


# ── Convenience ───────────────────────────────────────────────────


def propose_skills(
    patterns: list,
    run_id: str = "",
    min_fix_count: int = MIN_FIX_COUNT,
) -> list[dict]:
    """便捷函数 — 从提取的模式中蒸馏技能。

    返回简化的结果字典列表（用于日志/报告）。
    """
    proposer = SkillProposer(min_fix_count=min_fix_count)
    proposed = proposer.propose_from_patterns(patterns, run_id=run_id)
    return [
        {
            "skill_id": p.skill_id,
            "title": p.title,
            "confidence": p.confidence,
            "source_patterns": p.source_pattern_count,
            "modules": p.source_modules,
            "file": p.file_path,
        }
        for p in proposed
    ]

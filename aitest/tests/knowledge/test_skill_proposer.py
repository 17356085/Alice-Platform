"""Tests for knowledge/skill_proposer.py — SkillProposer, ProposedSkill.

Tests: 分组逻辑、阈值过滤、Markdown 生成、registry 条目构建。
No filesystem/ChromaDB dependency — mocks file I/O and YAML operations.
"""
import pytest
from unittest.mock import MagicMock, patch, mock_open
from pathlib import Path

from aitest.knowledge.skill_proposer import (
    SkillProposer,
    ProposedSkill,
    propose_skills,
    MIN_FIX_COUNT,
    MIN_CONFIDENCE,
)
from aitest.knowledge.knowledge_extractor import ExtractedPattern


# ══════════════════════════════════════════════════════════════════════════
#  Helpers
# ══════════════════════════════════════════════════════════════════════════


def _make_fix_patterns(
    count: int = 3,
    failure_type: str = "StaleLocator",
    module: str = "equipment",
    confidence: float = 0.85,
) -> list[ExtractedPattern]:
    """创建测试用的 fix 模式列表。"""
    patterns = []
    for i in range(count):
        patterns.append(ExtractedPattern(
            pattern_type="fix",
            module=module,
            summary=f"Fix for {failure_type}: strategy {i+1}",
            detail=f"Detailed fix strategy {i+1} for {failure_type}",
            confidence=confidence,
            source_run_id=f"run-{i}",
        ))
    return patterns


def _make_mixed_patterns(count: int = 5) -> list[ExtractedPattern]:
    """创建混合类型模式列表（locator + failure + fix）。"""
    patterns = []
    for i in range(count):
        patterns.append(ExtractedPattern(
            pattern_type="locator",
            module="equipment",
            summary=f"Locator pattern {i}",
            confidence=0.8,
        ))
    # Add fix patterns that meet threshold
    patterns.extend(_make_fix_patterns(count=3, failure_type="Timeout", module="equipment"))
    return patterns


# ══════════════════════════════════════════════════════════════════════════
#  ProposedSkill
# ══════════════════════════════════════════════════════════════════════════


class TestProposedSkill:
    def test_defaults(self):
        ps = ProposedSkill(skill_id="test-skill")
        assert ps.skill_id == "test-skill"
        assert ps.category == "auto-generated"
        assert ps.confidence == 0.0
        assert ps.source_pattern_count == 0
        assert ps.trigger_patterns == []
        assert ps.fix_strategies == []

    def test_custom_values(self):
        ps = ProposedSkill(
            skill_id="auto-fix-stalelocator-abc123",
            title="Auto-fix: StaleLocator (equipment)",
            confidence=0.85,
            source_pattern_count=5,
            source_modules=["equipment", "personnel"],
        )
        assert ps.confidence == 0.85
        assert len(ps.source_modules) == 2


# ══════════════════════════════════════════════════════════════════════════
#  _extract_failure_type
# ══════════════════════════════════════════════════════════════════════════


class TestExtractFailureType:
    def test_fix_for_format(self):
        assert SkillProposer._extract_failure_type("Fix for StaleLocator: ...") == "StaleLocator"

    def test_bracket_format(self):
        assert SkillProposer._extract_failure_type("[Timeout] some error") == "Timeout"

    def test_unknown_format(self):
        assert SkillProposer._extract_failure_type("random text") == "Unknown"

    def test_empty_string(self):
        assert SkillProposer._extract_failure_type("") == "Unknown"


# ══════════════════════════════════════════════════════════════════════════
#  _group_fix_patterns
# ══════════════════════════════════════════════════════════════════════════


class TestGroupFixPatterns:
    def test_groups_fix_patterns(self):
        proposer = SkillProposer()
        patterns = _make_fix_patterns(count=4, failure_type="StaleLocator", module="equipment")
        groups = proposer._group_fix_patterns(patterns)
        assert "StaleLocator:equipment" in groups
        assert len(groups["StaleLocator:equipment"]) == 4

    def test_ignores_locator_patterns(self):
        proposer = SkillProposer()
        patterns = [
            ExtractedPattern(pattern_type="locator", module="m", summary="A"),
            ExtractedPattern(pattern_type="correlation", module="m", summary="B"),
        ]
        groups = proposer._group_fix_patterns(patterns)
        assert len(groups) == 0

    def test_separates_by_module(self):
        proposer = SkillProposer()
        patterns = _make_fix_patterns(count=2, failure_type="Timeout", module="equipment")
        patterns.extend(_make_fix_patterns(count=2, failure_type="Timeout", module="personnel"))
        groups = proposer._group_fix_patterns(patterns)
        assert "Timeout:equipment" in groups
        assert "Timeout:personnel" in groups
        assert len(groups) == 2

    def test_failure_patterns_included(self):
        proposer = SkillProposer()
        patterns = [
            ExtractedPattern(
                pattern_type="failure",
                module="m",
                summary="[StaleLocator] element not found",
                confidence=0.8,
            ),
        ]
        groups = proposer._group_fix_patterns(patterns)
        assert "StaleLocator:m" in groups

    def test_empty_input(self):
        proposer = SkillProposer()
        assert proposer._group_fix_patterns([]) == {}


# ══════════════════════════════════════════════════════════════════════════
#  propose_from_patterns — threshold filtering
# ══════════════════════════════════════════════════════════════════════════


class TestProposeFromPatterns:
    def test_below_threshold_returns_empty(self):
        """低于 min_fix_count 的模式不蒸馏。"""
        proposer = SkillProposer(min_fix_count=5, auto_register=False)
        patterns = _make_fix_patterns(count=3)
        result = proposer.propose_from_patterns(patterns)
        assert result == []

    def test_meets_threshold_proposes_skill(self):
        """达到阈值的模式蒸馏出技能。"""
        proposer = SkillProposer(min_fix_count=3, auto_register=False)
        patterns = _make_fix_patterns(count=3)
        result = proposer.propose_from_patterns(patterns)
        assert len(result) == 1
        assert result[0].source_pattern_count == 3
        assert "StaleLocator" in result[0].title

    def test_low_confidence_filtered(self):
        """低置信度模式被过滤。"""
        proposer = SkillProposer(min_fix_count=2, min_confidence=0.9, auto_register=False)
        patterns = _make_fix_patterns(count=3, confidence=0.5)
        result = proposer.propose_from_patterns(patterns)
        assert result == []

    def test_mixed_patterns_only_fix_distilled(self):
        """混合模式中只有 fix 类型被蒸馏。"""
        proposer = SkillProposer(min_fix_count=3, auto_register=False)
        patterns = _make_mixed_patterns(count=5)
        result = proposer.propose_from_patterns(patterns)
        # Only the Timeout fix group (3 patterns) should be distilled
        assert len(result) == 1
        assert "Timeout" in result[0].title

    def test_empty_input(self):
        proposer = SkillProposer(auto_register=False)
        assert proposer.propose_from_patterns([]) == []

    def test_multiple_groups(self):
        """多个满足阈值的组各自蒸馏。"""
        proposer = SkillProposer(min_fix_count=2, auto_register=False)
        patterns = _make_fix_patterns(count=2, failure_type="Timeout", module="equipment")
        patterns.extend(_make_fix_patterns(count=2, failure_type="Assertion", module="personnel"))
        result = proposer.propose_from_patterns(patterns)
        assert len(result) == 2
        types = {r.title for r in result}
        assert any("Timeout" in t for t in types)
        assert any("Assertion" in t for t in types)


# ══════════════════════════════════════════════════════════════════════════
#  _distill_skill
# ══════════════════════════════════════════════════════════════════════════


class TestDistillSkill:
    def test_skill_id_format(self):
        proposer = SkillProposer(auto_register=False)
        patterns = _make_fix_patterns(count=3, failure_type="StaleLocator", module="equipment")
        skill = proposer._distill_skill("StaleLocator:equipment", patterns)
        assert skill.skill_id.startswith("auto-fix-stalelocator-")
        assert len(skill.skill_id) == len("auto-fix-stalelocator-") + 8  # hash 8 chars

    def test_markdown_contains_key_sections(self):
        proposer = SkillProposer(auto_register=False)
        patterns = _make_fix_patterns(count=3, failure_type="Timeout", module="equipment")
        skill = proposer._distill_skill("Timeout:equipment", patterns)
        assert "# Skill:" in skill.markdown
        assert "## 目标" in skill.markdown
        assert "## 触发条件" in skill.markdown
        assert "## 修复策略" in skill.markdown
        assert "experimental" in skill.markdown

    def test_registry_entry_format(self):
        proposer = SkillProposer(auto_register=False)
        patterns = _make_fix_patterns(count=3, failure_type="Timeout", module="equipment")
        skill = proposer._distill_skill("Timeout:equipment", patterns)
        entry = skill.registry_entry
        assert entry["status"] == "experimental"
        assert entry["risk_level"] == "medium"
        assert entry["needs_confirm"] is True
        assert entry["contract"]["stability"] == "experimental"
        assert entry["current_version"] == "0.1-exp"

    def test_confidence_averaged(self):
        proposer = SkillProposer(auto_register=False)
        patterns = [
            ExtractedPattern(
                pattern_type="fix", module="m",
                summary="Fix for X: a", detail="a",
                confidence=0.7,
            ),
            ExtractedPattern(
                pattern_type="fix", module="m",
                summary="Fix for X: b", detail="b",
                confidence=0.9,
            ),
        ]
        skill = proposer._distill_skill("X:m", patterns)
        assert skill.confidence == 0.8


# ══════════════════════════════════════════════════════════════════════════
#  propose_skills (convenience function)
# ══════════════════════════════════════════════════════════════════════════


class TestProposeSkills:
    def test_returns_simplified_dicts(self):
        proposer = SkillProposer(min_fix_count=3, auto_register=False)
        patterns = _make_fix_patterns(count=3)
        # Patch the class to disable file I/O
        with patch.object(SkillProposer, '_write_skill_file'):
            with patch.object(SkillProposer, '_register_to_yaml'):
                result = propose_skills(patterns, min_fix_count=3)
        assert isinstance(result, list)
        if result:
            assert "skill_id" in result[0]
            assert "confidence" in result[0]
            assert "source_patterns" in result[0]

    def test_empty_patterns(self):
        result = propose_skills([], min_fix_count=1)
        assert result == []

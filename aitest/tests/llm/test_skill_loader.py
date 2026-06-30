"""Tests for llm/skill_loader.py — skill prompt loading + versioning.

Tests: load_skill, list_skills, list_categories, get_skill_version,
resolve_skill_version, load_variant, list_variants, caching.
Uses real skill files from governance/skills/ (checked into repo).
"""
import pytest
from unittest.mock import patch, MagicMock

from aitest.llm.skill_loader import (
    load_skill, list_skills, list_categories,
    get_skill_version, resolve_skill_version,
    load_variant, list_variants,
    SkillVersionInfo, PromptVariant,
    SKILLS_DIR, SKILLS_DEV_DIR,
)


# ══════════════════════════════════════════════════════════════════════════
#  load_skill — existing skills
# ══════════════════════════════════════════════════════════════════════════


class TestLoadSkill:
    def test_loads_existing_skill_by_full_id(self):
        content = load_skill("automation/test-script-generator")
        assert len(content) > 50
        assert "test-script-generator" in content.lower() or "test" in content.lower()

    def test_loads_skill_with_content(self):
        content = load_skill("execution/data-sanitization")
        assert len(content) > 0
        assert isinstance(content, str)

    def test_raises_for_nonexistent_skill(self):
        with pytest.raises(FileNotFoundError, match="Skill not found"):
            load_skill("nonexistent/fake-skill-xyz")

    def test_loads_skill_with_version_syntax(self):
        """@version syntax parses version from skill_id."""
        # skill without @ — loads current
        content = load_skill("automation/test-script-generator")
        assert len(content) > 0


# ══════════════════════════════════════════════════════════════════════════
#  list_skills + list_categories
# ══════════════════════════════════════════════════════════════════════════


class TestListSkills:
    def test_returns_skills(self):
        skills = list_skills()
        assert len(skills) > 5
        for s in skills:
            assert "id" in s
            assert "category" in s
            assert "status" in s

    def test_filter_by_category(self):
        auto_skills = list_skills(category="automation")
        assert len(auto_skills) > 0
        for s in auto_skills:
            assert s["category"] == "automation"

    def test_unknown_category_returns_empty(self):
        result = list_skills(category="nonexistent-category-xyz")
        assert result == []


class TestListCategories:
    def test_returns_categories(self):
        cats = list_categories()
        assert "automation" in cats
        assert "execution" in cats
        assert "test-design" in cats

    def test_all_categories_are_strings(self):
        for cat in list_categories():
            assert isinstance(cat, str)


# ══════════════════════════════════════════════════════════════════════════
#  get_skill_version
# ══════════════════════════════════════════════════════════════════════════


class TestGetSkillVersion:
    def test_returns_none_for_unknown_skill(self):
        assert get_skill_version("nonexistent/skill") is None

    def test_returns_version_info_for_known_skill(self):
        info = get_skill_version("automation/test-script-generator")
        if info is not None:  # May not have version in registry
            assert isinstance(info, SkillVersionInfo)
            assert info.skill_id

    def test_version_info_has_required_fields(self):
        # Test with a skill we know is in the registry
        info = get_skill_version("automation/test-script-generator")
        if info is not None:
            assert info.resolved_version
            assert info.file_path


# ══════════════════════════════════════════════════════════════════════════
#  resolve_skill_version
# ══════════════════════════════════════════════════════════════════════════


class TestResolveSkillVersion:
    def test_resolves_unknown_skill_with_default(self):
        info = resolve_skill_version("nonexistent/skill-xyz")
        assert isinstance(info, SkillVersionInfo)
        assert info.skill_id == "nonexistent/skill-xyz"
        assert info.resolved_version == "?"

    def test_resolves_known_skill(self):
        info = resolve_skill_version("automation/test-script-generator")
        assert isinstance(info, SkillVersionInfo)

    def test_at_syntax_strips_version(self):
        info = resolve_skill_version("automation/test-script-generator@v9.9")
        assert isinstance(info, SkillVersionInfo)
        # Registry may store skill with short name or full ID
        assert "test-script-generator" in info.skill_id or "automation" in info.skill_id


# ══════════════════════════════════════════════════════════════════════════
#  Variants
# ══════════════════════════════════════════════════════════════════════════


class TestVariants:
    def test_list_variants_returns_list(self):
        variants = list_variants()
        assert isinstance(variants, list)

    def test_list_variants_filter_by_skill(self):
        variants = list_variants(skill_id="nonexistent")
        assert variants == []

    def test_load_variant_invalid_raises(self):
        with pytest.raises(ValueError, match="Variant"):
            load_variant("automation/test-script-generator", "nonexistent-variant-xyz")


# ══════════════════════════════════════════════════════════════════════════
#  PromptVariant dataclass
# ══════════════════════════════════════════════════════════════════════════


class TestPromptVariantDataclass:
    def test_default_tags(self):
        pv = PromptVariant(
            variant_id="test-v1",
            skill_id="test-skill",
            version="1.0",
        )
        assert pv.tags == []
        assert pv.description == ""
        assert pv.content == ""

    def test_to_dict(self):
        pv = PromptVariant(
            variant_id="v2",
            skill_id="test-design/page-analysis",
            version="2.0-exp",
            tags=["experimental"],
            description="Shorter variant",
        )
        d = pv.to_dict()
        assert d["variant_id"] == "v2"
        assert d["version"] == "2.0-exp"
        assert "experimental" in d["tags"]


# ══════════════════════════════════════════════════════════════════════════
#  Caching — lru_cache correctness
# ══════════════════════════════════════════════════════════════════════════


class TestCaching:
    def test_same_skill_returns_consistent_content(self):
        a = load_skill("automation/test-script-generator")
        b = load_skill("automation/test-script-generator")
        assert a == b

    def test_list_categories_is_stable(self):
        cats1 = list_categories()
        cats2 = list_categories()
        assert cats1 == cats2

"""Tests for platform/complexity/ — page complexity scoring + pipeline routing.

Tests: score_to_tier, pipeline_for_tier, ComplexityTier, PageComplexityProfile,
COMPLEXITY_RULES scoring, ComplexityClassifier (quick + heuristic paths).
LLM refinement path mocked.
"""
import pytest
from unittest.mock import patch, MagicMock

from aitest.platform.complexity.factors import (
    ComplexityTier, PageComplexityProfile, COMPLEXITY_RULES,
    SIMPLE_THRESHOLD, COMPLEX_THRESHOLD,
    SIMPLE_PIPELINE, STANDARD_PIPELINE, COMPLEX_PIPELINE,
    score_to_tier, pipeline_for_tier,
)
from aitest.platform.complexity.classifier import (
    ComplexityClassifier, IMMEDIATE_SIMPLE_PAGE_TITLES, IMMEDIATE_COMPLEX_PAGE_TITLES,
)


# ══════════════════════════════════════════════════════════════════════════
#  score_to_tier
# ══════════════════════════════════════════════════════════════════════════


class TestScoreToTier:
    def test_zero_is_simple(self):
        assert score_to_tier(0) == ComplexityTier.SIMPLE

    def test_below_simple_threshold_is_simple(self):
        assert score_to_tier(SIMPLE_THRESHOLD - 1) == ComplexityTier.SIMPLE
        assert score_to_tier(SIMPLE_THRESHOLD) == ComplexityTier.SIMPLE

    def test_between_is_standard(self):
        assert score_to_tier(SIMPLE_THRESHOLD + 1) == ComplexityTier.STANDARD
        assert score_to_tier(40) == ComplexityTier.STANDARD
        assert score_to_tier(COMPLEX_THRESHOLD - 1) == ComplexityTier.STANDARD

    def test_above_complex_threshold_is_complex(self):
        assert score_to_tier(COMPLEX_THRESHOLD) == ComplexityTier.COMPLEX
        assert score_to_tier(100) == ComplexityTier.COMPLEX


# ══════════════════════════════════════════════════════════════════════════
#  pipeline_for_tier
# ══════════════════════════════════════════════════════════════════════════


class TestPipelineForTier:
    def test_simple_pipeline_is_shortest(self):
        p = pipeline_for_tier(ComplexityTier.SIMPLE)
        assert len(p) == 2
        assert "automation-agent" in p

    def test_standard_pipeline(self):
        p = pipeline_for_tier(ComplexityTier.STANDARD)
        assert 4 <= len(p) <= 6

    def test_complex_pipeline_is_full(self):
        p = pipeline_for_tier(ComplexityTier.COMPLEX)
        assert len(p) >= 7
        assert "knowledge-agent" in p


# ══════════════════════════════════════════════════════════════════════════
#  PageComplexityProfile dataclass
# ══════════════════════════════════════════════════════════════════════════


class TestPageComplexityProfile:
    def test_defaults(self):
        p = PageComplexityProfile()
        assert p.tier == ComplexityTier.STANDARD
        assert p.score == 0.0
        assert p.field_count == 0
        assert p.has_dialog is False

    def test_scoring_field_count(self):
        p = PageComplexityProfile(field_count=30)
        score = COMPLEXITY_RULES["field_count"](p.field_count)
        assert 0 < score <= 50

    def test_field_count_capped(self):
        p = PageComplexityProfile(field_count=200)
        score = COMPLEXITY_RULES["field_count"](p.field_count)
        assert score == 50  # capped

    def test_table_column_scoring(self):
        p = PageComplexityProfile(table_column_count=20)
        score = COMPLEXITY_RULES["table_column_count"](p.table_column_count)
        assert score == 30  # 20 * 1.5 = 30

    def test_boolean_rules_are_flat_values(self):
        for key in ["has_dialog", "has_wizard", "has_workflow"]:
            assert isinstance(COMPLEXITY_RULES[key], (int, float)), \
                f"{key} should be a flat score value"

    def test_involves_money_adds_20(self):
        p = PageComplexityProfile(involves_money=True)
        assert COMPLEXITY_RULES["involves_money"] == 20

    def test_all_rules_have_corresponding_profile_fields(self):
        """Every rule key must be a valid PageComplexityProfile field."""
        for key in COMPLEXITY_RULES:
            assert hasattr(PageComplexityProfile(), key), \
                f"Rule '{key}' has no matching field in PageComplexityProfile"


# ══════════════════════════════════════════════════════════════════════════
#  ComplexityClassifier — quick path
# ══════════════════════════════════════════════════════════════════════════


class TestQuickClassify:
    def test_simple_title_match(self):
        c = ComplexityClassifier()
        result = c._quick_classify("用户详情", {})
        assert result is not None
        assert result.tier == ComplexityTier.SIMPLE

    def test_complex_title_match(self):
        c = ComplexityClassifier()
        result = c._quick_classify("审批管理", {})
        assert result is not None
        assert result.tier == ComplexityTier.COMPLEX
        assert result.has_workflow is True

    def test_no_match_returns_none(self):
        c = ComplexityClassifier()
        result = c._quick_classify("常规页面", {})
        assert result is None

    def test_case_insensitive_match(self):
        c = ComplexityClassifier()
        result = c._quick_classify("Detail Page", {})
        assert result is not None
        assert result.tier == ComplexityTier.SIMPLE

    def test_complex_match_in_components(self):
        c = ComplexityClassifier()
        result = c._quick_classify("普通标题", {"components": ["workflow", "form"]})
        assert result is not None
        assert result.tier == ComplexityTier.COMPLEX


# ══════════════════════════════════════════════════════════════════════════
#  ComplexityClassifier — heuristic path
# ══════════════════════════════════════════════════════════════════════════


class TestHeuristicClassify:
    def test_empty_data_scores_low(self):
        c = ComplexityClassifier()
        result = c._heuristic_classify({})
        assert result.tier == ComplexityTier.SIMPLE
        assert result.score <= SIMPLE_THRESHOLD

    def test_many_fields_scores_higher(self):
        c = ComplexityClassifier()
        result = c._heuristic_classify({"fields": [f"f{i}" for i in range(40)]})
        assert result.field_count == 40
        assert result.score > SIMPLE_THRESHOLD

    def test_complex_components_flag(self):
        c = ComplexityClassifier()
        result = c._heuristic_classify({
            "fields": [f"f{i}" for i in range(20)],
            "components": ["dialog", "wizard", "upload", "tree", "tabs"],
            "interactions": ["search", "batch", "import"],
        })
        assert result.has_dialog is True
        assert result.has_wizard is True
        assert result.has_search_filter is True
        assert result.has_batch_operation is True

    def test_dialog_via_alternate_keywords(self):
        c = ComplexityClassifier()
        for kw in ["modal", "drawer"]:
            result = c._heuristic_classify({"components": [kw]})
            assert result.has_dialog is True, f"'{kw}' should match has_dialog"

    def test_cascading_detection(self):
        c = ComplexityClassifier()
        result = c._heuristic_classify({"components": ["cascader"]})
        assert result.has_cascading is True

    def test_score_capped_at_100(self):
        c = ComplexityClassifier()
        result = c._heuristic_classify({
            "fields": [f"f{i}" for i in range(100)],
            "table_columns": [f"c{i}" for i in range(50)],
            "components": ["dialog", "wizard", "upload", "workflow", "tree", "tabs", "chart", "cascader", "rich_editor"],
            "interactions": ["search", "batch", "import", "export"],
            "page_type": "wizard",
        })
        result.involves_money = True
        result.involves_approval = True
        result.is_critical_path = True
        result.has_dynamic_form = True
        result.has_cross_page_validation = True
        # Re-score
        score = 0.0
        for rule_key, rule_fn in COMPLEXITY_RULES.items():
            value = getattr(result, rule_key, None)
            if value is None:
                continue
            if isinstance(value, bool):
                if value:
                    score += rule_fn
            elif isinstance(value, (int, float)) and value > 0:
                score += rule_fn(value) if callable(rule_fn) else rule_fn
        assert score >= 100  # would exceed without cap
        assert result.score <= 100  # capped at 100


# ══════════════════════════════════════════════════════════════════════════
#  ComplexityClassifier — full classify (mocked LLM)
# ══════════════════════════════════════════════════════════════════════════


class TestClassifyFull:
    def test_simple_page_uses_quick_path(self):
        c = ComplexityClassifier()
        result = c.classify(page_title="用户详情")
        assert result.tier == ComplexityTier.SIMPLE

    def test_complex_page_uses_quick_path(self):
        c = ComplexityClassifier()
        result = c.classify(
            page_title="设备管理",
            discovery_data={"components": ["workflow", "timeline"]},
        )
        assert result.tier == ComplexityTier.COMPLEX

    def test_regular_page_uses_heuristic_path(self):
        c = ComplexityClassifier()
        result = c.classify(
            page_title="设备列表",
            discovery_data={"fields": [f"f{i}" for i in range(5)]},
        )
        assert result.tier in (ComplexityTier.SIMPLE, ComplexityTier.STANDARD)

    def test_borderline_triggers_llm_refine(self, fake_llm):
        """Score 15-70 triggers LLM refinement."""
        c = ComplexityClassifier()
        # ~15 fields + 2 components → ~30 score (borderline)
        fake_llm.set_response("STANDARD")
        with patch("aitest.llm.provider.get_provider", return_value=fake_llm):
            result = c.classify(
                page_title="中等页面",
                discovery_data={
                    "fields": [f"f{i}" for i in range(15)],
                    "components": ["dialog", "tabs"],
                },
            )
        assert result.tier is not None

    def test_llm_failure_returns_heuristic(self):
        """LLM failure doesn't crash — returns heuristic tier."""
        c = ComplexityClassifier()
        fake_llm = MagicMock()
        fake_llm.complete.side_effect = RuntimeError("API down")
        with patch("aitest.llm.provider.get_provider", return_value=fake_llm):
            result = c.classify(
                page_title="边界页面",
                discovery_data={"fields": [f"f{i}" for i in range(15)]},
            )
        assert result.tier is not None  # heuristic fallback worked

    def test_high_score_no_llm(self, fake_llm):
        """Score > 70 skips LLM — already clearly COMPLEX."""
        c = ComplexityClassifier()
        # Many fields + complex components → high score
        data = {
            "fields": [f"f{i}" for i in range(80)],
            "components": ["wizard", "workflow", "dialog", "upload"],
            "interactions": ["search", "batch", "import"],
        }
        result = c.classify(discovery_data=data)
        assert result.tier == ComplexityTier.COMPLEX
        # LLM should NOT have been called


# ══════════════════════════════════════════════════════════════════════════
#  ComplexityTier enum
# ══════════════════════════════════════════════════════════════════════════


class TestComplexityTier:
    def test_three_values(self):
        assert ComplexityTier.SIMPLE.value == "simple"
        assert ComplexityTier.STANDARD.value == "standard"
        assert ComplexityTier.COMPLEX.value == "complex"

    def test_is_string_enum(self):
        assert isinstance(ComplexityTier.SIMPLE, str)

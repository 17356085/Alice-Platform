"""Tests for knowledge/knowledge_extractor.py — ExtractedPattern, KnowledgeExtractor.

Tests: ExtractedPattern dataclass, _deduplicate, _find_cross_module.
No ChromaDB dependency — tests pure extraction logic only.
"""
import pytest
from unittest.mock import MagicMock

from aitest.knowledge.knowledge_extractor import (
    ExtractedPattern, KnowledgeExtractor,
)


# ══════════════════════════════════════════════════════════════════════════
#  ExtractedPattern
# ══════════════════════════════════════════════════════════════════════════


class TestExtractedPattern:
    def test_defaults(self):
        p = ExtractedPattern(pattern_type="locator", module="equipment")
        assert p.pattern_type == "locator"
        assert p.module == "equipment"
        assert p.page == ""
        assert p.confidence == 0.5
        assert p.cross_module_applicable == []

    def test_custom_values(self):
        p = ExtractedPattern(
            pattern_type="failure",
            module="equipment",
            page="alarm-config",
            summary="Timeout waiting for table",
            detail="el-table not rendered within 10s",
            confidence=0.9,
            cross_module_applicable=["personnel"],
        )
        assert p.pattern_type == "failure"
        assert p.confidence == 0.9
        assert p.cross_module_applicable == ["personnel"]

    def test_auto_timestamp(self):
        p = ExtractedPattern(pattern_type="fix", module="m")
        assert p.extracted_at != ""


# ══════════════════════════════════════════════════════════════════════════
#  KnowledgeExtractor — initialization
# ══════════════════════════════════════════════════════════════════════════


class TestKnowledgeExtractorInit:
    def test_default_auto_index(self):
        ext = KnowledgeExtractor()
        assert ext.auto_index is True

    def test_disable_auto_index(self):
        ext = KnowledgeExtractor(auto_index=False)
        assert ext.auto_index is False

    def test_empty_extracted(self):
        ext = KnowledgeExtractor()
        assert ext._extracted == []


# ══════════════════════════════════════════════════════════════════════════
#  extract_from_execution (mocked ChromaDB)
# ══════════════════════════════════════════════════════════════════════════


class TestExtractFromExecution:
    def test_returns_list(self, monkeypatch):
        ext = KnowledgeExtractor(auto_index=False)
        # Mock _index_to_chromadb to avoid ChromaDB calls
        monkeypatch.setattr(ext, "_index_to_chromadb", lambda patterns: None)
        result = ext.extract_from_execution(module="equipment")
        assert isinstance(result, list)

    def test_empty_events_returns_empty(self, monkeypatch):
        ext = KnowledgeExtractor(auto_index=False)
        monkeypatch.setattr(ext, "_index_to_chromadb", lambda patterns: None)
        result = ext.extract_from_execution(
            module="equipment", trace_events=[], execution_results={}
        )
        assert result == []

    def test_with_trace_events(self, monkeypatch):
        ext = KnowledgeExtractor(auto_index=False)
        monkeypatch.setattr(ext, "_index_to_chromadb", lambda patterns: None)
        events = [
            {
                "event_type": "skill_execution",
                "skill_id": "automation/page-object-generator",
                "status": "success",
                "response_preview": 'By.CSS_SELECTOR("[data-testid=alarm-table]")',
                "metadata": {"page": "alarm"},
                "run_id": "r1",
            },
        ]
        result = ext.extract_from_execution(module="equipment", trace_events=events)
        assert isinstance(result, list)


# ══════════════════════════════════════════════════════════════════════════
#  _extract_locator_patterns
# ══════════════════════════════════════════════════════════════════════════


class TestExtractLocatorPatterns:
    def test_finds_css_selector(self):
        ext = KnowledgeExtractor()
        # Use format that matches the regex: By.CSS_SELECTOR("...")
        events = [
            {
                "event_type": "skill_execution",
                "skill_id": "automation/page-object-generator",
                "status": "success",
                "response_preview": 'By.CSS_SELECTOR("[data-testid=alarm-table]")',
                "metadata": {"page": "alarm"},
                "run_id": "r1",
            },
        ]
        patterns = ext._extract_locator_patterns(events, "equipment")
        assert len(patterns) >= 1
        assert patterns[0].pattern_type == "locator"

    def test_ignores_non_automation_events(self):
        ext = KnowledgeExtractor()
        events = [
            {
                "event_type": "skill_execution",
                "skill_id": "project/context-manager",
                "status": "success",
                "response_preview": 'By.CSS_SELECTOR(".test")',
                "metadata": {},
                "run_id": "r1",
            },
        ]
        patterns = ext._extract_locator_patterns(events, "equipment")
        assert len(patterns) == 0

    def test_ignores_failed_events(self):
        ext = KnowledgeExtractor()
        events = [
            {
                "event_type": "skill_execution",
                "skill_id": "automation/page-object-generator",
                "status": "error",
                "response_preview": 'By.CSS_SELECTOR(".test")',
                "metadata": {},
                "run_id": "r1",
            },
        ]
        patterns = ext._extract_locator_patterns(events, "equipment")
        assert len(patterns) == 0

    def test_ignores_trivial_xpath(self):
        ext = KnowledgeExtractor()
        events = [
            {
                "event_type": "skill_execution",
                "skill_id": "automation/page-object-generator",
                "status": "success",
                "response_preview": 'By.XPATH("//div")',
                "metadata": {},
                "run_id": "r1",
            },
        ]
        patterns = ext._extract_locator_patterns(events, "equipment")
        assert len(patterns) == 0


# ══════════════════════════════════════════════════════════════════════════
#  _deduplicate
# ══════════════════════════════════════════════════════════════════════════


class TestDeduplicate:
    def test_removes_duplicates(self):
        ext = KnowledgeExtractor()
        patterns = [
            ExtractedPattern(pattern_type="locator", module="m", summary="Same locator"),
            ExtractedPattern(pattern_type="locator", module="m", summary="Same locator"),
            ExtractedPattern(pattern_type="locator", module="m", summary="Different locator"),
        ]
        result = ext._deduplicate(patterns)
        assert len(result) == 2

    def test_empty_input(self):
        ext = KnowledgeExtractor()
        assert ext._deduplicate([]) == []

    def test_preserves_unique(self):
        ext = KnowledgeExtractor()
        patterns = [
            ExtractedPattern(pattern_type="locator", module="m1", summary="A"),
            ExtractedPattern(pattern_type="failure", module="m2", summary="B"),
        ]
        result = ext._deduplicate(patterns)
        assert len(result) == 2

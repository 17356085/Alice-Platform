"""Tests for llm/context_builder.py — 6-step context discovery pipeline.

Tests: extract_keywords, _score_relevance, categorize_files,
discover_patterns, search_test_files, build_context.
Pure filesystem steps — no LLM calls.
"""
import pytest
from pathlib import Path

from alice_engine.core.context_builder import (
    extract_keywords, search_test_files, _score_relevance,
    categorize_files, discover_patterns, build_context,
    DiscoveredFile, SubtaskContext, FIXED_KEYWORDS,
    INTERESTING_PATTERNS, MAX_DISCOVERED_FILES, MAX_SNIPPET_CHARS,
)


# ══════════════════════════════════════════════════════════════════════════
#  extract_keywords
# ══════════════════════════════════════════════════════════════════════════


class TestExtractKeywords:
    def test_empty_returns_fixed_keywords(self):
        result = extract_keywords("")
        assert "conftest" in result
        assert "BasePage" in result
        assert "pytest" in result

    def test_filters_stop_words(self):
        result = extract_keywords("测试 页面 的 登录 功能")
        assert "登录" in result
        assert "功能" in result
        assert "测试" not in result  # stop word
        assert "页面" not in result  # stop word

    def test_deduplicates_case_insensitive(self):
        result = extract_keywords("Login login LOGIN Test TEST")
        # Should only have one "Login" (case-insensitive dedup)
        lower_results = [k.lower() for k in result]
        assert lower_results.count("login") == 1

    def test_strips_short_tokens(self):
        result = extract_keywords("a b c ab cd")
        # "a", "b", "c" are too short (< 2 chars)
        assert "a" not in result
        assert "b" not in result

    def test_appends_fixed_keywords(self):
        result = extract_keywords("CRUD operations")
        # Fixed keywords always appended at end
        assert "CRUD" in result or "crud" in result
        assert "conftest" in result

    def test_none_input(self):
        result = extract_keywords(None)
        assert len(result) == len(FIXED_KEYWORDS)

    def test_chinese_delimiters(self):
        result = extract_keywords("设备报警配置页面，CRUD测试；包含增删改查。")
        assert "设备报警配置页面" in result or "报警配置" in result or "CRUD测试" in result


# ══════════════════════════════════════════════════════════════════════════
#  _score_relevance
# ══════════════════════════════════════════════════════════════════════════


class TestScoreRelevance:
    def test_base_score(self):
        score = _score_relevance("script/equipment/test_alarm.py", "equipment")
        assert 0.5 < score <= 1.0

    def test_module_match_adds(self):
        with_mod = _score_relevance("script/equipment/test_x.py", "equipment")
        without_mod = _score_relevance("script/other/test_x.py", "equipment")
        assert with_mod > without_mod

    def test_page_match_adds(self):
        with_page = _score_relevance("page/equipment_page/alarm.py", "equipment", page="alarm")
        without_page = _score_relevance("page/equipment_page/alarm.py", "equipment", page="")
        assert with_page > without_page

    def test_keyword_hits(self):
        score = _score_relevance("script/test_login.py", "system", page="",
                                 keywords_lower=["login", "auth"])
        assert score > 0.3

    def test_capped_at_one(self):
        score = _score_relevance("equipment_alarm_config_test.py", "equipment",
                                 page="alarm", keywords_lower=["equipment", "alarm", "config", "test"])
        assert score <= 1.0


# ══════════════════════════════════════════════════════════════════════════
#  categorize_files
# ══════════════════════════════════════════════════════════════════════════


class TestCategorizeFiles:
    def test_conftest_is_reference(self):
        f = DiscoveredFile(path="script/conftest.py", role="", relevance=0.8, snippet="")
        modify, ref = categorize_files([f])
        assert len(modify) == 0
        assert len(ref) == 1
        assert ref[0].role == "reference"

    def test_init_is_reference(self):
        f = DiscoveredFile(path="page/__init__.py", role="", relevance=0.5, snippet="")
        modify, ref = categorize_files([f])
        assert len(ref) == 1
        assert ref[0].role == "reference"

    def test_test_py_is_modify(self):
        f = DiscoveredFile(path="script/equipment/test_alarm.py", role="", relevance=0.9, snippet="")
        modify, ref = categorize_files([f])
        assert len(modify) == 1
        assert len(ref) == 0
        assert modify[0].role == "modify"

    def test_md_is_reference(self):
        f = DiscoveredFile(path=".tlo/knowledge/modules/doc.md", role="", relevance=0.7, snippet="")
        modify, ref = categorize_files([f])
        assert len(modify) == 0
        assert len(ref) == 1
        assert ref[0].role == "reference"

    def test_mixed_files(self):
        files = [
            DiscoveredFile(path="script/test_a.py", role="", relevance=0.9, snippet=""),
            DiscoveredFile(path="script/conftest.py", role="", relevance=0.8, snippet=""),
            DiscoveredFile(path="page/equipment_page/locators.py", role="", relevance=0.7, snippet=""),
            DiscoveredFile(path=".tlo/doc.md", role="", relevance=0.5, snippet=""),
        ]
        modify, ref = categorize_files(files)
        assert len(modify) == 2  # test_a.py, locators.py
        assert len(ref) == 2     # conftest.py, doc.md

    def test_case_insensitive_basename_check(self):
        f = DiscoveredFile(path="script/Conftest.py", role="", relevance=0.8, snippet="")
        modify, ref = categorize_files([f])
        assert len(ref) == 1  # case-insensitive


# ══════════════════════════════════════════════════════════════════════════
#  discover_patterns
# ══════════════════════════════════════════════════════════════════════════


class TestDiscoverPatterns:
    def test_finds_pytest_fixture(self, temp_dir):
        ref_file = temp_dir / "conftest.py"
        ref_file.write_text('@pytest.fixture\ndef driver():\n    yield')
        f = DiscoveredFile(path="conftest.py", role="reference", relevance=1.0, snippet="")

        patterns = discover_patterns(temp_dir, [f])
        assert "pytest fixture" in patterns

    def test_finds_basepage_inheritance(self, temp_dir):
        ref_file = temp_dir / "base_page.py"
        ref_file.write_text('class LoginPage(BasePage):\n    pass')
        f = DiscoveredFile(path="base_page.py", role="reference", relevance=1.0, snippet="")

        patterns = discover_patterns(temp_dir, [f])
        assert "BasePage inheritance" in patterns

    def test_skips_nonexistent_file(self, temp_dir):
        f = DiscoveredFile(path="nonexistent.py", role="reference", relevance=1.0, snippet="")
        patterns = discover_patterns(temp_dir, [f])
        assert patterns == []

    def test_empty_reference_returns_empty(self, temp_dir):
        patterns = discover_patterns(temp_dir, [])
        assert patterns == []

    def test_returns_sorted(self, temp_dir):
        ref_file = temp_dir / "test_x.py"
        ref_file.write_text('@pytest.fixture\nclass X(BasePage):\n@By.CSS_SELECTOR')
        f = DiscoveredFile(path="test_x.py", role="reference", relevance=1.0, snippet="")

        patterns = discover_patterns(temp_dir, [f])
        assert patterns == sorted(patterns)


# ══════════════════════════════════════════════════════════════════════════
#  search_test_files
# ══════════════════════════════════════════════════════════════════════════


class TestSearchTestFiles:
    def test_empty_when_no_search_paths(self, temp_dir):
        """Returns empty list when project_root has no matching dirs."""
        files = search_test_files("nonexistent_module", temp_dir)
        assert files == []

    def test_finds_py_files_in_page_dir(self, temp_dir):
        page_dir = temp_dir / "page" / "equipment_page"
        page_dir.mkdir(parents=True)
        (page_dir / "alarm_config.py").write_text("# page object")
        subdir = page_dir / "subdir"
        subdir.mkdir(parents=True)
        (subdir / "nested.py").write_text("# nested")

        files = search_test_files("equipment", temp_dir)
        assert len(files) >= 1
        paths = [f.path for f in files]
        assert any("alarm_config" in p for p in paths)

    def test_finds_test_files_in_script_dir(self, temp_dir):
        script_dir = temp_dir / "script" / "equipment"
        script_dir.mkdir(parents=True)
        (script_dir / "test_alarm.py").write_text("def test_alarm():\n    pass")
        (script_dir / "test_config.py").write_text("def test_config():\n    pass")

        files = search_test_files("equipment", temp_dir)
        assert len(files) >= 2

    def test_respects_max_files(self, temp_dir):
        script_dir = temp_dir / "script" / "equipment"
        script_dir.mkdir(parents=True)
        for i in range(20):
            (script_dir / f"test_{i:02d}.py").write_text(f"# test {i}")

        files = search_test_files("equipment", temp_dir)
        assert len(files) <= MAX_DISCOVERED_FILES

    def test_snippet_truncated(self, temp_dir):
        script_dir = temp_dir / "script" / "equipment"
        script_dir.mkdir(parents=True)
        long_content = "x" * (MAX_SNIPPET_CHARS + 200)
        (script_dir / "test_xxx.py").write_text(long_content)

        files = search_test_files("equipment", temp_dir)
        assert len(files) >= 1
        assert len(files[0].snippet) <= MAX_SNIPPET_CHARS

    def test_finds_md_files_in_tlo_dir(self, temp_dir):
        tlo_dir = temp_dir / ".tlo" / "knowledge" / "modules" / "equipment"
        tlo_dir.mkdir(parents=True)
        (tlo_dir / "MODULE_CONTEXT.md").write_text("# Equipment Module Context")

        files = search_test_files("equipment", temp_dir)
        assert len(files) >= 1
        assert any(".md" in f.path for f in files)


# ══════════════════════════════════════════════════════════════════════════
#  build_context — main pipeline
# ══════════════════════════════════════════════════════════════════════════


class TestBuildContext:
    def test_returns_subtask_context(self, temp_dir):
        script_dir = temp_dir / "script" / "equipment"
        script_dir.mkdir(parents=True)
        (script_dir / "test_x.py").write_text("def test_x():\n    pass")

        ctx = build_context(
            module="equipment",
            project_root=temp_dir,
            task_description="设备报警配置页面 CRUD 测试",
        )
        assert isinstance(ctx, SubtaskContext)
        assert ctx.source_count >= 1
        assert len(ctx.keywords) > 0

    def test_include_memory_false_skips_step6(self, temp_dir):
        script_dir = temp_dir / "script" / "equipment"
        script_dir.mkdir(parents=True)
        (script_dir / "test_x.py").write_text("def test_x():\n    pass")

        ctx = build_context(
            module="equipment",
            project_root=temp_dir,
            include_memory=False,
        )
        assert ctx.memory_hints == ""

    def test_empty_project_root_returns_empty_context(self, temp_dir):
        ctx = build_context(
            module="nonexistent",
            project_root=temp_dir,
        )
        assert ctx.source_count == 0
        assert ctx.files == []

    def test_keywords_include_task_terms(self, temp_dir):
        script_dir = temp_dir / "script" / "system"
        script_dir.mkdir(parents=True)
        (script_dir / "test_user.py").write_text("def test():\n    pass")

        ctx = build_context(
            module="system",
            project_root=temp_dir,
            task_description="用户管理 权限配置",
        )
        # Keywords should include Chinese task terms
        assert any("用户管理" in kw or "权限配置" in kw for kw in ctx.keywords)


# ══════════════════════════════════════════════════════════════════════════
#  DiscoveredFile dataclass
# ══════════════════════════════════════════════════════════════════════════


class TestDiscoveredFile:
    def test_fields(self):
        f = DiscoveredFile(path="test.py", role="modify", relevance=0.9, snippet="code")
        assert f.path == "test.py"
        assert f.role == "modify"
        assert f.relevance == 0.9
        assert f.snippet == "code"

    def test_defaults(self):
        f = DiscoveredFile(path="", role="", relevance=0.0, snippet="")
        assert f.path == ""

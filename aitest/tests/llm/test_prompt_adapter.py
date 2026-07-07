"""Tests for llm/prompt_adapter.py — cross-model prompt adaptation.

Tests: PromptAdapter.adapt() for claude/openai/deepseek/ollama,
XML tag stripping, few-shot injection, context injection, truncation.
Pure string processing — no LLM calls.
"""
import pytest

from alice_engine.core.prompt_adapter import PromptAdapter


# ══════════════════════════════════════════════════════════════════════════
#  PromptAdapter — adapt()
# ══════════════════════════════════════════════════════════════════════════


class TestAdapt:
    def test_claude_returns_unchanged(self):
        adapter = PromptAdapter()
        prompt = "You are a test automation agent."
        result = adapter.adapt(prompt, "claude")
        assert result == prompt

    def test_unknown_provider_returns_unchanged(self):
        adapter = PromptAdapter()
        prompt = "Test prompt"
        result = adapter.adapt(prompt, "unknown-provider")
        assert result == prompt

    def test_openai_adds_context(self):
        adapter = PromptAdapter()
        prompt = "Test prompt"
        result = adapter.adapt(prompt, "openai", context="Extra info")
        assert "Extra info" in result
        assert "---" in result  # Markdown separator

    def test_ollama_strips_xml_tags(self):
        adapter = PromptAdapter()
        prompt = "<rules>Always use CSS selectors</rules>"
        result = adapter.adapt(prompt, "ollama")
        assert "<rules>" not in result
        assert "Always use CSS selectors" in result

    def test_ollama_strips_example_tags(self):
        adapter = PromptAdapter()
        prompt = "<example>def test(): pass</example>"
        result = adapter.adapt(prompt, "ollama")
        assert "<example>" not in result
        assert "def test(): pass" in result

    def test_ollama_strips_generic_tags(self):
        adapter = PromptAdapter()
        prompt = "<instructions>Do this</instructions>"
        result = adapter.adapt(prompt, "ollama")
        assert "<instructions>" not in result
        assert "**instructions**" in result

    def test_context_injection_with_separator(self):
        adapter = PromptAdapter()
        result = adapter.adapt("Base", "openai", context="Context data")
        assert "## 参考上下文" in result
        assert "Context data" in result

    def test_no_context_no_injection(self):
        adapter = PromptAdapter()
        result = adapter.adapt("Base", "openai")
        assert "参考上下文" not in result

    def test_truncation_for_long_prompt(self):
        adapter = PromptAdapter()
        long_prompt = "x" * 10000
        result = adapter.adapt(long_prompt, "ollama")  # max 4000
        assert len(result) < len(long_prompt)
        assert "截断" in result

    def test_truncation_preserves_head_and_tail(self):
        adapter = PromptAdapter()
        long_prompt = "HEAD" + "x" * 10000 + "TAIL"
        result = adapter.adapt(long_prompt, "ollama")
        assert "HEAD" in result
        assert "TAIL" in result


# ══════════════════════════════════════════════════════════════════════════
#  _strip_xml_tags
# ══════════════════════════════════════════════════════════════════════════


class TestStripXmlTags:
    def test_generic_tag_conversion(self):
        adapter = PromptAdapter()
        result = adapter._strip_xml_tags("<tag>content</tag>")
        assert "**tag**: content" in result

    def test_rules_tag(self):
        adapter = PromptAdapter()
        result = adapter._strip_xml_tags("<rules>Be careful</rules>")
        # Generic regex converts <rules>content</rules> → **rules**: content
        assert "<rules>" not in result
        assert "Be careful" in result

    def test_example_tag(self):
        adapter = PromptAdapter()
        result = adapter._strip_xml_tags("<example>code here</example>")
        # Generic regex converts <example>content</example> → **example**: content
        assert "<example>" not in result
        assert "code here" in result

    def test_no_tags_unchanged(self):
        adapter = PromptAdapter()
        text = "No tags here"
        result = adapter._strip_xml_tags(text)
        assert result == text


# ══════════════════════════════════════════════════════════════════════════
#  _inject_few_shot
# ══════════════════════════════════════════════════════════════════════════


class TestInjectFewShot:
    def test_skips_if_already_has_examples(self):
        adapter = PromptAdapter()
        text = "Some prompt with 示例 section"
        result = adapter._inject_few_shot(text)
        assert result == text

    def test_skips_if_has_example_keyword(self):
        adapter = PromptAdapter()
        text = "Some prompt with example"
        result = adapter._inject_few_shot(text)
        assert result == text

    def test_injects_for_page_analysis(self):
        adapter = PromptAdapter()
        text = "页面分析 prompt"
        result = adapter._inject_few_shot(text)
        assert "输出示例" in result

    def test_injects_for_code_generation(self):
        adapter = PromptAdapter()
        text = "代码生成 prompt"
        result = adapter._inject_few_shot(text)
        assert "输出示例" in result

    def test_no_injection_for_unknown_type(self):
        adapter = PromptAdapter()
        text = "Generic prompt"
        result = adapter._inject_few_shot(text)
        assert result == text


# ══════════════════════════════════════════════════════════════════════════
#  ADAPTATIONS config
# ══════════════════════════════════════════════════════════════════════════


class TestAdaptationsConfig:
    def test_all_providers_configured(self):
        adapter = PromptAdapter()
        for provider in ["claude", "openai", "deepseek", "ollama"]:
            assert provider in adapter.ADAPTATIONS

    def test_ollama_strips_xml(self):
        assert PromptAdapter.ADAPTATIONS["ollama"]["strip_xml_tags"] is True

    def test_claude_keeps_xml(self):
        assert PromptAdapter.ADAPTATIONS["claude"]["strip_xml_tags"] is False

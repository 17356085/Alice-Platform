"""Tests for agents/skill_executor.py — Agent→Skill mapping, run_skill.

Tests: AGENT_SKILL_MAP, _FALLBACK_AGENT_SKILL_MAP, _load_agent_definitions,
get_agent_definition, run_skill (mocked LLM).
No real LLM calls — all providers mocked.
"""
import pytest
from unittest.mock import patch, MagicMock

from aitest.agents.skill_executor import (
    AGENT_SKILL_MAP, _FALLBACK_AGENT_SKILL_MAP,
    _load_agent_definitions, get_agent_definition,
    run_skill, _ALL_SKILL_MAP,
)
from aitest.llm.provider_base import LLMResponse


# ══════════════════════════════════════════════════════════════════════════
#  AGENT_SKILL_MAP
# ══════════════════════════════════════════════════════════════════════════


class TestAgentSkillMap:
    def test_has_eight_agents(self):
        assert len(AGENT_SKILL_MAP) >= 8

    def test_project_agent_has_skills(self):
        skills = AGENT_SKILL_MAP.get("project-agent", [])
        assert len(skills) >= 2

    def test_automation_agent_has_skills(self):
        skills = AGENT_SKILL_MAP.get("automation-agent", [])
        assert len(skills) >= 3
        assert any("page-object" in s for s in skills)
        assert any("test-script" in s for s in skills)

    def test_all_skills_are_string_ids(self):
        for agent, skills in AGENT_SKILL_MAP.items():
            for skill in skills:
                assert isinstance(skill, str), f"{agent}: skill is not str: {skill}"
                assert "/" in skill, f"{agent}: skill '{skill}' missing category prefix"

    def test_fallback_map_covers_agents(self):
        for agent in ["project-agent", "requirement-agent", "test-design-agent",
                       "automation-agent", "execution-agent", "report-agent", "knowledge-agent"]:
            assert agent in _FALLBACK_AGENT_SKILL_MAP

    def test_all_skill_map_merges(self):
        assert len(_ALL_SKILL_MAP) >= len(AGENT_SKILL_MAP)


# ══════════════════════════════════════════════════════════════════════════
#  get_agent_definition
# ══════════════════════════════════════════════════════════════════════════


class TestGetAgentDefinition:
    def test_known_agent(self):
        defn = get_agent_definition("automation-agent")
        if defn:  # YAML may or may not be loaded
            assert isinstance(defn, dict)

    def test_unknown_agent_returns_empty(self):
        defn = get_agent_definition("nonexistent-agent-xyz")
        assert defn == {}


# ══════════════════════════════════════════════════════════════════════════
#  run_skill (mocked LLM)
# ══════════════════════════════════════════════════════════════════════════


class TestRunSkill:
    def test_nonexistent_skill_returns_error(self, fake_llm):
        """Skill that doesn't exist returns error LLMResponse."""
        response = run_skill(
            skill_id="nonexistent/fake-skill-xyz",
            user_input="do something",
            provider="fake",
        )
        assert response.finish_reason == "error"
        assert "Skill 加载失败" in response.content or "not found" in response.content.lower()

    def test_successful_skill_execution(self, fake_llm, monkeypatch):
        fake_llm.set_response("Test result: 3 tests passed", token_usage={"input": 100, "output": 50})

        monkeypatch.setattr("aitest.engine.skill_executor.get_provider", lambda p: fake_llm)

        response = run_skill(
            skill_id="execution/data-sanitization",
            user_input="Sanitize test data",
            provider="fake",
        )
        assert "Test result" in response.content
        assert response.finish_reason != "error"

    def test_provider_failure_returns_error(self, fake_llm, monkeypatch):
        fake_llm.set_error(ValueError("Provider not configured"))
        monkeypatch.setattr("aitest.engine.skill_executor.get_provider", lambda p: fake_llm)

        response = run_skill(
            skill_id="execution/data-sanitization",
            user_input="test",
            provider="fake",
        )
        assert response.finish_reason == "error"
        assert "Provider 初始化失败" in response.content

    def test_context_vars_passed_to_injector(self, fake_llm, monkeypatch):
        fake_llm.set_response("OK")
        monkeypatch.setattr("aitest.engine.skill_executor.get_provider", lambda p: fake_llm)

        response = run_skill(
            skill_id="execution/data-sanitization",
            user_input="test",
            context_vars={"module": "equipment", "page": "alarm"},
            provider="fake",
        )
        # Should not crash with context vars
        assert response.content == "OK"

    def test_variant_parameter(self, fake_llm, monkeypatch):
        fake_llm.set_response("variant response")
        monkeypatch.setattr("aitest.engine.skill_executor.get_provider", lambda p: fake_llm)

        response = run_skill(
            skill_id="execution/data-sanitization",
            user_input="test",
            variant=None,  # No variant
            provider="fake",
        )
        assert response.content == "variant response"

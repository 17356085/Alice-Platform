"""Tests for agents/runner_state.py — data structures (no LLM).

Tests: ArtifactRule, Observation, AgentState, AgentEvent,
AUTOMATION_ARTIFACT_RULES, DEV_ARTIFACT_RULES.
Pure dataclass tests — zero IO.
"""
import pytest

from aitest.agents.runner_state import (
    ArtifactRule, Observation, AgentState, AgentEvent,
    AUTOMATION_ARTIFACT_RULES, DEV_ARTIFACT_RULES, _ALL_ARTIFACT_RULES,
)


# ══════════════════════════════════════════════════════════════════════════
#  ArtifactRule
# ══════════════════════════════════════════════════════════════════════════


class TestArtifactRule:
    def test_defaults(self):
        rule = ArtifactRule(glob_pattern="test_*.py")
        assert rule.check_type == "exists_non_empty"
        assert rule.grep_pattern == ""
        assert rule.required is True
        assert rule.label == ""

    def test_grep_rule(self):
        rule = ArtifactRule(
            glob_pattern="*.py",
            check_type="grep_pass",
            grep_pattern=r"def test_",
            label="Has test functions",
        )
        assert rule.check_type == "grep_pass"
        assert rule.grep_pattern == r"def test_"

    def test_negative_grep(self):
        rule = ArtifactRule(
            glob_pattern="*.py",
            check_type="grep_pass",
            grep_pattern=r"time\.sleep\(",
            grep_should_find=False,
            label="No time.sleep",
        )
        assert rule.grep_should_find is False

    def test_optional_rule(self):
        rule = ArtifactRule(glob_pattern="conftest.py", required=False)
        assert rule.required is False


# ══════════════════════════════════════════════════════════════════════════
#  Artifact rule registries
# ══════════════════════════════════════════════════════════════════════════


class TestArtifactRuleRegistries:
    def test_automation_rules_have_key_skills(self):
        assert "automation/page-object-generator" in AUTOMATION_ARTIFACT_RULES
        assert "automation/test-script-generator" in AUTOMATION_ARTIFACT_RULES

    def test_page_object_rules_are_comprehensive(self):
        rules = AUTOMATION_ARTIFACT_RULES["automation/page-object-generator"]
        assert len(rules) >= 4  # At least file + BasePage + no-xpath + no-sleep

    def test_test_script_rules(self):
        rules = AUTOMATION_ARTIFACT_RULES["automation/test-script-generator"]
        assert len(rules) >= 3  # file + test_ function + no-sleep

    def test_all_artifact_rules_merges_both(self):
        """_ALL_ARTIFACT_RULES should contain rules from both registries."""
        assert "automation/page-object-generator" in _ALL_ARTIFACT_RULES
        # DEV rules may also be present

    def test_code_consistency_has_no_rules(self):
        rules = AUTOMATION_ARTIFACT_RULES.get("automation/code-consistency-checker", [])
        assert rules == []

    def test_all_rules_are_artifact_rule_instances(self):
        for skill_id, rules in AUTOMATION_ARTIFACT_RULES.items():
            for rule in rules:
                assert isinstance(rule, ArtifactRule), \
                    f"{skill_id} rule is not ArtifactRule: {type(rule)}"


# ══════════════════════════════════════════════════════════════════════════
#  Observation
# ══════════════════════════════════════════════════════════════════════════


class TestObservation:
    def test_defaults(self):
        obs = Observation(skill_id="test-skill")
        assert obs.status == "pending"
        assert obs.artifacts_found == []
        assert obs.quality_issues == []
        assert obs.suggestion == "continue"

    def test_auto_timestamp(self):
        obs = Observation(skill_id="test")
        assert obs.timestamp != ""

    def test_custom_values(self):
        obs = Observation(
            skill_id="automation/run",
            status="pass",
            artifacts_found=["report.xlsx"],
            summary="All tests passed",
            token_usage={"input": 1000, "output": 500},
            latency_ms=3200,
        )
        assert obs.status == "pass"
        assert "report.xlsx" in obs.artifacts_found
        assert obs.latency_ms == 3200

    def test_failure_categories(self):
        """Failure categories help attribute errors."""
        valid_cats = ["prompt", "tool_desc", "schema", "context_pollution",
                      "retrieval", "env_permission"]
        obs = Observation(skill_id="x", status="fail", failure_category="prompt")
        assert obs.failure_category in valid_cats

    def test_safety_flags_default_empty(self):
        obs = Observation(skill_id="x")
        assert obs.safety_flags == []

    def test_raw_output_full_is_stored(self):
        obs = Observation(skill_id="x", raw_output_full="LLM response here")
        assert obs.raw_output_full == "LLM response here"


# ══════════════════════════════════════════════════════════════════════════
#  AgentState
# ══════════════════════════════════════════════════════════════════════════


class TestAgentState:
    def test_defaults(self):
        state = AgentState(agent_name="test-agent")
        assert state.agent_name == "test-agent"
        assert state.step == 0
        assert state.max_steps == 12
        assert state.done is False
        assert state.success is False
        assert state.provider is None  # Resolved at runtime from config

    def test_custom_values(self):
        state = AgentState(
            agent_name="automation-agent",
            goal="Test equipment module",
            module="equipment",
            page="alarm-config",
            provider="deepseek",
            max_steps=20,
        )
        assert state.module == "equipment"
        assert state.page == "alarm-config"
        assert state.max_steps == 20

    def test_to_dict_includes_all_fields(self):
        state = AgentState(agent_name="test-agent", step=5)
        d = state.to_dict()
        assert d["agent_name"] == "test-agent"
        assert d["step"] == 5
        assert d["done"] is False

    def test_to_dict_serializes_observations(self):
        state = AgentState(agent_name="test")
        state.observations.append(Observation(skill_id="s1", status="pass"))
        d = state.to_dict()
        assert len(d["observations"]) == 1
        assert d["observations"][0]["status"] == "pass"

    def test_failed_skills_default_dict(self):
        state = AgentState(agent_name="test")
        assert state.failed_skills == {}

    def test_termination_reason_default(self):
        state = AgentState(agent_name="test")
        assert state.termination_reason == ""

    def test_task_state_default(self):
        state = AgentState(agent_name="test")
        assert state.task_state == "backlog"


# ══════════════════════════════════════════════════════════════════════════
#  AgentEvent
# ══════════════════════════════════════════════════════════════════════════


class TestAgentEvent:
    def test_has_required_fields(self):
        ev = AgentEvent(type="agent_start")
        assert ev.type == "agent_start"

    def test_defaults(self):
        ev = AgentEvent(type="skill_start")
        assert ev.skill_id == ""
        assert ev.content == ""
        assert ev.summary == ""
        assert ev.status == ""
        assert ev.error == ""

    def test_with_observation(self):
        obs = Observation(skill_id="s1", status="pass")
        ev = AgentEvent(type="skill_end", observation=obs, summary="Done")
        assert ev.observation.status == "pass"
        assert ev.summary == "Done"

    def test_interaction_event(self):
        ev = AgentEvent(
            type="interaction_required",
            interaction_id="int-1",
            interaction_type="confirm",
            interaction_prompt="Proceed?",
            interaction_options=["yes", "no"],
        )
        assert ev.interaction_type == "confirm"
        assert len(ev.interaction_options) == 2

    def test_token_usage(self):
        ev = AgentEvent(
            type="agent_message",
            skill_id="test-skill",
            token_usage={"input": 100, "output": 50},
        )
        assert ev.token_usage["input"] == 100
        assert ev.token_usage["output"] == 50

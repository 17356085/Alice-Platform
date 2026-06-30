"""Tests for graphs/state.py — data structures (no graph execution).

Tests: GateResult, SkillObservation, PageResult, AgentResult,
CANONICAL_PHASES, AGENT_PHASE_MAP, MODE_SKIP_MAP,
CommonSOPStage, GateLevel, create_initial_state.
Pure dataclass + constant tests — zero LLM calls.
"""
import pytest

from aitest.graphs.state import (
    GateResult, SkillObservation, PageResult, AgentResult,
    GateLevel, CommonSOPStage, PhaseName, AgentName,
    CANONICAL_PHASES, AGENT_PHASE_MAP, MODE_SKIP_MAP,
    SOPMode, create_initial_state, MAX_PHASE_RETRY_ROUNDS,
)


# ══════════════════════════════════════════════════════════════════════════
#  GateResult
# ══════════════════════════════════════════════════════════════════════════


class TestGateResult:
    def test_ok_gate(self):
        g = GateResult(level=GateLevel.L1_ORCHESTRATOR, phase="Preflight", ok=True)
        assert g.ok is True
        assert g.to_dict()["ok"] is True

    def test_failed_gate(self):
        g = GateResult(level=GateLevel.L2_AGENT, phase="Automation", ok=False,
                       message="Missing page object", details={"missing": ["alarm.py"]})
        d = g.to_dict()
        assert d["ok"] is False
        assert "Missing page object" in d["message"]
        assert "alarm.py" in str(d["details"])

    def test_to_dict_includes_level(self):
        g = GateResult(level=GateLevel.L3_VALIDATOR, phase="Report", ok=True)
        assert g.to_dict()["level"] == "L3_VALIDATOR"


# ══════════════════════════════════════════════════════════════════════════
#  SkillObservation
# ══════════════════════════════════════════════════════════════════════════


class TestSkillObservation:
    def test_defaults(self):
        obs = SkillObservation(skill_id="test-skill")
        assert obs.status == "pending"
        assert obs.suggestion == "continue"

    def test_to_dict(self):
        obs = SkillObservation(
            skill_id="automation/run",
            status="pass",
            artifacts_found=["report.xlsx"],
            summary="All good",
            token_usage={"input": 500, "output": 200},
        )
        d = obs.to_dict()
        assert d["status"] == "pass"
        assert d["artifacts_found"] == ["report.xlsx"]


# ══════════════════════════════════════════════════════════════════════════
#  PageResult
# ══════════════════════════════════════════════════════════════════════════


class TestPageResult:
    def test_defaults(self):
        pr = PageResult(page_slug="alarm-config")
        assert pr.status == "pending"
        assert pr.phases_completed == []
        assert pr.errors == []

    def test_to_dict(self):
        pr = PageResult(
            page_slug="device-list",
            status="completed",
            phases_completed=["Project Init", "Requirement", "Automation"],
            errors=["timeout in Execution"],
        )
        d = pr.to_dict()
        assert d["page_slug"] == "device-list"
        assert len(d["phases_completed"]) == 3
        assert "timeout" in d["errors"][0]


# ══════════════════════════════════════════════════════════════════════════
#  AgentResult
# ══════════════════════════════════════════════════════════════════════════


class TestAgentResult:
    def test_defaults(self):
        ar = AgentResult(agent_name="automation-agent")
        assert ar.success is False
        assert ar.execution_failed is False

    def test_successful_result(self):
        ar = AgentResult(
            agent_name="execution-agent",
            success=True,
            module="equipment",
            step=8,
            completed_skills=["run_pytest", "collect_results"],
        )
        d = ar.to_dict()
        assert d["success"] is True
        assert d["module"] == "equipment"
        assert len(d["completed_skills"]) == 2

    def test_execution_failed_flag(self):
        ar = AgentResult(
            agent_name="execution-agent",
            success=False,
            execution_failed=True,
            termination_reason="pytest returned exit code 1",
        )
        assert ar.execution_failed is True
        d = ar.to_dict()
        assert d["execution_failed"] is True


# ══════════════════════════════════════════════════════════════════════════
#  CANONICAL_PHASES
# ══════════════════════════════════════════════════════════════════════════


class TestCanonicalPhases:
    def test_nine_phases(self):
        assert len(CANONICAL_PHASES) == 9

    def test_starts_with_preflight(self):
        assert CANONICAL_PHASES[0] == "Project Init"

    def test_ends_with_knowledge(self):
        assert CANONICAL_PHASES[-1] == "Knowledge"

    def test_all_are_valid_phase_names(self):
        valid = set(PhaseName.__args__)
        for p in CANONICAL_PHASES:
            assert p in valid, f"{p} not in PhaseName"


# ══════════════════════════════════════════════════════════════════════════
#  AGENT_PHASE_MAP
# ══════════════════════════════════════════════════════════════════════════


class TestAgentPhaseMap:
    def test_all_eight_agents_mapped(self):
        assert len(AGENT_PHASE_MAP) >= 8

    def test_each_agent_has_valid_phase(self):
        valid_phases = set(CANONICAL_PHASES)
        for agent, phase in AGENT_PHASE_MAP.items():
            assert phase in valid_phases, f"{agent}: {phase} not in CANONICAL_PHASES"

    def test_automation_agent_is_automation_phase(self):
        assert AGENT_PHASE_MAP["automation-agent"] == "Automation"

    def test_execution_agent_is_execute_debug(self):
        assert AGENT_PHASE_MAP["execution-agent"] == "Execute & Debug"


# ══════════════════════════════════════════════════════════════════════════
#  MODE_SKIP_MAP
# ══════════════════════════════════════════════════════════════════════════


class TestModeSkipMap:
    def test_full_mode_skips_nothing(self):
        assert MODE_SKIP_MAP["full"] == []

    def test_from_requirement_skips_project_init(self):
        assert "Project Init" in MODE_SKIP_MAP["from-requirement"]

    def test_from_test_design_skips_two(self):
        skipped = MODE_SKIP_MAP["from-test-design"]
        assert "Project Init" in skipped
        assert "Requirement" in skipped

    def test_from_automation_skips_three(self):
        skipped = MODE_SKIP_MAP["from-automation"]
        assert len(skipped) == 3


# ══════════════════════════════════════════════════════════════════════════
#  GateLevel
# ══════════════════════════════════════════════════════════════════════════


class TestGateLevel:
    def test_three_levels(self):
        assert GateLevel.L1_ORCHESTRATOR.value == 1
        assert GateLevel.L2_AGENT.value == 2
        assert GateLevel.L3_VALIDATOR.value == 3


# ══════════════════════════════════════════════════════════════════════════
#  create_initial_state
# ══════════════════════════════════════════════════════════════════════════


class TestCreateInitialState:
    def test_returns_typed_dict(self):
        state = create_initial_state(module="equipment", pages=["alarm"])
        assert state["module"] == "equipment"
        assert state["pages"] == ["alarm"]
        assert state["status"] == "running"

    def test_default_provider(self):
        state = create_initial_state(module="m", pages=["p"])
        assert state["provider"] == "claude"

    def test_custom_provider(self):
        state = create_initial_state(module="m", pages=["p"], provider="deepseek")
        assert state["provider"] == "deepseek"

    def test_default_mode(self):
        state = create_initial_state(module="m", pages=["p"])
        assert state["mode"] == "full"

    def test_empty_phases_on_start(self):
        state = create_initial_state(module="m", pages=["p"])
        assert state["completed_phases"] == []
        assert state["skip_phases"] == []

    def test_max_phase_retry_default(self):
        from aitest.graphs.state import MAX_PHASE_RETRY_ROUNDS
        assert MAX_PHASE_RETRY_ROUNDS == 2

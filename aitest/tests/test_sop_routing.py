"""
LangGraph Routing Smoke Tests — Class 2: 不调 LLM，纯路由逻辑验证。

运行: pytest aitest/tests/test_sop_routing.py -v
       python -m pytest aitest/tests/test_sop_routing.py -v
"""

import os
import sys
import pytest

os.environ["LANGCHAIN_TRACING_V2"] = "false"
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from aitest.graphs.state import (
    create_initial_state,
    CANONICAL_PHASES,
    AGENT_PHASE_MAP,
    MODE_SKIP_MAP,
    AgentResult,
)
from aitest.graphs.sop_graph import route_next_phase, build_sop_graph, PHASE_TO_NODE
from aitest.graphs.checkpoint import get_checkpointer
from aitest.graphs.nodes import make_agent_loop_node


# ═══════════════════════════════════════════════════════════════
#  Route Logic Tests
# ═══════════════════════════════════════════════════════════════

class TestRouteNextPhase:
    """条件路由逻辑 — route_next_phase() 所有路径。"""

    def test_full_mode_starts_at_project_init(self):
        state = create_initial_state("equipment", ["alarm-config", "camera", "key-param", "maintenance"], mode="full")
        assert route_next_phase(state) == "project_agent"

    def test_status_mode_goes_to_exit(self):
        state = create_initial_state("equipment", ["alarm-config", "camera", "key-param", "maintenance"], mode="status")
        assert route_next_phase(state) == "exit"

    def test_fatal_error_goes_to_exit(self):
        state = create_initial_state("equipment", ["alarm-config", "camera", "key-param", "maintenance"], mode="full")
        state["fatal_error"] = "test error"
        assert route_next_phase(state) == "exit"

    def test_skips_completed_phases(self):
        state = create_initial_state("equipment", ["alarm-config", "camera", "key-param", "maintenance"], mode="full")
        state["completed_phases"] = ["Project Init", "Requirement"]
        assert route_next_phase(state) == "test_design_agent"

    def test_from_requirement_skips_project_init(self):
        state = create_initial_state("equipment", ["alarm-config", "camera", "key-param", "maintenance"], mode="from-requirement")
        assert route_next_phase(state) == "requirement_agent"

    def test_from_test_design_skips_first_two(self):
        state = create_initial_state("equipment", ["alarm-config", "camera", "key-param", "maintenance"], mode="from-test-design")
        assert route_next_phase(state) == "test_design_agent"

    def test_from_automation_skips_first_three(self):
        state = create_initial_state("equipment", ["alarm-config", "camera", "key-param", "maintenance"], mode="from-automation")
        # P1-3 HITL: equipment 在 P0 模块白名单中时，需要先走 testcase_approval
        # 设置 test_cases_approved 绕过审批直接进入 automation
        state["test_cases_approved"] = True
        assert route_next_phase(state) == "automation_agent_pre"

    def test_execution_failed_triggers_bug_analysis(self):
        state = create_initial_state("equipment", ["alarm-config", "camera", "key-param", "maintenance"], mode="full")
        state["completed_phases"] = [
            "Project Init", "Requirement", "Test Design", "Automation", "Execute & Debug"
        ]
        state["agent_outputs"] = {"execution_failed": True}
        assert route_next_phase(state) == "bug_analysis_agent"

    def test_execution_passed_skips_bug_analysis(self):
        state = create_initial_state("equipment", ["alarm-config", "camera", "key-param", "maintenance"], mode="full")
        state["completed_phases"] = [
            "Project Init", "Requirement", "Test Design", "Automation", "Execute & Debug"
        ]
        state["agent_outputs"] = {"execution-agent": {"success": True}}
        # Phase chain: execution → data_sanitization → report (per v2.1 agent routing)
        assert route_next_phase(state) in ("report_agent", "data_sanitization_agent")

    def test_agent_result_execution_failed_triggers_bug_analysis(self):
        """P2-4: AgentResult.execution_failed 标志。"""
        state = create_initial_state("equipment", ["alarm-config", "camera", "key-param", "maintenance"], mode="full")
        state["completed_phases"] = [
            "Project Init", "Requirement", "Test Design", "Automation", "Execute & Debug"
        ]
        state["agent_outputs"] = {
            "execution-agent": AgentResult(
                agent_name="execution-agent", success=False, execution_failed=True
            ).to_dict()
        }
        assert route_next_phase(state) == "bug_analysis_agent"

    def test_all_completed_goes_to_exit(self):
        state = create_initial_state("equipment", ["alarm-config", "camera", "key-param", "maintenance"], mode="full")
        state["completed_phases"] = list(CANONICAL_PHASES)
        assert route_next_phase(state) == "exit"


# ═══════════════════════════════════════════════════════════════
#  Graph Structure Tests
# ═══════════════════════════════════════════════════════════════

class TestGraphStructure:
    """图结构完整性。"""

    def test_all_agent_nodes_present(self):
        builder = build_sop_graph()
        nodes = set(builder.nodes.keys())
        for phase, node_name in PHASE_TO_NODE.items():
            assert node_name in nodes, f"Missing node: {node_name}"
        assert "entry" in nodes
        assert "preflight" in nodes
        assert "exit" in nodes

    def test_graph_compiles(self):
        builder = build_sop_graph()
        checkpointer = get_checkpointer()
        compiled = builder.compile(checkpointer=checkpointer)
        assert compiled is not None

    def test_all_phases_have_node_mapping(self):
        for phase in CANONICAL_PHASES:
            assert phase in PHASE_TO_NODE, f"Missing phase mapping: {phase}"


# ═══════════════════════════════════════════════════════════════
#  AgentLoop Node Tests
# ═══════════════════════════════════════════════════════════════

class TestAgentLoopNode:
    """AgentLoop 节点工厂。"""

    def test_creates_named_node(self):
        for agent_name in ["project-agent", "requirement-agent", "test-design-agent", "automation-agent"]:
            node = make_agent_loop_node(agent_name)
            assert callable(node)
            assert agent_name.replace("-", "_") in node.__name__

    def test_all_agents_have_node(self):
        for agent_name in AGENT_PHASE_MAP:
            node = make_agent_loop_node(agent_name)
            assert callable(node)


# ═══════════════════════════════════════════════════════════════
#  State Tests
# ═══════════════════════════════════════════════════════════════

class TestState:
    """状态对象。"""

    def test_create_initial_state_has_required_fields(self):
        state = create_initial_state("equipment", ["alarm-config", "camera", "key-param", "maintenance"])
        required = ["module", "pages", "mode", "provider", "run_id", "status"]
        for field in required:
            assert field in state, f"Missing field: {field}"
        assert state["module"] == "equipment"
        assert state["pages"] == ["alarm-config", "camera", "key-param", "maintenance"]
        assert state["mode"] == "full"
        assert state["status"] == "running"

    def test_mode_skip_map_integrity(self):
        assert MODE_SKIP_MAP["full"] == []
        assert MODE_SKIP_MAP["resume"] == []
        assert MODE_SKIP_MAP["from-requirement"] == ["Project Init"]
        assert MODE_SKIP_MAP["from-test-design"] == ["Project Init", "Requirement"]
        assert MODE_SKIP_MAP["from-automation"] == ["Project Init", "Requirement", "Test Design"]

    def test_agent_result_to_dict(self):
        ar = AgentResult(
            agent_name="test-agent",
            success=True,
            completed_skills=["a", "b"],
            failed_skills={"c": "error"},
            execution_failed=False,
        )
        d = ar.to_dict()
        assert d["agent_name"] == "test-agent"
        assert d["success"] is True
        assert d["completed_skills"] == ["a", "b"]
        assert d["execution_failed"] is False


# ═══════════════════════════════════════════════════════════════
#  Preflight Tests (pass-through, no LLM)
# ═══════════════════════════════════════════════════════════════

class TestPreflight:
    """Preflight 节点 — 产物扫描。"""

    @pytest.mark.skip(reason="Requires configured test project with code_path — run with project set")
    def test_preflight_discovers_pages(self):
        from aitest.graphs.sop_graph import preflight_node
        state = create_initial_state("equipment", [], mode="full")
        result = preflight_node(state)
        assert "pages" in result
        assert len(result["pages"]) > 0

    @pytest.mark.skip(reason="Requires configured test project — run with project set")
    def test_preflight_recommends_mode(self):
        from aitest.graphs.sop_graph import preflight_node
        state = create_initial_state("equipment", ["alarm-config"], mode="full")
        result = preflight_node(state)
        auto = result["agent_outputs"]["preflight_auto_detect"]
        assert "recommended_mode" in auto
        assert auto["has_project"] is True  # PROJECT_CONTEXT.md 应该存在

    def test_preflight_never_recommends_status(self):
        """preflight 不应自动推荐 status 模式——只有用户显式指定才用。"""
        from aitest.graphs.sop_graph import preflight_node
        state = create_initial_state("equipment", ["alarm-config", "camera", "key-param", "maintenance"], mode="full")
        result = preflight_node(state)
        auto = result["agent_outputs"]["preflight_auto_detect"]
        assert auto["recommended_mode"] != "status", (
            "preflight should never auto-recommend status mode. "
            "status mode skips execution; only user should opt into that."
        )

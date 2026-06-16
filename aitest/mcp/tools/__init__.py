"""
Tool Registry — 所有 MCP Tool 的注册表。
新增 Tool: 在此文件的 _build_registry() 中添加一行 _ToolDef 即可。
"""
from aitest.mcp.tools.registry import ToolDef
from aitest.mcp.rate_limit import ToolPermission

# 导入所有 handler
from aitest.mcp.tools.quality import run_code_quality_check
from aitest.mcp.tools.knowledge import search_known_issues, rag_search_with_sampling
from aitest.mcp.tools.status import get_module_status, get_automation_coverage
from aitest.mcp.tools.agents import run_agent_tool
from aitest.mcp.tools.execution import run_pytest, run_sop_handler
from aitest.mcp.tools.consistency import run_consistency_check
from aitest.mcp.tools.management import cancel_task_handler, list_tasks_handler
from aitest.mcp.tools.gate_checker import check_sop_gate


def _build_registry() -> dict[str, ToolDef]:
    """构建 Tool 注册表。每项包含 P3-2 元数据。"""
    return {
        # ── READ: 只读查询 ──
        "check_code_quality": ToolDef(
            name="check_code_quality",
            description="Run code quality scanner against 8 code redline rules",
            schema={"type": "object", "properties": {
                "target": {"type": "string", "description": "File path or leave empty for all"},
                "staged": {"type": "boolean", "description": "Only check git staged files"},
            }},
            handler=lambda args: run_code_quality_check(
                target=args.get("target", ""), staged=args.get("staged", False)),
            permission=ToolPermission.READ, produces=["code_quality_report"],
            side_effect="read", estimated_duration="10s",
        ),
        "search_known_issues": ToolDef(
            name="search_known_issues",
            description="Search known Element Plus pitfalls / failure patterns from known-issues.yaml. P3-4: supports offset/limit pagination.",
            schema={"type": "object", "properties": {
                "query": {"type": "string", "description": "Search keyword"},
                "category": {"type": "string", "enum": ["element-plus", "failure-pattern", "environment"]},
                "component": {"type": "string", "description": "e.g. el-select, el-dialog"},
                "severity": {"type": "string", "enum": ["high", "medium", "low"]},
                "offset": {"type": "integer", "description": "Pagination offset (default 0)", "default": 0},
                "limit": {"type": "integer", "description": "Results per page (default 50, 0=unlimited)", "default": 50},
            }},
            handler=lambda args: search_known_issues(
                query=args.get("query", ""), category=args.get("category", ""),
                component=args.get("component", ""), severity=args.get("severity", ""),
                offset=args.get("offset", 0), limit=args.get("limit", 50)),
            permission=ToolPermission.READ, produces=["known_issue_list"],
            side_effect="read", estimated_duration="1s",
        ),
        "get_module_status": ToolDef(
            name="get_module_status",
            description="Query module SOP phase status and document completeness",
            schema={"type": "object", "properties": {
                "module_name": {"type": "string", "description": "Module name or ID"},
            }},
            handler=lambda args: get_module_status(module_name=args.get("module_name", "")),
            permission=ToolPermission.READ, depends_on=["MODULE_INDEX.md"],
            produces=["module_status"], side_effect="read", estimated_duration="1s",
        ),
        "get_automation_coverage": ToolDef(
            name="get_automation_coverage",
            description="Get automation code coverage: PageObject + test script counts",
            schema={"type": "object", "properties": {
                "module_name": {"type": "string", "description": "Module filter"},
            }},
            handler=lambda args: get_automation_coverage(module_name=args.get("module_name", "")),
            permission=ToolPermission.READ, produces=["coverage_stats"],
            side_effect="read", estimated_duration="2s",
        ),
        "rag_search_known_issues": ToolDef(
            name="rag_search_known_issues",
            description="RAG vector search known issues for bug-analysis auto-matching. P2-1: When results >3 and client supports sampling, LLM reranks.",
            schema={"type": "object", "properties": {
                "query": {"type": "string", "description": "Error description"},
                "n_results": {"type": "integer", "description": "Result count (default 5)", "default": 5},
                "use_sampling": {"type": "boolean", "description": "Enable LLM sampling (default true)", "default": True},
            }, "required": ["query"]},
            handler=lambda args: rag_search_with_sampling(
                query=args.get("query", ""), n_results=args.get("n_results", 5),
                use_sampling=args.get("use_sampling", True)),
            permission=ToolPermission.READ, depends_on=["ChromaDB index"],
            produces=["rag_matches"], side_effect="read", estimated_duration="2s",
        ),
        "check_consistency": ToolDef(
            name="check_consistency",
            description="Run cross-layer consistency checks (agent-skill sync, skill files, registry completeness, page interface freshness, deprecated skill refs, regression baselines) — ZERO LLM cost.",
            schema={"type": "object", "properties": {}},
            handler=lambda args: run_consistency_check(),
            permission=ToolPermission.READ, produces=["consistency_report"],
            side_effect="read", estimated_duration="3s",
        ),
        "check_sop_gate": ToolDef(
            name="check_sop_gate",
            description="P3-3: Run SOP gate check before Agent execution. Returns gate pass/blocked with missing prerequisites.",
            schema={"type": "object", "properties": {
                "module": {"type": "string", "description": "Module name"},
                "agent": {"type": "string", "description": "Agent name (e.g. automation-agent, test-design-agent)"},
            }, "required": ["module"]},
            handler=lambda args: check_sop_gate(
                module=args.get("module", ""), agent=args.get("agent", "")),
            permission=ToolPermission.READ, depends_on=["MODULE_CONTEXT.md"],
            produces=["gate_status"], side_effect="read", estimated_duration="2s",
        ),
        "list_tasks": ToolDef(
            name="list_tasks",
            description="List all currently running long tasks with elapsed time and cancellation status",
            schema={"type": "object", "properties": {}},
            handler=lambda args: list_tasks_handler(),
            permission=ToolPermission.READ, produces=["task_list"],
            side_effect="read", estimated_duration="1s",
        ),

        # ── WRITE: 状态修改 ──
        "cancel_task": ToolDef(
            name="cancel_task",
            description="Cancel a running long task (run_sop, run_pytest) by tool name prefix.",
            schema={"type": "object", "properties": {
                "tool_name": {"type": "string", "description": "Tool name: 'run_sop' or 'run_pytest'"},
            }, "required": ["tool_name"]},
            handler=lambda args: cancel_task_handler(args.get("tool_name", "")),
            permission=ToolPermission.WRITE, depends_on=["list_tasks"],
            produces=["cancellation_result"], side_effect="write", estimated_duration="1s",
        ),

        # ── EXECUTE: 执行外部进程/Agent ──
        "run_test_design_agent": ToolDef(
            name="run_test_design_agent",
            description="Execute test-design agent: page analysis -> risk modeling -> test case design.",
            schema={"type": "object", "properties": {
                "module": {"type": "string", "description": "Module name"},
                "page": {"type": "string", "description": "Page slug"},
                "execute": {"type": "boolean", "description": "Actually execute (false=dry run)", "default": True},
            }, "required": ["module", "page"]},
            handler=lambda args: run_agent_tool("test-design-agent", args),
            permission=ToolPermission.EXECUTE, depends_on=["MODULE_CONTEXT.md"],
            produces=["PAGE_CONTEXT.md", "RISK_MODEL.md", "TEST_CASES.md"],
            side_effect="execute", estimated_duration="3min",
        ),
        "run_automation_agent": ToolDef(
            name="run_automation_agent",
            description="Execute automation agent: tech analysis -> PageObject -> test scripts -> code check.",
            schema={"type": "object", "properties": {
                "module": {"type": "string", "description": "Module name"},
                "page": {"type": "string", "description": "Page slug"},
                "execute": {"type": "boolean", "description": "Actually execute (false=dry run)", "default": True},
            }, "required": ["module", "page"]},
            handler=lambda args: run_agent_tool("automation-agent", args),
            permission=ToolPermission.EXECUTE,
            depends_on=["PAGE_CONTEXT.md", "TEST_CASES.md", "check_sop_gate"],
            produces=["PageObject.py", "test_*.py"], side_effect="execute",
            estimated_duration="5min",
        ),
        "run_sop": ToolDef(
            name="run_sop",
            description="End-to-end SOP orchestrator: 8 Agent pipeline with LangGraph engine. Supports resume, HITL, auto bug-fix loop.",
            schema={"type": "object", "properties": {
                "module": {"type": "string", "description": "Module name"},
                "mode": {"type": "string", "enum": ["full", "resume", "status", "from-requirement",
                          "from-test-design", "from-automation"], "default": "full"},
                "pages": {"type": "string", "description": "Page slug list (comma-separated)"},
                "provider": {"type": "string", "enum": ["claude", "openai", "ollama"], "default": "claude"},
            }, "required": ["module"]},
            handler=run_sop_handler,
            permission=ToolPermission.EXECUTE,
            depends_on=["check_sop_gate", "get_module_status"],
            produces=["all_artifacts"], side_effect="execute",
            estimated_duration="10-20min",
        ),
        "run_pytest": ToolDef(
            name="run_pytest",
            description="Run pytest tests for a module and return structured results. Supports cancellation via cancel_task.",
            schema={"type": "object", "properties": {
                "module": {"type": "string", "description": "Module name (required)"},
                "marker": {"type": "string", "description": "pytest marker: smoke, integration, destructive"},
                "parallel": {"type": "integer", "description": "Parallel workers (1=serial)", "default": 1},
                "test_file": {"type": "string", "description": "Specific test file name"},
                "timeout": {"type": "integer", "description": "Max execution seconds (default 300)", "default": 300},
            }, "required": ["module"]},
            handler=lambda args: run_pytest(
                module=args.get("module", ""), marker=args.get("marker", ""),
                parallel=args.get("parallel", 1), test_file=args.get("test_file", ""),
                timeout=args.get("timeout", 300)),
            permission=ToolPermission.EXECUTE,
            depends_on=["test_*.py files exist", "check_sop_gate"],
            produces=["test_results", "allure_results"], side_effect="execute",
            estimated_duration="2min",
        ),
    }


# 全局注册表（单例）
TOOL_REGISTRY: dict[str, ToolDef] = _build_registry()

# 向后兼容别名
TOOL_ALIASES = {"run_full_sop": "run_sop", "run_sop_graph": "run_sop"}

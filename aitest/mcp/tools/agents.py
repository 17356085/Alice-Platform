"""Tools: run_test_design_agent + run_automation_agent。"""
from aitest.mcp.config import CONTEXT_MODULES, ZJSN_TEST
from aitest.mcp.error_taxonomy import ErrorCode, error_response, success_response
from aitest.agent_runner import AgentLoop


def _check_agent_preconditions(agent_name: str, module: str, page: str = "") -> dict:
    """检查 Agent 执行的前置条件。"""
    missing = []
    module_dir = CONTEXT_MODULES / module

    if agent_name == "test-design-agent":
        if not (module_dir / "MODULE_CONTEXT.md").exists():
            missing.append("MODULE_CONTEXT.md")

    elif agent_name == "automation-agent":
        if page:
            page_dir = module_dir / "pages" / page
            if not page_dir.exists():
                missing.append(f"pages/{page}/ (目录不存在)")
            else:
                for doc in ["PAGE_CONTEXT.md", "TEST_CASES.md"]:
                    if not (page_dir / doc).exists():
                        missing.append(f"pages/{page}/{doc}")

    if missing:
        return {
            "status": "blocked",
            "agent": agent_name,
            "module": module,
            "page": page,
            "missing_prerequisites": missing,
            "suggestion": f"请先完成前置步骤。使用 run_sop module={module} 从头开始。",
        }
    return {"status": "ready", "agent": agent_name, "module": module, "page": page}


def run_agent_tool(agent_name: str, arguments: dict) -> dict:
    """通用 Agent 执行 Tool。"""
    module = arguments.get("module", "")
    page = arguments.get("page", "")
    execute = arguments.get("execute", True)

    precond = _check_agent_preconditions(agent_name, module, page)
    if precond["status"] == "blocked":
        return error_response(
            ErrorCode.PRECONDITION_FAILED,
            f"Agent '{agent_name}' 前置条件未满足",
            precond.get("suggestion", "请先完成前置步骤"),
            retryable=False,
            missing_prerequisites=precond.get("missing_prerequisites", []),
        )

    if not execute:
        return success_response({"status": "ready", "agent": agent_name, "module": module,
                                 "page": page, "mode": "dry_run"})

    try:
        agent = AgentLoop(agent_name, module=module, page=page, verbose=False)
        state = agent.run()
        return success_response({"status": "executed", "agent": agent_name, "module": module,
                                 "page": page, "execution_result": state.to_dict()})
    except Exception as e:
        return error_response(
            ErrorCode.EXECUTION_FAILED,
            f"Agent '{agent_name}' 执行失败: {str(e)}",
            "检查前置文档是否完整，或使用 run_sop 从头编排。",
            retryable=True, agent=agent_name, module=module, page=page,
        )

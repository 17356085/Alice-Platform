"""Tools: run_pytest + run_sop (LangGraph orchestrator)。"""
import traceback as _traceback

from aitest.testing import run_pytest
from aitest.mcp.config import CONTEXT_MODULES
from aitest.mcp.error_taxonomy import ErrorCode, error_response
from aitest.mcp.cancellation import register_task, deregister_task
from aitest.mcp.tools.status import get_module_status


def run_sop_handler(arguments: dict) -> dict:
    """统一 SOP 编排 — LangGraph 引擎。P2-4: 支持取消。"""
    module = arguments.get("module", "")
    mode = arguments.get("mode", "full")
    pages_str = arguments.get("pages", "")
    provider = arguments.get("provider", "claude")
    pages = [p.strip() for p in pages_str.split(",") if p.strip()] if pages_str else []

    if mode == "status":
        result = get_module_status(module)
        result["mode"] = "status"
        return result

    task_handle = register_task("run_sop")

    try:
        from aitest.graphs.state import create_initial_state
        from aitest.graphs.checkpoint import get_checkpointer
        from alice_engine.workflow.sop_graph import build_sop_graph

        initial_state = create_initial_state(module=module, pages=pages, mode=mode, provider=provider)
        checkpointer = get_checkpointer()
        graph = build_sop_graph()
        compiled = graph.compile(checkpointer=checkpointer)
        thread = {"configurable": {"thread_id": initial_state["run_id"]}}

        events = []
        from langgraph.types import Command
        state_stream = initial_state
        for event in compiled.stream(state_stream, thread, stream_mode="updates"):
            if task_handle.is_cancelled():
                deregister_task(task_handle.task_id)
                return error_response(
                    ErrorCode.EXECUTION_FAILED,
                    f"run_sop cancelled (task {task_handle.task_id})",
                    f"SOP 已中断于 {events[-1]['phase'] if events else 'initial'} 阶段。使用 run_sop mode=resume 续跑。",
                    retryable=True,
                    cancelled_task_id=task_handle.task_id,
                    completed_phases_before_cancel=[e.get("phase") for e in events],
                )
            if "__interrupt__" in event:
                state_stream = Command(resume="approve")
                continue
            for node_name, update in event.items():
                if isinstance(update, dict):
                    events.append({"node": node_name, "phase": update.get("current_phase", ""),
                                   "completed": update.get("completed_phases", [])})

        deregister_task(task_handle.task_id)
        final = compiled.get_state(thread)
        return {
            "status": final.values.get("status", "completed") if final and final.values else "completed",
            "module": module, "mode": mode, "engine": "langgraph",
            "run_id": initial_state["run_id"], "events": events[-10:],
            "completed_phases": final.values.get("completed_phases", []) if final and final.values else [],
        }
    except Exception as e:
        deregister_task(task_handle.task_id)
        tb = _traceback.format_exc()[-500:]
        return error_response(
            ErrorCode.EXECUTION_FAILED, f"run_sop failed: {str(e)}",
            f"检查模块 '{module}' 的前置文档是否完整。可使用 get_module_status module_name={module} 诊断。",
            retryable=True, module=module, mode=mode, traceback=tb,
        )

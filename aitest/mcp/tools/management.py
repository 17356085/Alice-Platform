"""Tools: cancel_task + list_tasks (P2-4)。"""
from aitest.mcp.error_taxonomy import ErrorCode, error_response
from aitest.mcp.cancellation import cancel_task_by_prefix, list_running_tasks


def cancel_task_handler(tool_name: str) -> dict:
    """取消运行中的长任务。"""
    if not tool_name:
        return error_response(
            ErrorCode.INVALID_PARAMS, "tool_name is required",
            "指定要取消的 Tool: 'run_sop' 或 'run_pytest'。使用 list_tasks 查看运行中的任务。",
        )

    count = cancel_task_by_prefix(tool_name)
    if count == 0:
        return {
            "status": "ok", "cancelled_count": 0,
            "message": f"No running tasks matched '{tool_name}'. Use list_tasks to see active tasks.",
            "running_tasks": list_running_tasks(),
        }

    return {
        "status": "ok", "cancelled_count": count,
        "message": f"Cancelled {count} task(s) matching '{tool_name}'",
        "remaining_tasks": list_running_tasks(),
    }


def list_tasks_handler() -> dict:
    """列出所有运行中的长任务。"""
    return {"status": "ok", "running_tasks": list_running_tasks()}

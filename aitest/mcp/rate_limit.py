"""
P2-2: Tool Auth — 权限分级 + 速率控制
滑动窗口限流，per-tool 粒度，按权限等级配置上限。
"""
import enum
import time as _time_module
from collections import defaultdict


class ToolPermission(enum.Enum):
    """Tool 权限等级。"""
    READ = "read"        # 只读，无副作用，高频安全
    WRITE = "write"      # 修改状态（取消任务等）
    EXECUTE = "execute"  # 执行外部进程/Agent，副作用大


# 每 Tool 的权限定义
TOOL_PERMISSIONS: dict[str, ToolPermission] = {
    "check_code_quality": ToolPermission.READ,
    "search_known_issues": ToolPermission.READ,
    "get_module_status": ToolPermission.READ,
    "get_automation_coverage": ToolPermission.READ,
    "rag_search_known_issues": ToolPermission.READ,
    "check_consistency": ToolPermission.READ,
    "check_sop_gate": ToolPermission.READ,
    "list_tasks": ToolPermission.READ,
    "cancel_task": ToolPermission.WRITE,
    "run_test_design_agent": ToolPermission.EXECUTE,
    "run_automation_agent": ToolPermission.EXECUTE,
    "run_sop": ToolPermission.EXECUTE,
    "run_pytest": ToolPermission.EXECUTE,
}

# 每权限等级的速率限制 (calls per 60s window)
RATE_LIMITS: dict[ToolPermission, int] = {
    ToolPermission.READ: 30,
    ToolPermission.WRITE: 10,
    ToolPermission.EXECUTE: 5,
}

# 速率限制状态: tool_name → list of timestamps (sliding window)
_rate_limit_state: dict[str, list[float]] = defaultdict(list)
RATE_WINDOW_SECONDS = 60


def check_rate_limit(tool_name: str) -> tuple[bool, str]:
    """检查指定 Tool 是否超出速率限制。返回 (allowed, message)。"""
    perm = TOOL_PERMISSIONS.get(tool_name, ToolPermission.READ)
    limit = RATE_LIMITS.get(perm, 30)

    now = _time_module.time()
    window_start = now - RATE_WINDOW_SECONDS

    # 清理过期记录
    timestamps = _rate_limit_state[tool_name]
    _rate_limit_state[tool_name] = [t for t in timestamps if t > window_start]

    current_count = len(_rate_limit_state[tool_name])
    if current_count >= limit:
        oldest = min(_rate_limit_state[tool_name]) if _rate_limit_state[tool_name] else now
        retry_after = round(oldest + RATE_WINDOW_SECONDS - now, 1)
        return False, (
            f"Rate limit exceeded for '{tool_name}' ({perm.value} tier: {limit}/min). "
            f"{current_count} calls in the last {RATE_WINDOW_SECONDS}s. Retry in {retry_after}s."
        )

    # 记录本次调用
    _rate_limit_state[tool_name].append(now)
    return True, ""

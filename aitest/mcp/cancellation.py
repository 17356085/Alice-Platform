"""
P2-4: 长任务 Cancellation — 任务注册表 + asyncio.Event 中断信号
支持 run_sop / run_pytest 等长任务的取消。
"""
import asyncio
import time
import uuid
from dataclasses import dataclass, field


@dataclass
class TaskHandle:
    """可取消任务的句柄。"""
    task_id: str
    tool_name: str
    started_at: float
    cancel_event: asyncio.Event = field(default_factory=asyncio.Event)

    def is_cancelled(self) -> bool:
        return self.cancel_event.is_set()

    def signal_cancel(self) -> None:
        self.cancel_event.set()


# 全局任务注册表：task_id → TaskHandle
_RUNNING_TASKS: dict[str, TaskHandle] = {}


def register_task(tool_name: str) -> TaskHandle:
    """注册一个可取消的长任务。返回句柄。"""
    task_id = f"{tool_name}-{uuid.uuid4().hex[:8]}"
    handle = TaskHandle(task_id=task_id, tool_name=tool_name, started_at=time.time())
    _RUNNING_TASKS[task_id] = handle
    return handle


def deregister_task(task_id: str) -> None:
    """注销已完成/已取消的任务。"""
    _RUNNING_TASKS.pop(task_id, None)


def cancel_task_by_prefix(tool_name: str) -> int:
    """按 Tool 名称前缀取消所有匹配的运行中任务。返回取消数量。"""
    count = 0
    for tid, handle in list(_RUNNING_TASKS.items()):
        if handle.tool_name == tool_name or handle.tool_name.startswith(tool_name):
            handle.signal_cancel()
            count += 1
    return count


def list_running_tasks() -> list[dict]:
    """列出所有运行中的任务。"""
    return [
        {
            "task_id": h.task_id,
            "tool_name": h.tool_name,
            "elapsed_seconds": round(time.time() - h.started_at, 1),
            "cancelled": h.is_cancelled(),
        }
        for h in _RUNNING_TASKS.values()
    ]

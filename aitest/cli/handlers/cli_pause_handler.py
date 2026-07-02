"""
CLI Pause Handler — 处理 HITL 中断。

在 CLI 模式下，拦截 pause.json 事件，显示交互提示，等待用户输入。
"""

import json
import time
import threading
import logging
from pathlib import Path
from typing import Optional

from rich.console import Console

console = Console()
logger = logging.getLogger(__name__)


class CLIPauseHandler:
    """CLI 模式下的暂停处理器。"""

    def __init__(self):
        self._pause_events: dict[str, threading.Event] = {}
        self._pause_data: dict[str, dict] = {}
        self._resume_events: dict[str, threading.Event] = {}

    def on_pause(self, event: dict):
        """处理暂停事件。"""
        task_id = event.get("task_id", "")
        reason = event.get("reason", "")
        skill_id = event.get("skill_id", "")
        risk_level = event.get("risk_level", "high")

        console.print(f"\n[bold yellow]⏸️  HITL 暂停[/bold yellow]")
        console.print(f"  任务: {task_id}")
        console.print(f"  原因: {reason}")
        console.print(f"  Skill: {skill_id}")
        console.print(f"  风险级别: {risk_level}")

        console.print()
        console.print("  [bold]操作:[/bold]")
        console.print("    [cyan]Enter[/cyan] 确认继续")
        console.print("    [cyan]s[/cyan] 跳过此 Skill")
        console.print("    [cyan]a[/cyan] 中止执行")

        # 等待用户输入
        while True:
            choice = input("> ").strip().lower()

            if choice == "" or choice == "enter":
                # 确认继续
                self._write_resume(task_id)
                console.print("[green]✅ 已确认，继续执行[/green]")
                return
            elif choice == "s":
                # 跳过
                self._write_resume(task_id, skip=True)
                console.print("[yellow]⏭️  已跳过[/yellow]")
                return
            elif choice == "a":
                # 中止
                self._write_resume(task_id, abort=True)
                console.print("[red]🛑 已中止[/red]")
                return
            else:
                console.print("[yellow]⚠️  无效输入，请重试[/yellow]")

    def _write_resume(self, task_id: str, skip: bool = False, abort: bool = False):
        """写入 resume.json 文件。"""
        from aitest.infra.pause_handler import write_resume_file

        try:
            write_resume_file(task_id)
        except Exception as e:
            logger.error(f"Failed to write resume file: {e}")


# 全局实例
_cli_pause_handler: Optional[CLIPauseHandler] = None


def get_cli_pause_handler() -> CLIPauseHandler:
    """获取全局 CLI 暂停处理器。"""
    global _cli_pause_handler
    if _cli_pause_handler is None:
        _cli_pause_handler = CLIPauseHandler()
    return _cli_pause_handler

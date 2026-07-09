"""server worker 命令 — 启动独立执行 worker。"""

from __future__ import annotations

import time

from rich.console import Console
from aitest.cli.core.composition import get_cli_execution_service
from aitest.platform.execution_worker import get_execution_worker

console = Console()


def worker_command(
    worker_id: str = "",
    poll_interval: float = 1.0,
):
    """启动独立执行 worker，消费 execution_requests。"""
    worker = get_execution_worker(
        service=get_cli_execution_service(),
        worker_id=worker_id,
        poll_interval=poll_interval,
    )
    worker.start()
    console.print(f"[bold green]Execution worker started[/bold green] ({worker.worker_id})")
    console.print("  Polling execution_requests table ...")
    console.print("  Stop: Ctrl+C")

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        console.print("\n[yellow]Stopping worker...[/yellow]")
    finally:
        worker.stop()
        console.print("[green]Worker stopped[/green]")

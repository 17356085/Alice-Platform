"""server status 命令 — 查看工作台状态。"""

from rich.console import Console
from rich.table import Table

console = Console()


def status_command():
    """查看工作台状态。"""
    from aitest.cli.adapters.server_adapter import ServerAdapter

    adapter = ServerAdapter()
    result = adapter.status()

    status = result.get("status", "unknown")
    pid = result.get("pid")
    port = result.get("port", 8000)
    host = result.get("host", "0.0.0.0")

    status_map = {
        "running": ("[green]RUNNING[/green]", "green"),
        "stopped": ("[dim]STOPPED[/dim]", "dim"),
        "stale_pid": ("[yellow]STALE_PID[/yellow]", "yellow"),
        "external_process": ("[yellow]EXTERNAL[/yellow]", "yellow"),
    }

    status_text, style = status_map.get(status, (f"[dim]{status}[/dim]", "dim"))

    table = Table(title="工作台状态")
    table.add_column("属性", style="bold")
    table.add_column("值")

    table.add_row("状态", status_text)
    table.add_row("地址", f"{host}:{port}")
    if pid:
        table.add_row("PID", str(pid))

    console.print(table)

    if status == "running":
        console.print(f"\n  访问: http://localhost:{port}/chat")
    elif status == "stopped":
        console.print("\n  启动: alice server start")

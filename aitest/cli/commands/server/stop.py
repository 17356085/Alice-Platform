"""server stop 命令 — 停止测试工作台。"""

from rich.console import Console

console = Console()


def stop_command():
    """停止测试工作台。"""
    from aitest.cli.adapters.server_adapter import ServerAdapter

    adapter = ServerAdapter()

    try:
        result = adapter.stop()
        console.print(f"[green]工作台已停止 (PID: {result.get('pid')})[/green]")
    except RuntimeError as e:
        console.print(f"[red]{e}[/red]")

"""server start 命令 — 启动测试工作台。

支持前台和后台两种模式:
  - 前台: Ctrl+C 停止 (默认)
  - 后台: --daemon, alice server stop 停止
"""

from rich.console import Console

console = Console()


def start_command(
    host: str = "0.0.0.0",
    port: int = 8000,
    daemon: bool = False,
    reload: bool = False,
):
    """启动测试工作台。"""
    from aitest.cli.adapters.server_adapter import ServerAdapter, _is_port_in_use

    if _is_port_in_use(port, "localhost"):
        console.print(f"[red]端口 {port} 已被占用[/red]")
        console.print("  使用 --port 指定其他端口，或 alice server stop 停止现有服务")
        return

    adapter = ServerAdapter(host=host, port=port)

    if daemon:
        console.print("[bold]启动工作台 (后台模式)...[/bold]")
    else:
        console.print("[bold]启动工作台 (前台模式，Ctrl+C 停止)...[/bold]")

    try:
        result = adapter.start(daemon=daemon, reload=reload)
        if daemon:
            console.print("[green]工作台已启动[/green]")
            console.print(f"  PID: {result.get('pid')}")
            console.print(f"  地址: {host}:{port}")
            console.print(f"  停止: alice server stop")
            console.print(f"  访问: http://localhost:{port}/chat")
    except RuntimeError as e:
        console.print(f"[red]{e}[/red]")

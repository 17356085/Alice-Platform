"""project register 命令 — 注册新项目。"""

from rich.console import Console

console = Console()


def register_command(path: str):
    """注册新项目。"""
    from aitest.cli.config import CLIConfig
    from aitest.cli.context import CLIContext

    config = CLIConfig()
    ctx = CLIContext(config)
    adapter = ctx.get_project_adapter()

    try:
        result = adapter.register_project(path)
        console.print(f"[green][OK] 项目已注册: {result['id']}[/green]")
        console.print(f"  名称: {result.get('name', '')}")
        console.print(f"  路径: {result.get('path', '')}")
    except ValueError as e:
        console.print(f"[red][FAIL] {e}[/red]")

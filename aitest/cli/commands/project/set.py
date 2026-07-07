"""project set 命令 — 切换活跃项目。"""

from rich.console import Console

console = Console()


def set_command(project_id: str):
    """切换活跃项目。"""
    from aitest.cli.config import CLIConfig
    from aitest.cli.context import CLIContext

    config = CLIConfig()
    ctx = CLIContext(config)
    adapter = ctx.get_project_adapter()

    try:
        adapter.set_active_project(project_id)
        console.print(f"[green]活跃项目已切换为: {project_id}[/green]")
    except ValueError as e:
        console.print(f"[red]{e}[/red]")

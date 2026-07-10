"""project set 命令 — 切换活跃项目。

支持特殊别名:
    "-": 切换到上一个项目
"""

from rich.console import Console

console = Console()


def set_command(project_id: str):
    """切换活跃项目。

    示例:
        aitest project set --id=my-project
        aitest project set --id=-  # 切换到上一个项目
    """
    from aitest.cli.config import CLIConfig
    from aitest.cli.context import CLIContext

    config = CLIConfig()
    ctx = CLIContext(config)
    adapter = ctx.get_project_adapter()

    try:
        actual_id = adapter.set_active_project(project_id)

        # 显示切换信息
        if project_id == "-":
            console.print(f"[green]✓ 已切换回上一个项目: {actual_id}[/green]")
        else:
            console.print(f"[green]✓ 活跃项目已切换为: {actual_id}[/green]")

        # 显示最近使用的项目
        recent = config.recent_projects
        if len(recent) > 1:
            console.print("\n[dim]最近使用的项目:[/dim]")
            for i, pid in enumerate(recent[:3], 1):
                marker = "●" if pid == actual_id else " "
                console.print(f"  [{i}] {marker} {pid}")

    except ValueError as e:
        console.print(f"[red]✗ {e}[/red]")
        raise

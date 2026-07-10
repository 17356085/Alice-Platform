"""project switch 命令 — 快速切换项目（set 命令的别名）。

更直观的项目切换命令，支持特殊别名:
    "-": 切换到上一个项目
    数字: 从最近列表中选择（如 "1" 表示最近第一个项目）
"""

from rich.console import Console

console = Console()


def switch_command(project_id: str):
    """快速切换项目。

    示例:
        aitest project switch my-project    # 切换到指定项目
        aitest project switch -             # 切换到上一个项目
        aitest project switch 1             # 切换到最近第 1 个项目
        aitest project switch 2             # 切换到最近第 2 个项目
    """
    from aitest.cli.config import CLIConfig
    from aitest.cli.context import CLIContext

    config = CLIConfig()
    ctx = CLIContext(config)
    adapter = ctx.get_project_adapter()

    # 解析数字别名（从最近列表中选择）
    resolved_id = project_id
    if project_id.isdigit():
        index = int(project_id) - 1
        recent = config.recent_projects
        if 0 <= index < len(recent):
            resolved_id = recent[index]
            console.print(f"[dim]从最近列表选择: {resolved_id}[/dim]")
        else:
            console.print(f"[red]✗ 最近列表中没有第 {project_id} 个项目（共 {len(recent)} 个）[/red]")
            if recent:
                console.print("\n[dim]最近使用的项目:[/dim]")
                for i, pid in enumerate(recent[:5], 1):
                    console.print(f"  [{i}] {pid}")
            raise ValueError(f"无效的项目索引: {project_id}")

    try:
        actual_id = adapter.set_active_project(resolved_id)

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

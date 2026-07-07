"""project list 命令 — 列出所有项目。

扫描已注册项目、governance/context/projects/、.tlo/project.yaml。
"""

import json
from typing import Optional

from rich.console import Console
from rich.table import Table

console = Console()


def list_command(
    workspace: str | None = None,
    output_format: str | None = None,
):
    """列出所有项目。"""
    from aitest.cli.config import CLIConfig
    from aitest.cli.context import CLIContext

    config = CLIConfig()
    ctx = CLIContext(config)
    adapter = ctx.get_project_adapter()

    resolved_format = config.resolve_output_format(output_format)

    projects = adapter.list_projects(workspace=workspace)

    if resolved_format == "json":
        print(json.dumps(projects, ensure_ascii=False, indent=2))
        return

    # table 格式
    if not projects:
        console.print("[yellow]⚠️  未找到任何项目[/yellow]")
        console.print("\n使用以下命令注册项目:")
        console.print("  alice project register --path=<path>")
        console.print("  alice project init")
        return

    table = Table(title="项目列表")
    table.add_column("", width=3)  # 活跃标记
    table.add_column("ID", style="bold")
    table.add_column("名称")
    table.add_column("路径")
    table.add_column("来源")

    for project in projects:
        active_mark = "●" if project.get("active") else ""
        active_style = "green" if project.get("active") else "dim"
        table.add_row(
            f"[{active_style}]{active_mark}[/{active_style}]",
            project.get("id", ""),
            project.get("name", ""),
            project.get("path", ""),
            project.get("source", ""),
        )

    console.print(table)

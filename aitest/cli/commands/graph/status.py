"""graph status 命令 — 查看执行状态。

读取 .tlo/runtime/sop-status/ 下的状态文件。
"""

import json
from typing import Optional

from rich.console import Console
from rich.table import Table

console = Console()


def status_command(
    module: str | None = None,
    output_format: str | None = None,
    project_path: str | None = None,
):
    """查看执行状态。"""
    from aitest.cli.config import CLIConfig
    from aitest.cli.context import CLIContext

    config = CLIConfig()
    ctx = CLIContext(config)
    if project_path:
        ctx.project_path = project_path

    resolved_format = config.resolve_output_format(output_format)

    # 通过 adapter 获取状态
    adapter = ctx.get_engine_adapter()
    data = adapter.get_status(module=module)

    if resolved_format == "json":
        print(json.dumps(data, ensure_ascii=False, indent=2))
        return

    # table 格式
    runs = data.get("runs", [])

    if not runs:
        console.print("[yellow][WARN]  未找到执行状态[/yellow]")
        return

    table = Table(title="执行状态")
    table.add_column("模块", style="bold")
    table.add_column("状态")
    table.add_column("完成 Phase")
    table.add_column("失败 Phase")
    table.add_column("更新时间")

    for run_data in runs:
        module_name = run_data.get("module", "")
        status = run_data.get("status", "unknown")
        completed = len(run_data.get("completed_phases", []))
        failed = len(run_data.get("failed_phases", []))
        updated = run_data.get("updated_at", "")

        status_icon = {
            "completed": "[green][OK] 完成[/green]",
            "completed_with_issues": "[yellow][WARN]  部分完成[/yellow]",
            "failed": "[red][FAIL] 失败[/red]",
        }.get(status, f"[dim]{status}[/dim]")

        table.add_row(
            module_name,
            status_icon,
            str(completed),
            str(failed) if failed > 0 else "[dim]-[/dim]",
            updated[:19] if updated else "[dim]-[/dim]",
        )

    console.print(table)

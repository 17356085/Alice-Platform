"""project validate 命令 — 检查项目配置是否合法。"""

import json
from typing import Optional

from rich.console import Console
from rich.table import Table

console = Console()


def validate_command(
    project_id: str | None = None,
    output_format: str | None = None,
):
    """检查项目配置是否合法。"""
    from aitest.cli.config import CLIConfig
    from aitest.cli.context import CLIContext

    config = CLIConfig()
    ctx = CLIContext(config)
    adapter = ctx.get_project_adapter()

    resolved_format = config.resolve_output_format(output_format)

    result = adapter.validate_project(project_id=project_id)

    if resolved_format == "json":
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return

    # table 格式
    checks = result.get("checks", [])

    table = Table(title="项目配置检查")
    table.add_column("检查项", style="bold")
    table.add_column("状态", justify="center")
    table.add_column("说明")

    status_icons = {"ok": "[OK]", "warn": "[WARN]", "error": "[FAIL]"}

    for check in checks:
        status = check.get("status", "")
        icon = status_icons.get(status, status)
        status_style = "green" if status == "ok" else ("yellow" if status == "warn" else "red")
        table.add_row(
            check.get("name", ""),
            f"[{status_style}]{icon}[/{status_style}]",
            check.get("detail", ""),
        )

    console.print(table)

    # 总结
    errors = sum(1 for c in checks if c.get("status") == "error")
    warnings = sum(1 for c in checks if c.get("status") == "warn")

    console.print()
    if errors > 0:
        console.print(f"[red][FAIL] 发现 {errors} 个错误，需要修复[/red]")
    elif warnings > 0:
        console.print(f"[yellow][WARN]  发现 {warnings} 个警告，建议处理[/yellow]")
    else:
        console.print("[green][OK] 配置检查通过[/green]")

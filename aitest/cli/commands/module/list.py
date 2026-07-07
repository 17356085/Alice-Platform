"""module list 命令 — 列出项目中的模块。"""

import json
from pathlib import Path
from typing import Optional

from rich.console import Console
from rich.table import Table

console = Console()


def list_command(
    project_id: str | None = None,
    output_format: str | None = None,
):
    """列出项目中的模块。"""
    from aitest.cli.config import CLIConfig
    from aitest.cli.context import CLIContext

    config = CLIConfig()
    ctx = CLIContext(config)
    if project_id:
        # 临时切换项目
        ctx.config.active_project = project_id

    resolved_format = config.resolve_output_format(output_format)

    # 查找模块目录
    project_path = Path(ctx.project_path)
    modules_dir = project_path / ".tlo" / "knowledge" / "modules"

    if not modules_dir.exists():
        console.print("[yellow][WARN]  未找到模块目录[/yellow]")
        return

    modules = []
    for d in sorted(modules_dir.iterdir()):
        if d.is_dir():
            pages_dir = d / "pages"
            pages_count = sum(1 for p in pages_dir.iterdir() if p.is_dir()) if pages_dir.exists() else 0
            has_context = (d / "MODULE_CONTEXT.md").exists()
            modules.append({
                "name": d.name,
                "pages_count": pages_count,
                "has_context": has_context,
                "path": str(d),
            })

    if not modules:
        console.print("[yellow][WARN]  未找到任何模块[/yellow]")
        return

    if resolved_format == "json":
        print(json.dumps(modules, ensure_ascii=False, indent=2))
        return

    # table 格式
    table = Table(title="模块列表")
    table.add_column("模块", style="bold")
    table.add_column("页面数", justify="right")
    table.add_column("已有知识")
    table.add_column("路径")

    for module in modules:
        has_context = "[OK]" if module.get("has_context") else "[WARN]"
        table.add_row(
            module.get("name", ""),
            str(module.get("pages_count", 0)),
            has_context,
            module.get("path", ""),
        )

    console.print(table)

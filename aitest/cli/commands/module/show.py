"""module show 命令 — 显示模块详情。"""

from pathlib import Path
from typing import Optional

from rich.console import Console
from rich.panel import Panel
from rich.table import Table

console = Console()


def show_command(
    module: str,
    project_id: str | None = None,
):
    """显示模块详情。"""
    from aitest.cli.config import CLIConfig
    from aitest.cli.context import CLIContext

    config = CLIConfig()
    ctx = CLIContext(config)
    if project_id:
        ctx.config.active_project = project_id

    project_path = Path(ctx.project_path)
    module_dir = project_path / ".tlo" / "knowledge" / "modules" / module

    if not module_dir.exists():
        console.print(f"[red][FAIL] 模块 {module} 不存在[/red]")
        return

    # 模块信息
    info = Table(show_header=False, box=None)
    info.add_column("属性", style="bold")
    info.add_column("值")

    info.add_row("模块名", module)
    info.add_row("路径", str(module_dir))

    # 模块上下文
    context_file = module_dir / "MODULE_CONTEXT.md"
    if context_file.exists():
        info.add_row("模块上下文", "[OK] 存在")
    else:
        info.add_row("模块上下文", "[WARN] 不存在")

    # 页面列表
    pages_dir = module_dir / "pages"
    pages = []
    if pages_dir.exists():
        pages = sorted([d.name for d in pages_dir.iterdir() if d.is_dir()])

    info.add_row("页面数量", str(len(pages)))

    # 每个页面的详细信息
    if pages:
        pages_table = Table(title="页面列表")
        pages_table.add_column("页面", style="bold")
        pages_table.add_column("PAGE_CONTEXT")
        pages_table.add_column("PAGE_INTERFACE")
        pages_table.add_column("TEST_CASES")
        pages_table.add_column("TEST_DESIGN")

        for page in pages:
            page_dir = pages_dir / page
            pages_table.add_row(
                page,
                "[OK]" if (page_dir / "PAGE_CONTEXT.md").exists() else "[FAIL]",
                "[OK]" if (page_dir / "PAGE_INTERFACE.yaml").exists() else "[FAIL]",
                "[OK]" if (page_dir / "TEST_CASES.md").exists() else "[FAIL]",
                "[OK]" if (page_dir / "TEST_DESIGN.md").exists() else "[FAIL]",
            )

        console.print(pages_table)

    panel = Panel(info, title=f"[bold]模块: {module}[/bold]", border_style="blue")
    console.print(panel)

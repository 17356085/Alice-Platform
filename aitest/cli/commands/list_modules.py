"""
list-modules 命令 — 列出项目中的模块。

用法:
    alice list-modules --project-path ...
"""

from pathlib import Path

from rich.console import Console
from rich.table import Table

console = Console()


def list_modules_command(project_path: str):
    """列出项目中的模块。"""
    project_dir = Path(project_path)
    tlo_dir = project_dir / ".tlo"

    console.print(f"\n[bold]扫描项目: {project_path}[/bold]\n")

    # 查找模块目录
    modules_dir = tlo_dir / "knowledge" / "modules"

    if not modules_dir.exists():
        console.print("[yellow]⚠️  未找到模块目录[/yellow]")
        return

    # 扫描模块
    modules = []

    for d in modules_dir.iterdir():
        if d.is_dir():
            module_info = _load_module_info(d)
            modules.append(module_info)

    if not modules:
        console.print("[yellow]⚠️  未找到任何模块[/yellow]")
        return

    # 显示模块列表
    table = Table(title="模块列表")

    table.add_column("模块", style="bold")
    table.add_column("页面数", justify="right")
    table.add_column("已有知识")
    table.add_column("路径")

    for module in modules:
        pages_count = module.get("pages_count", 0)
        has_context = "✅" if module.get("has_context") else "⚠️"
        table.add_row(
            module.get("name", ""),
            str(pages_count),
            has_context,
            module.get("path", ""),
        )

    console.print(table)


def _load_module_info(module_dir: Path) -> dict:
    """加载模块信息。"""
    pages_dir = module_dir / "pages"
    pages_count = 0

    if pages_dir.exists():
        pages_count = sum(1 for d in pages_dir.iterdir() if d.is_dir())

    return {
        "name": module_dir.name,
        "pages_count": pages_count,
        "has_context": (module_dir / "MODULE_CONTEXT.md").exists(),
        "path": str(module_dir),
    }

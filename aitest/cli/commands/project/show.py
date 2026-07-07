"""project show 命令 — 查看项目详情。"""

from typing import Optional

from rich.console import Console
from rich.panel import Panel
from rich.table import Table

console = Console()


def show_command(project_id: str | None = None):
    """查看项目详情。"""
    from aitest.cli.config import CLIConfig
    from aitest.cli.context import CLIContext

    config = CLIConfig()
    ctx = CLIContext(config)
    adapter = ctx.get_project_adapter()

    try:
        project = adapter.show_project(project_id=project_id)
    except ValueError as e:
        console.print(f"[red][FAIL] {e}[/red]")
        return

    # 项目信息
    info = Table(show_header=False, box=None)
    info.add_column("属性", style="bold")
    info.add_column("值")

    info.add_row("项目 ID", project.get("id", ""))
    info.add_row("项目名称", project.get("name", ""))
    info.add_row("项目路径", project.get("path", ""))
    info.add_row(".tlo 存在", "[OK]" if project.get("tlo_exists") else "[FAIL]")
    info.add_row("模块数量", str(project.get("module_count", 0)))

    if project.get("modules"):
        info.add_row("模块列表", ", ".join(project["modules"]))

    # 连接信息
    cfg = project.get("config", {})
    conn = cfg.get("connection", {})
    if conn:
        info.add_row("目标 URL", conn.get("base_url", ""))
        info.add_row("环境", conn.get("environment", ""))
        info.add_row("登录方式", conn.get("login_method", ""))

    panel = Panel(info, title=f"[bold]项目: {project.get('id', '')}[/bold]", border_style="blue")
    console.print(panel)

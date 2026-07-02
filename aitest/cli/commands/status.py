"""
status 命令 — 查看执行状态。

用法:
    alice status --project-path ...
    alice status --project-path ... --module equipment
"""

from pathlib import Path

from rich.console import Console
from rich.table import Table

console = Console()


def status_command(project_path: str, module: str = None):
    """查看执行状态。"""
    project_dir = Path(project_path)
    tlo_dir = project_dir / ".tlo"

    console.print(f"\n[bold]项目状态: {project_path}[/bold]\n")

    # 查找 SOP_STATUS 文件
    sop_status_dir = tlo_dir / "runtime" / "sop-status"

    if not sop_status_dir.exists():
        console.print("[yellow]⚠️  未找到执行状态文件[/yellow]")
        return

    # 列出所有状态文件
    status_files = list(sop_status_dir.glob("SOP_STATUS_*.json"))

    if not status_files:
        console.print("[yellow]⚠️  未找到执行状态文件[/yellow]")
        return

    # 过滤模块
    if module:
        status_files = [f for f in status_files if module in f.name]

    if not status_files:
        console.print(f"[yellow]⚠️  未找到模块 {module} 的执行状态[/yellow]")
        return

    # 显示状态
    table = Table(title="执行状态")

    table.add_column("模块", style="bold")
    table.add_column("状态")
    table.add_column("完成 Phase")
    table.add_column("失败 Phase")
    table.add_column("更新时间")

    for status_file in status_files:
        try:
            import json
            with open(status_file, "r", encoding="utf-8") as f:
                data = json.load(f)

            module_name = data.get("module", "")
            status = data.get("status", "unknown")
            completed = len(data.get("completed_phases", []))
            failed = len(data.get("failed_phases", []))
            updated = data.get("updated_at", "")

            status_icon = {
                "completed": "[green]✅ 完成[/green]",
                "completed_with_issues": "[yellow]⚠️  部分完成[/yellow]",
                "failed": "[red]❌ 失败[/red]",
            }.get(status, f"[dim]{status}[/dim]")

            table.add_row(
                module_name,
                status_icon,
                str(completed),
                str(failed) if failed > 0 else "[dim]-[/dim]",
                updated[:19] if updated else "[dim]-[/dim]",
            )

        except Exception as e:
            console.print(f"[red]❌ 读取状态文件失败: {status_file.name}: {e}[/red]")

    console.print(table)

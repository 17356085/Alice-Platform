"""
CLI 输出格式化 — 使用 rich 库美化终端输出。
"""

from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

console = Console()


def print_header(project_path: str, module: str, pages: list[str] = None, mode: str = "full"):
    """打印执行头部信息。"""
    info = Text()
    info.append("项目路径: ", style="bold")
    info.append(project_path, style="cyan")
    info.append("\n")
    info.append("模块: ", style="bold")
    info.append(module, style="green")
    info.append("\n")
    if pages:
        info.append("页面: ", style="bold")
        info.append(", ".join(pages), style="yellow")
        info.append("\n")
    info.append("模式: ", style="bold")
    info.append(mode, style="magenta")

    panel = Panel(info, title="[bold blue]Alice Engine[/bold blue]", border_style="blue")
    console.print(panel)
    console.print()


def print_phase_start(phase: str, index: int, total: int):
    """打印 Phase 开始信息。"""
    console.print(f"\n[bold cyan]━━━ Phase {index}/{total}: {phase} ━━━[/bold cyan]")


def print_phase_result(phase: str, files: list[str] = None, summary: str = "", elapsed: float = 0):
    """打印 Phase 完成信息。"""
    status = f"[green]✅ {phase} 完成[/green]"
    if elapsed > 0:
        status += f" ({elapsed:.1f}s)"
    console.print(status)

    if files:
        for f in files:
            console.print(f"  📄 {f}")

    if summary:
        console.print(f"  {summary}")


def print_phase_skip(phase: str, reason: str = ""):
    """打印 Phase 跳过信息。"""
    msg = f"[yellow]⏭️  {phase} 跳过[/yellow]"
    if reason:
        msg += f" ({reason})"
    console.print(msg)


def print_interrupt(phase: str, files: list[str] = None, summary: str = ""):
    """打印 HITL 中断信息。"""
    console.print(f"\n[bold yellow]⏸️  {phase} — 需要确认[/bold yellow]")

    if files:
        for f in files:
            console.print(f"  📄 {f}")

    if summary:
        console.print(f"  {summary}")

    console.print()
    console.print("  [bold]操作:[/bold]")
    console.print("    [cyan]Enter[/cyan] 继续")
    console.print("    [cyan]v[/cyan] 查看")
    console.print("    [cyan]e[/cyan] 修改")
    console.print("    [cyan]r[/cyan] 重新生成")
    console.print("    [cyan]s[/cyan] 跳过")
    console.print()


def print_test_result(result: dict):
    """打印测试结果表格。"""
    table = Table(title="测试结果")

    table.add_column("指标", style="bold")
    table.add_column("数值", justify="right")

    passed = result.get("passed", 0)
    failed = result.get("failed", 0)
    errors = result.get("errors", 0)
    skipped = result.get("skipped", 0)
    total = passed + failed + errors + skipped

    table.add_row("通过", f"[green]{passed}[/green]")
    table.add_row("失败", f"[red]{failed}[/red]" if failed else "0")
    table.add_row("错误", f"[red]{errors}[/red]" if errors else "0")
    table.add_row("跳过", f"[yellow]{skipped}[/yellow]" if skipped else "0")
    table.add_row("总计", str(total))

    if total > 0:
        pass_rate = passed / (total - skipped) * 100 if (total - skipped) > 0 else 0
        table.add_row("通过率", f"[{'green' if pass_rate >= 80 else 'red'}]{pass_rate:.1f}%[/]")

    console.print(table)


def print_gate_result(gate: dict):
    """打印门禁结果。"""
    status = gate.get("status", "unknown")
    pass_rate = gate.get("pass_rate", 0)

    if status == "pass":
        console.print(f"[green]✅ 门禁通过[/green] (通过率: {pass_rate:.1f}%)")
    elif status == "partial":
        console.print(f"[yellow]⚠️  部分通过[/yellow] (调整后通过率: {pass_rate:.1f}%)")
    else:
        console.print(f"[red]❌ 门禁不通过[/red] (通过率: {pass_rate:.1f}%)")


def print_final_result(result: dict):
    """打印最终结果。"""
    console.print()

    status = result.get("status", "unknown")
    run_id = result.get("run_id", "")
    elapsed = result.get("elapsed_seconds", 0)
    completed = result.get("completed_phases", [])
    failed = result.get("failed_phases", [])
    pages = result.get("pages", [])

    # 状态图标
    status_icon = {
        "completed": "✅",
        "completed_with_issues": "⚠️",
        "failed": "❌",
    }.get(status, "❓")

    # 结果面板
    info = Text()
    info.append(f"状态: {status_icon} {status}\n", style="bold")
    info.append(f"Run ID: {run_id}\n")
    info.append(f"耗时: {elapsed:.1f}s\n")
    info.append(f"完成 Phase: {len(completed)}\n")
    if failed:
        info.append(f"失败 Phase: {len(failed)}\n", style="red")
    if pages:
        info.append(f"处理页面: {', '.join(pages)}\n")

    border_style = "green" if status == "completed" else ("yellow" if status == "completed_with_issues" else "red")
    panel = Panel(info, title="[bold]执行结果[/bold]", border_style=border_style)
    console.print(panel)

    # Phase 列表
    if completed:
        console.print("\n[bold]已完成 Phase:[/bold]")
        for phase in completed:
            console.print(f"  ✅ {phase}")

    if failed:
        console.print("\n[bold red]失败 Phase:[/bold]")
        for phase in failed:
            console.print(f"  ❌ {phase}")


def print_agent_progress(agent_name: str, skills_completed: int, skills_total: int, steps: int):
    """打印 Agent 进度。"""
    progress_bar = "█" * skills_completed + "░" * (skills_total - skills_completed)
    console.print(f"  [{agent_name}] {progress_bar} {skills_completed}/{skills_total} skills, {steps} steps")


def print_skill_execution(skill_id: str, status: str, elapsed: float = 0, tokens: int = 0):
    """打印 Skill 执行详情。"""
    status_icon = {
        "pass": "✅",
        "fail": "❌",
        "partial": "⚠️",
        "skip": "⏭️",
    }.get(status, "❓")

    msg = f"  {status_icon} {skill_id}"
    if elapsed > 0:
        msg += f" ({elapsed:.1f}s)"
    if tokens > 0:
        msg += f" [{tokens} tokens]"
    console.print(msg)


def print_summary_table(phases: list[dict]):
    """打印 Phase 汇总表格。"""
    table = Table(title="Phase 执行汇总")

    table.add_column("Phase", style="bold")
    table.add_column("状态", justify="center")
    table.add_column("耗时", justify="right")
    table.add_column("文件数", justify="right")
    table.add_column("说明")

    for phase in phases:
        name = phase.get("name", "")
        status = phase.get("status", "unknown")
        elapsed = phase.get("elapsed", 0)
        files_count = phase.get("files_count", 0)
        summary = phase.get("summary", "")

        status_icon = {
            "completed": "[green]✅[/green]",
            "skipped": "[yellow]⏭️[/yellow]",
            "failed": "[red]❌[/red]",
            "running": "[blue]🔄[/blue]",
        }.get(status, f"[dim]{status}[/dim]")

        elapsed_str = f"{elapsed:.1f}s" if elapsed > 0 else "-"
        files_str = str(files_count) if files_count > 0 else "-"

        table.add_row(name, status_icon, elapsed_str, files_str, summary[:50])

    console.print(table)

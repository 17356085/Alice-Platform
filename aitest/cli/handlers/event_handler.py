"""
CLI 事件处理器 — 订阅 Engine 事件并展示。
"""

from rich.console import Console

console = Console()


class CLIEventHandler:
    """CLI 事件处理器。"""

    def on_phase_start(self, event: dict):
        """Phase 开始。"""
        phase = event.get("phase", "")
        index = event.get("index", 0)
        total = event.get("total", 9)
        console.print(f"\n[bold cyan]━━━ Phase {index}/{total}: {phase} ━━━[/bold cyan]")

    def on_phase_complete(self, event: dict):
        """Phase 完成。"""
        phase = event.get("phase", "")
        files = event.get("files", [])
        summary = event.get("summary", "")
        elapsed = event.get("elapsed", 0)

        status = f"[green]✅ {phase} 完成[/green]"
        if elapsed > 0:
            status += f" ({elapsed:.1f}s)"
        console.print(status)

        if files:
            for f in files:
                console.print(f"  📄 {f}")

        if summary:
            console.print(f"  {summary}")

    def on_phase_skip(self, event: dict):
        """Phase 跳过。"""
        phase = event.get("phase", "")
        reason = event.get("reason", "")
        msg = f"[yellow]⏭️  {phase} 跳过[/yellow]"
        if reason:
            msg += f" ({reason})"
        console.print(msg)

    def on_interrupt(self, event: dict):
        """HITL 中断。"""
        phase = event.get("phase", "")
        files = event.get("files", [])
        summary = event.get("summary", "")

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

    def on_test_result(self, event: dict):
        """测试结果。"""
        from aitest.cli.output.formatter import print_test_result
        print_test_result(event)

    def on_gate_result(self, event: dict):
        """门禁结果。"""
        from aitest.cli.output.formatter import print_gate_result
        print_gate_result(event)

    def on_error(self, event: dict):
        """错误。"""
        error_type = event.get("error_type", "")
        message = event.get("message", "")
        console.print(f"[red]❌ {error_type}: {message}[/red]")

    def on_complete(self, event: dict):
        """全部完成。"""
        from aitest.cli.output.formatter import print_final_result
        print_final_result(event)

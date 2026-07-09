"""
run 命令 — 通过官方 ExecutionService 主链路执行 SOP。
"""

from __future__ import annotations

import os
from typing import Optional

import typer
from rich.console import Console
from aitest.cli.core.composition import (
    cli_runtime_scope,
    get_cli_execution_service,
    resolve_cli_project_dir,
    resolve_cli_provider,
)

console = Console()


def run_command(
    project_path: str | None,
    module: str,
    pages: Optional[list[str]] = None,
    mode: str = "full",
    extensions: Optional[list[str]] = None,
    mock_llm: bool = False,
    llm_provider: Optional[str] = None,
    verbose: bool = False,
):
    """执行一次完整 SOP 流水线。"""
    del extensions, verbose  # Phase 1: CLI 先统一主链路，扩展挂接后续回收

    try:
        project_dir = resolve_cli_project_dir(project_path)
    except (FileNotFoundError, ValueError) as exc:
        console.print(f"[red]{exc}[/red]")
        raise typer.Exit(1)

    resolved_provider = resolve_cli_provider(llm_provider)

    pages = pages or []

    from aitest.platform.workspace import ExecutionContext

    svc = get_cli_execution_service()
    ctx = ExecutionContext(
        workspace_id=project_dir.name or "cli",
        user_id="cli",
        scopes=["read", "execute", "admin"],
        org_id="local",
        entrypoint="cli.graph.run",
        metadata={"project_path": str(project_dir)},
    )

    console.print(f"[bold]Alice Graph Run[/bold]")
    console.print(f"  project: {project_dir}")
    console.print(f"  module: {module}")
    console.print(f"  pages: {', '.join(pages) if pages else '(auto)'}")
    console.print(f"  mode: {mode}")
    console.print()

    try:
        with cli_runtime_scope(project_dir, resolved_provider, mock_llm):
            result = svc.execute(
                ctx,
                module=module,
                pages=pages,
                agent="sop",
                mode=mode,
                provider=resolved_provider,
            )
    except KeyboardInterrupt:
        console.print("[yellow]执行已中断[/yellow]")
        raise typer.Exit(130)
    except Exception as exc:
        console.print(f"[red]执行失败: {str(exc)[:300]}[/red]")
        raise typer.Exit(1)

    console.print(f"[bold]状态:[/bold] {result.status}")
    console.print(f"[bold]Run ID:[/bold] {result.run_id}")
    console.print(f"[bold]耗时:[/bold] {result.duration_ms:.1f}ms")
    if result.completed_phases:
        console.print(f"[bold]完成阶段:[/bold] {', '.join(result.completed_phases)}")
    if result.failed_phases:
        console.print(f"[bold]失败阶段:[/bold] {', '.join(result.failed_phases)}")
    if result.error_message:
        console.print(f"[bold red]错误:[/bold red] {result.error_message}")

    if not result.success:
        raise typer.Exit(1)

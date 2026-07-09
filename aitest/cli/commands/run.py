"""
run 命令 — 执行一次完整 SOP 流水线。

用法:
    alice run --project-path ... --module equipment
    alice run --project-path ... --module equipment --pages alarm-config,camera
    alice run --project-path ... --module equipment --mock-llm
"""

import sys
from pathlib import Path
from typing import Optional

from rich.console import Console
from rich.panel import Panel
from rich.table import Table

console = Console()


def run_command(
    project_path: str,
    module: str,
    pages: Optional[list[str]] = None,
    mode: str = "full",
    extensions: Optional[list[str]] = None,
    mock_llm: bool = False,
    llm_provider: Optional[str] = None,
    verbose: bool = False,
):
    """执行一次完整 SOP 流水线。"""
    from aitest.cli.output.formatter import print_header, print_phase_result, print_final_result
    from aitest.cli.output.progress import create_progress
    from aitest.cli.handlers.event_handler import CLIEventHandler
    from aitest.cli.handlers.cli_pause_handler import get_cli_pause_handler
    from aitest.engine.event_bus import get_event_bus

    # 显示执行信息
    print_header(project_path, module, pages, mode)

    # 检查 project.yaml
    project_dir = Path(project_path)
    tlo_dir = project_dir / ".tlo"
    project_yaml = tlo_dir / "project.yaml"

    if not project_yaml.exists():
        console.print("[yellow]⚠️  未找到 project.yaml，将进入 Phase 0 配置[/yellow]")
        from aitest.cli.commands.phase0 import phase0_interactive
        config = phase0_interactive(project_path)
        if not config:
            raise typer.Exit(0)

    # 初始化 Engine
    try:
        from aitest.engine import Engine

        # 创建事件处理器并订阅事件
        event_handler = CLIEventHandler()
        pause_handler = get_cli_pause_handler()
        bus = get_event_bus()
        bus.subscribe("phase_start", event_handler.on_phase_start)
        bus.subscribe("phase_complete", event_handler.on_phase_complete)
        bus.subscribe("phase_skip", event_handler.on_phase_skip)
        bus.subscribe("interrupt", event_handler.on_interrupt)
        bus.subscribe("test_result", event_handler.on_test_result)
        bus.subscribe("gate_result", event_handler.on_gate_result)
        bus.subscribe("error", event_handler.on_error)
        bus.subscribe("complete", event_handler.on_complete)
        bus.subscribe("pause", pause_handler.on_pause)

        engine = Engine(
            workstudy=str(project_dir),
            governance=str(project_dir / "governance") if (project_dir / "governance").exists() else None,
            llm_provider=llm_provider,
            mock_llm=mock_llm if mock_llm else None,
            event_bus=bus,
        )

        # 加载 Extensions
        if extensions:
            from aitest.engine.extensions import (
                AuditExtension, ComplexityExtension,
                KnowledgeExtension, MemoryExtension,
            )
            ext_map = {
                "audit": AuditExtension,
                "complexity": ComplexityExtension,
                "knowledge": KnowledgeExtension,
                "memory": MemoryExtension,
            }
            for ext_name in extensions:
                ext_cls = ext_map.get(ext_name.strip())
                if ext_cls:
                    engine.add_extension(ext_cls())
                    console.print(f"  [green]✅ Extension loaded: {ext_name}[/green]")
                else:
                    console.print(f"  [yellow]⚠️  Unknown extension: {ext_name}[/yellow]")

        # 执行
        console.print()
        with create_progress() as progress:
            task = progress.add_task("执行 SOP...", total=None)

            result = engine.run(
                module=module,
                pages=pages,
                mode=mode,
            )

            progress.update(task, completed=True)

        # 显示结果 (如果 complete 事件没有被处理)
        if result.get("status"):
            print_final_result(result)

    except KeyboardInterrupt:
        from aitest.cli.handlers.error_handler import print_error
        print_error("user_interrupt")
        raise typer.Exit(130)
    except Exception as e:
        from aitest.cli.handlers.error_handler import handle_exception
        handle_exception(e, verbose)
        raise typer.Exit(1)

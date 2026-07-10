"""workflow show 命令 — 显示 Workflow 详情。

显示 Workflow 的完整配置，包括 Agents、Steps、Transitions。
"""

import json
import yaml
from pathlib import Path
from rich.console import Console
from rich.table import Table
from rich.tree import Tree

console = Console()


def show_command(workflow_id: str, output_format: str = "table"):
    """显示 Workflow 详情。

    示例:
        aitest workflow show my-workflow
        aitest workflow show my-workflow --output json
    """
    from aitest.cli.config import CLIConfig

    config = CLIConfig()

    try:
        # 获取活跃项目路径
        project_path = config.active_project_path
        if not project_path:
            console.print("[red]✗ 未找到活跃项目，请先使用 'aitest project set --id=<id>'[/red]")
            raise ValueError("未找到活跃项目")

        workflow_dir = Path(project_path) / ".tlo" / "workflows"
        workflow_file = workflow_dir / f"{workflow_id}.yaml"

        if not workflow_file.exists():
            console.print(f"[red]✗ Workflow 不存在: {workflow_id}[/red]")
            console.print(f"\n使用以下命令查看所有 Workflow:")
            console.print("  aitest workflow list")
            raise ValueError(f"Workflow 不存在: {workflow_id}")

        # 加载 Workflow
        with open(workflow_file, "r", encoding="utf-8") as f:
            workflow_data = yaml.safe_load(f)

        # 输出
        if output_format == "json":
            print(json.dumps(workflow_data, ensure_ascii=False, indent=2))
            return
        elif output_format == "yaml":
            print(yaml.dump(workflow_data, allow_unicode=True, default_flow_style=False))
            return

        # 表格输出
        _print_workflow_detail(workflow_data, workflow_file)

    except Exception as e:
        console.print(f"[red]✗ 显示失败: {e}[/red]")
        raise


def _print_workflow_detail(workflow_data: dict, file_path: Path):
    """打印 Workflow 详细信息。"""
    # 标题
    console.print(f"\n[bold cyan]{workflow_data.get('id', 'Workflow')}[/bold cyan]")
    console.print(f"[bold]{workflow_data.get('name', '')}[/bold]")
    if workflow_data.get("description"):
        console.print(f"[dim]{workflow_data['description']}[/dim]")
    console.print(f"[dim]文件: {file_path}[/dim]\n")

    # Agents
    console.print("[bold]Agents:[/bold]")
    agents = workflow_data.get("agents", [])
    if agents:
        for i, agent in enumerate(agents, 1):
            console.print(f"  {i}. {agent}")
    else:
        console.print("  [dim]无[/dim]")

    # Steps
    console.print("\n[bold]Steps:[/bold]")
    steps = workflow_data.get("steps", [])
    if steps:
        table = Table(show_header=True, box=None)
        table.add_column("ID", style="cyan")
        table.add_column("Agent", style="yellow")
        table.add_column("Description")
        table.add_column("Config", style="dim")

        for step in steps:
            config_str = ""
            if step.get("config"):
                config_str = f"{len(step['config'])} keys"

            table.add_row(
                step.get("id", ""),
                step.get("agent", ""),
                step.get("description", ""),
                config_str,
            )

        console.print(table)
    else:
        console.print("  [dim]无[/dim]")

    # Transitions
    console.print("\n[bold]Transitions:[/bold]")
    transitions = workflow_data.get("transitions", [])
    if transitions:
        tree = Tree("Flow")
        step_nodes = {}

        # 构建步骤节点
        for step in steps:
            step_id = step.get("id")
            step_nodes[step_id] = step_id

        # 显示流转
        for trans in transitions:
            from_step = trans.get("from")
            to_step = trans.get("to")
            condition = trans.get("condition", "")
            condition_str = f" [dim]({condition})[/dim]" if condition else ""
            console.print(f"  {from_step} → {to_step}{condition_str}")
    else:
        console.print("  [dim]无（单步流程）[/dim]")

    # Input/Output Schema
    if workflow_data.get("input_schema"):
        console.print("\n[bold]Input Schema:[/bold]")
        console.print(f"  [dim]{yaml.dump(workflow_data['input_schema'], default_flow_style=False)}[/dim]")

    if workflow_data.get("output_schema"):
        console.print("\n[bold]Output Schema:[/bold]")
        console.print(f"  [dim]{yaml.dump(workflow_data['output_schema'], default_flow_style=False)}[/dim]")

    # Metadata
    if workflow_data.get("metadata"):
        console.print("\n[bold]Metadata:[/bold]")
        for key, value in workflow_data["metadata"].items():
            console.print(f"  {key}: {value}")

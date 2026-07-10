"""workflow create 命令 — 创建新 Workflow。

Workflow 定义测试流程的编排方式，包含：
- Agents: 参与的 Agent 列表
- Steps: 执行步骤序列
- Transitions: 步骤间的流转规则
- Input/Output: 输入输出规范
"""

import json
import yaml
from pathlib import Path
from rich.console import Console

console = Console()


def create_command(
    workflow_id: str,
    name: str = None,
    description: str = None,
    template: str = None,
    from_file: str = None,
    output_format: str = "table",
):
    """创建新的 Workflow。

    示例:
        # 从模板创建
        aitest workflow create --id=my-flow --template=page-test

        # 从文件创建
        aitest workflow create --id=my-flow --from-file=workflow.yaml

        # 交互式创建
        aitest workflow create --id=my-flow --name="My Workflow"
    """
    from aitest.cli.config import CLIConfig
    from aitest.cli.context import CLIContext

    config = CLIConfig()
    ctx = CLIContext(config)

    try:
        # 1. 从文件加载
        if from_file:
            file_path = Path(from_file)
            if not file_path.exists():
                console.print(f"[red]✗ 文件不存在: {from_file}[/red]")
                raise ValueError(f"文件不存在: {from_file}")

            if file_path.suffix in [".yaml", ".yml"]:
                with open(file_path, "r", encoding="utf-8") as f:
                    workflow_data = yaml.safe_load(f)
            elif file_path.suffix == ".json":
                with open(file_path, "r", encoding="utf-8") as f:
                    workflow_data = json.load(f)
            else:
                console.print(f"[red]✗ 不支持的文件格式: {file_path.suffix}[/red]")
                raise ValueError(f"不支持的文件格式: {file_path.suffix}")

            console.print(f"[dim]从文件加载: {from_file}[/dim]")

        # 2. 从模板创建
        elif template:
            workflow_data = _get_template(template)
            console.print(f"[dim]使用模板: {template}[/dim]")

        # 3. 交互式创建
        else:
            workflow_data = _interactive_create(workflow_id, name, description)

        # 覆盖 ID
        workflow_data["id"] = workflow_id

        # 保存到项目
        project_path = _get_project_path(config)
        if not project_path:
            console.print("[red]✗ 未找到活跃项目，请先使用 'aitest project set --id=<id>'[/red]")
            raise ValueError("未找到活跃项目")

        workflow_dir = project_path / ".tlo" / "workflows"
        workflow_dir.mkdir(parents=True, exist_ok=True)

        workflow_file = workflow_dir / f"{workflow_id}.yaml"
        if workflow_file.exists():
            console.print(f"[yellow]⚠️  Workflow 已存在: {workflow_id}[/yellow]")
            from rich.prompt import Confirm
            if not Confirm.ask("是否覆盖?", default=False):
                console.print("[dim]已取消[/dim]")
                return

        with open(workflow_file, "w", encoding="utf-8") as f:
            yaml.dump(workflow_data, f, allow_unicode=True, default_flow_style=False)

        console.print(f"[green]✓ Workflow 已创建: {workflow_id}[/green]")
        console.print(f"[dim]文件: {workflow_file}[/dim]")

        # 显示详情
        if output_format == "table":
            _print_workflow_summary(workflow_data)
        elif output_format == "json":
            print(json.dumps(workflow_data, ensure_ascii=False, indent=2))
        elif output_format == "yaml":
            print(yaml.dump(workflow_data, allow_unicode=True, default_flow_style=False))

    except Exception as e:
        console.print(f"[red]✗ 创建失败: {e}[/red]")
        raise


def _get_template(template_name: str) -> dict:
    """获取预定义模板。"""
    templates = {
        "page-test": {
            "name": "Page Test Workflow",
            "description": "单页面测试流程",
            "agents": ["page-observer", "action-executor", "assertion-writer"],
            "steps": [
                {"id": "observe", "agent": "page-observer", "description": "观察页面"},
                {"id": "execute", "agent": "action-executor", "description": "执行操作"},
                {"id": "assert", "agent": "assertion-writer", "description": "编写断言"},
            ],
            "transitions": [
                {"from": "observe", "to": "execute"},
                {"from": "execute", "to": "assert"},
            ],
        },
        "module-test": {
            "name": "Module Test Workflow",
            "description": "模块级测试流程",
            "agents": ["module-analyzer", "page-observer", "action-executor", "assertion-writer", "script-merger"],
            "steps": [
                {"id": "analyze", "agent": "module-analyzer", "description": "分析模块"},
                {"id": "observe", "agent": "page-observer", "description": "观察页面"},
                {"id": "execute", "agent": "action-executor", "description": "执行操作"},
                {"id": "assert", "agent": "assertion-writer", "description": "编写断言"},
                {"id": "merge", "agent": "script-merger", "description": "合并脚本"},
            ],
            "transitions": [
                {"from": "analyze", "to": "observe"},
                {"from": "observe", "to": "execute"},
                {"from": "execute", "to": "assert"},
                {"from": "assert", "to": "merge"},
            ],
        },
        "simple": {
            "name": "Simple Workflow",
            "description": "简单单步流程",
            "agents": ["page-observer"],
            "steps": [
                {"id": "step1", "agent": "page-observer", "description": "执行任务"},
            ],
            "transitions": [],
        },
    }

    if template_name not in templates:
        available = ", ".join(templates.keys())
        raise ValueError(f"模板 {template_name} 不存在。可用模板: {available}")

    return templates[template_name]


def _interactive_create(workflow_id: str, name: str = None, description: str = None) -> dict:
    """交互式创建 Workflow。"""
    from rich.prompt import Prompt

    workflow_name = name or Prompt.ask("Workflow 名称", default=workflow_id.replace("-", " ").title())
    workflow_desc = description or Prompt.ask("Workflow 描述", default="")

    console.print("\n[dim]请输入 Agent 列表（逗号分隔）:[/dim]")
    agents_input = Prompt.ask("Agents", default="page-observer")
    agents = [a.strip() for a in agents_input.split(",")]

    console.print("\n[yellow]⚠️  Steps 和 Transitions 需要在 YAML 文件中手动配置[/yellow]")

    return {
        "id": workflow_id,
        "name": workflow_name,
        "description": workflow_desc,
        "agents": agents,
        "steps": [
            {"id": "step1", "agent": agents[0], "description": "执行任务"}
        ],
        "transitions": [],
    }


def _get_project_path(config) -> Path | None:
    """获取活跃项目路径。"""
    project_path = config.active_project_path
    if project_path:
        return Path(project_path)
    return None


def _print_workflow_summary(workflow_data: dict):
    """打印 Workflow 摘要。"""
    from rich.table import Table

    console.print(f"\n[bold]{workflow_data.get('name', 'Workflow')}[/bold]")
    if workflow_data.get("description"):
        console.print(f"[dim]{workflow_data['description']}[/dim]")

    # Agents
    console.print("\n[bold]Agents:[/bold]")
    for agent in workflow_data.get("agents", []):
        console.print(f"  • {agent}")

    # Steps
    console.print("\n[bold]Steps:[/bold]")
    table = Table(show_header=True)
    table.add_column("ID", style="cyan")
    table.add_column("Agent", style="yellow")
    table.add_column("Description")

    for step in workflow_data.get("steps", []):
        table.add_row(
            step.get("id", ""),
            step.get("agent", ""),
            step.get("description", ""),
        )

    console.print(table)

    # Transitions
    if workflow_data.get("transitions"):
        console.print("\n[bold]Transitions:[/bold]")
        for trans in workflow_data["transitions"]:
            console.print(f"  {trans.get('from')} → {trans.get('to')}")

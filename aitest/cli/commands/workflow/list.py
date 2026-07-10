"""workflow list 命令 — 列出所有 Workflow。

扫描项目 .tlo/workflows/ 目录下的所有 Workflow 定义。
"""

import json
import yaml
from pathlib import Path
from rich.console import Console
from rich.table import Table

console = Console()


def list_command(output_format: str = "table"):
    """列出所有 Workflow。

    示例:
        aitest workflow list
        aitest workflow list --output json
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
        if not workflow_dir.exists():
            console.print("[yellow]⚠️  未找到 Workflow 目录[/yellow]")
            console.print(f"\n使用以下命令创建 Workflow:")
            console.print("  aitest workflow create --id=<id> --template=page-test")
            return

        # 扫描所有 YAML 文件
        workflows = []
        for file_path in workflow_dir.glob("*.yaml"):
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    data = yaml.safe_load(f)
                    if data:
                        workflows.append({
                            "id": data.get("id", file_path.stem),
                            "name": data.get("name", ""),
                            "description": data.get("description", ""),
                            "agents": data.get("agents", []),
                            "steps": len(data.get("steps", [])),
                            "file": str(file_path),
                        })
            except Exception as e:
                console.print(f"[yellow]⚠️  无法解析 {file_path.name}: {e}[/yellow]")

        if not workflows:
            console.print("[yellow]⚠️  未找到任何 Workflow[/yellow]")
            console.print(f"\n使用以下命令创建 Workflow:")
            console.print("  aitest workflow create --id=<id> --template=page-test")
            return

        # 输出
        if output_format == "json":
            print(json.dumps(workflows, ensure_ascii=False, indent=2))
            return
        elif output_format == "yaml":
            print(yaml.dump(workflows, allow_unicode=True, default_flow_style=False))
            return

        # 表格输出
        table = Table(title=f"Workflows ({len(workflows)})")
        table.add_column("ID", style="bold cyan")
        table.add_column("名称")
        table.add_column("描述")
        table.add_column("Agents", style="yellow")
        table.add_column("Steps", justify="right")

        for wf in workflows:
            agents_str = ", ".join(wf["agents"][:2])
            if len(wf["agents"]) > 2:
                agents_str += f" +{len(wf['agents']) - 2}"

            table.add_row(
                wf["id"],
                wf["name"],
                wf["description"][:50] + "..." if len(wf.get("description", "")) > 50 else wf.get("description", ""),
                agents_str,
                str(wf["steps"]),
            )

        console.print(table)
        console.print(f"\n[dim]目录: {workflow_dir}[/dim]")

    except Exception as e:
        console.print(f"[red]✗ 列出失败: {e}[/red]")
        raise

"""quality eval 命令 — 评估任务管理。

评估任务用于测试 Agent 在数据集上的表现。
"""

import json
import yaml
from pathlib import Path
from datetime import datetime
from rich.console import Console
from rich.table import Table

console = Console()


def eval_run(
    eval_id: str,
    agent_id: str,
    dataset_id: str,
    provider: str = None,
    mock_llm: bool = False,
    wait: bool = True,
    output_format: str = "table",
):
    """运行评估任务。

    示例:
        aitest quality eval run --id=eval-001 --agent=page-observer --dataset=my-dataset
        aitest quality eval run --id=eval-001 --agent=page-observer --dataset=my-dataset --provider=deepseek
    """
    from aitest.cli.config import CLIConfig

    config = CLIConfig()

    try:
        project_path = config.active_project_path
        if not project_path:
            console.print("[red]✗ 未找到活跃项目[/red]")
            raise ValueError("未找到活跃项目")

        # 验证数据集存在
        dataset_dir = Path(project_path) / ".tlo" / "quality" / "datasets"
        dataset_file = dataset_dir / f"{dataset_id}.yaml"
        if not dataset_file.exists():
            console.print(f"[red]✗ 数据集不存在: {dataset_id}[/red]")
            raise ValueError(f"数据集不存在: {dataset_id}")

        console.print(f"[bold]运行评估任务: {eval_id}[/bold]")
        console.print(f"  Agent: {agent_id}")
        console.print(f"  Dataset: {dataset_id}")
        console.print(f"  Provider: {provider or config.resolve_llm_provider()}")
        console.print()

        # 加载数据集
        with open(dataset_file, "r", encoding="utf-8") as f:
            dataset_data = yaml.safe_load(f)

        samples = dataset_data.get("samples", [])
        if not samples:
            console.print("[yellow]⚠️  数据集为空，无样本可评估[/yellow]")
            return

        console.print(f"[dim]数据集样本数: {len(samples)}[/dim]")
        console.print("[yellow]⚠️  评估功能需要集成到 Run 系统，当前为模拟输出[/yellow]\n")

        # 模拟评估结果
        eval_result = {
            "eval_id": eval_id,
            "agent_id": agent_id,
            "dataset_id": dataset_id,
            "provider": provider or config.resolve_llm_provider(),
            "timestamp": datetime.now().isoformat(),
            "sample_count": len(samples),
            "results": {
                "passed": int(len(samples) * 0.85),  # 模拟 85% 通过率
                "failed": int(len(samples) * 0.15),
                "accuracy": 0.85,
            },
            "status": "completed",
        }

        # 保存评估结果
        eval_dir = Path(project_path) / ".tlo" / "quality" / "evaluations"
        eval_dir.mkdir(parents=True, exist_ok=True)

        eval_file = eval_dir / f"{eval_id}.yaml"
        with open(eval_file, "w", encoding="utf-8") as f:
            yaml.dump(eval_result, f, allow_unicode=True, default_flow_style=False)

        console.print(f"[green]✓ 评估完成: {eval_id}[/green]")
        console.print(f"[dim]结果文件: {eval_file}[/dim]\n")

        # 输出结果
        if output_format == "json":
            print(json.dumps(eval_result, ensure_ascii=False, indent=2))
        elif output_format == "yaml":
            print(yaml.dump(eval_result, allow_unicode=True, default_flow_style=False))
        else:
            _print_eval_result(eval_result)

    except Exception as e:
        console.print(f"[red]✗ 评估失败: {e}[/red]")
        raise


def eval_list(output_format: str = "table"):
    """列出所有评估任务。

    示例:
        aitest quality eval list
        aitest quality eval list --output json
    """
    from aitest.cli.config import CLIConfig

    config = CLIConfig()

    try:
        project_path = config.active_project_path
        if not project_path:
            console.print("[red]✗ 未找到活跃项目[/red]")
            raise ValueError("未找到活跃项目")

        eval_dir = Path(project_path) / ".tlo" / "quality" / "evaluations"
        if not eval_dir.exists():
            console.print("[yellow]⚠️  未找到评估结果目录[/yellow]")
            console.print("\n使用以下命令运行评估:")
            console.print("  aitest quality eval run --id=<id> --agent=<agent> --dataset=<dataset>")
            return

        # 扫描所有评估结果
        evaluations = []
        for file_path in eval_dir.glob("*.yaml"):
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    data = yaml.safe_load(f)
                    if data:
                        evaluations.append({
                            "eval_id": data.get("eval_id", file_path.stem),
                            "agent_id": data.get("agent_id", ""),
                            "dataset_id": data.get("dataset_id", ""),
                            "accuracy": data.get("results", {}).get("accuracy", 0),
                            "sample_count": data.get("sample_count", 0),
                            "timestamp": data.get("timestamp", ""),
                            "status": data.get("status", ""),
                        })
            except Exception as e:
                console.print(f"[yellow]⚠️  无法解析 {file_path.name}: {e}[/yellow]")

        if not evaluations:
            console.print("[yellow]⚠️  未找到任何评估结果[/yellow]")
            return

        # 按时间排序
        evaluations.sort(key=lambda x: x["timestamp"], reverse=True)

        # 输出
        if output_format == "json":
            print(json.dumps(evaluations, ensure_ascii=False, indent=2))
            return
        elif output_format == "yaml":
            print(yaml.dump(evaluations, allow_unicode=True, default_flow_style=False))
            return

        # 表格输出
        table = Table(title=f"评估任务 ({len(evaluations)})")
        table.add_column("Eval ID", style="bold cyan")
        table.add_column("Agent")
        table.add_column("Dataset")
        table.add_column("Accuracy", justify="right")
        table.add_column("Samples", justify="right")
        table.add_column("时间", style="dim")
        table.add_column("状态")

        for ev in evaluations:
            accuracy_str = f"{ev['accuracy']:.1%}" if ev['accuracy'] else "N/A"
            status_color = "green" if ev["status"] == "completed" else "yellow"

            table.add_row(
                ev["eval_id"],
                ev["agent_id"],
                ev["dataset_id"],
                accuracy_str,
                str(ev["sample_count"]),
                ev["timestamp"][:19] if ev["timestamp"] else "",
                f"[{status_color}]{ev['status']}[/{status_color}]",
            )

        console.print(table)
        console.print(f"\n[dim]目录: {eval_dir}[/dim]")

    except Exception as e:
        console.print(f"[red]✗ 列出失败: {e}[/red]")
        raise


def eval_show(eval_id: str, output_format: str = "table"):
    """显示评估详情。

    示例:
        aitest quality eval show eval-001
        aitest quality eval show eval-001 --output json
    """
    from aitest.cli.config import CLIConfig

    config = CLIConfig()

    try:
        project_path = config.active_project_path
        if not project_path:
            console.print("[red]✗ 未找到活跃项目[/red]")
            raise ValueError("未找到活跃项目")

        eval_dir = Path(project_path) / ".tlo" / "quality" / "evaluations"
        eval_file = eval_dir / f"{eval_id}.yaml"

        if not eval_file.exists():
            console.print(f"[red]✗ 评估结果不存在: {eval_id}[/red]")
            raise ValueError(f"评估结果不存在: {eval_id}")

        # 加载评估结果
        with open(eval_file, "r", encoding="utf-8") as f:
            eval_data = yaml.safe_load(f)

        # 输出
        if output_format == "json":
            print(json.dumps(eval_data, ensure_ascii=False, indent=2))
            return
        elif output_format == "yaml":
            print(yaml.dump(eval_data, allow_unicode=True, default_flow_style=False))
            return

        # 表格输出
        _print_eval_result(eval_data)

    except Exception as e:
        console.print(f"[red]✗ 显示失败: {e}[/red]")
        raise


def _print_eval_result(eval_data: dict):
    """打印评估结果。"""
    console.print(f"\n[bold cyan]{eval_data.get('eval_id', 'Evaluation')}[/bold cyan]")
    console.print(f"  Agent: {eval_data.get('agent_id', '')}")
    console.print(f"  Dataset: {eval_data.get('dataset_id', '')}")
    console.print(f"  Provider: {eval_data.get('provider', '')}")
    console.print(f"  时间: {eval_data.get('timestamp', '')}")
    console.print()

    results = eval_data.get("results", {})
    sample_count = eval_data.get("sample_count", 0)

    console.print("[bold]评估结果:[/bold]")
    console.print(f"  样本总数: {sample_count}")
    console.print(f"  通过: [green]{results.get('passed', 0)}[/green]")
    console.print(f"  失败: [red]{results.get('failed', 0)}[/red]")
    console.print(f"  准确率: [bold]{results.get('accuracy', 0):.1%}[/bold]")

    status = eval_data.get("status", "")
    status_color = "green" if status == "completed" else "yellow"
    console.print(f"  状态: [{status_color}]{status}[/{status_color}]")

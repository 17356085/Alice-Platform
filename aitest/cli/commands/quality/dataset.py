"""quality dataset 命令 — 数据集管理。

数据集用于评估 Agent 质量，包含：
- 输入样本（测试用例）
- 预期输出（Ground Truth）
- 元数据（标签、难度等）
"""

import json
import yaml
from pathlib import Path
from rich.console import Console
from rich.table import Table

console = Console()


def dataset_list(output_format: str = "table"):
    """列出所有数据集。

    示例:
        aitest quality dataset list
        aitest quality dataset list --output json
    """
    from aitest.cli.config import CLIConfig

    config = CLIConfig()

    try:
        project_path = config.active_project_path
        if not project_path:
            console.print("[red]✗ 未找到活跃项目，请先使用 'aitest project set --id=<id>'[/red]")
            raise ValueError("未找到活跃项目")

        dataset_dir = Path(project_path) / ".tlo" / "quality" / "datasets"
        if not dataset_dir.exists():
            console.print("[yellow]⚠️  未找到数据集目录[/yellow]")
            console.print("\n使用以下命令创建数据集:")
            console.print("  aitest quality dataset create --id=<id>")
            return

        # 扫描所有数据集
        datasets = []
        for file_path in dataset_dir.glob("*.yaml"):
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    data = yaml.safe_load(f)
                    if data:
                        samples = data.get("samples", [])
                        datasets.append({
                            "id": data.get("id", file_path.stem),
                            "name": data.get("name", ""),
                            "description": data.get("description", ""),
                            "sample_count": len(samples),
                            "tags": data.get("tags", []),
                            "file": str(file_path),
                        })
            except Exception as e:
                console.print(f"[yellow]⚠️  无法解析 {file_path.name}: {e}[/yellow]")

        if not datasets:
            console.print("[yellow]⚠️  未找到任何数据集[/yellow]")
            console.print("\n使用以下命令创建数据集:")
            console.print("  aitest quality dataset create --id=<id>")
            return

        # 输出
        if output_format == "json":
            print(json.dumps(datasets, ensure_ascii=False, indent=2))
            return
        elif output_format == "yaml":
            print(yaml.dump(datasets, allow_unicode=True, default_flow_style=False))
            return

        # 表格输出
        table = Table(title=f"数据集 ({len(datasets)})")
        table.add_column("ID", style="bold cyan")
        table.add_column("名称")
        table.add_column("描述")
        table.add_column("样本数", justify="right")
        table.add_column("标签", style="dim")

        for ds in datasets:
            tags_str = ", ".join(ds["tags"][:3])
            if len(ds["tags"]) > 3:
                tags_str += f" +{len(ds['tags']) - 3}"

            table.add_row(
                ds["id"],
                ds["name"],
                ds["description"][:40] + "..." if len(ds.get("description", "")) > 40 else ds.get("description", ""),
                str(ds["sample_count"]),
                tags_str,
            )

        console.print(table)
        console.print(f"\n[dim]目录: {dataset_dir}[/dim]")

    except Exception as e:
        console.print(f"[red]✗ 列出失败: {e}[/red]")
        raise


def dataset_show(dataset_id: str, output_format: str = "table"):
    """显示数据集详情。

    示例:
        aitest quality dataset show my-dataset
        aitest quality dataset show my-dataset --output json
    """
    from aitest.cli.config import CLIConfig

    config = CLIConfig()

    try:
        project_path = config.active_project_path
        if not project_path:
            console.print("[red]✗ 未找到活跃项目[/red]")
            raise ValueError("未找到活跃项目")

        dataset_dir = Path(project_path) / ".tlo" / "quality" / "datasets"
        dataset_file = dataset_dir / f"{dataset_id}.yaml"

        if not dataset_file.exists():
            console.print(f"[red]✗ 数据集不存在: {dataset_id}[/red]")
            raise ValueError(f"数据集不存在: {dataset_id}")

        # 加载数据集
        with open(dataset_file, "r", encoding="utf-8") as f:
            dataset_data = yaml.safe_load(f)

        # 输出
        if output_format == "json":
            print(json.dumps(dataset_data, ensure_ascii=False, indent=2))
            return
        elif output_format == "yaml":
            print(yaml.dump(dataset_data, allow_unicode=True, default_flow_style=False))
            return

        # 表格输出
        _print_dataset_detail(dataset_data, dataset_file)

    except Exception as e:
        console.print(f"[red]✗ 显示失败: {e}[/red]")
        raise


def dataset_create(
    dataset_id: str,
    name: str = None,
    description: str = None,
    from_file: str = None,
    output_format: str = "table",
):
    """创建新数据集。

    示例:
        # 交互式创建
        aitest quality dataset create --id=my-dataset

        # 从文件创建
        aitest quality dataset create --id=my-dataset --from-file=dataset.yaml
    """
    from aitest.cli.config import CLIConfig

    config = CLIConfig()

    try:
        project_path = config.active_project_path
        if not project_path:
            console.print("[red]✗ 未找到活跃项目[/red]")
            raise ValueError("未找到活跃项目")

        # 从文件加载
        if from_file:
            file_path = Path(from_file)
            if not file_path.exists():
                console.print(f"[red]✗ 文件不存在: {from_file}[/red]")
                raise ValueError(f"文件不存在: {from_file}")

            if file_path.suffix in [".yaml", ".yml"]:
                with open(file_path, "r", encoding="utf-8") as f:
                    dataset_data = yaml.safe_load(f)
            elif file_path.suffix == ".json":
                with open(file_path, "r", encoding="utf-8") as f:
                    dataset_data = json.load(f)
            else:
                console.print(f"[red]✗ 不支持的文件格式: {file_path.suffix}[/red]")
                raise ValueError(f"不支持的文件格式")

            console.print(f"[dim]从文件加载: {from_file}[/dim]")
        else:
            # 交互式创建
            dataset_data = _interactive_create_dataset(dataset_id, name, description)

        # 覆盖 ID
        dataset_data["id"] = dataset_id

        # 保存
        dataset_dir = Path(project_path) / ".tlo" / "quality" / "datasets"
        dataset_dir.mkdir(parents=True, exist_ok=True)

        dataset_file = dataset_dir / f"{dataset_id}.yaml"
        if dataset_file.exists():
            console.print(f"[yellow]⚠️  数据集已存在: {dataset_id}[/yellow]")
            from rich.prompt import Confirm
            if not Confirm.ask("是否覆盖?", default=False):
                console.print("[dim]已取消[/dim]")
                return

        with open(dataset_file, "w", encoding="utf-8") as f:
            yaml.dump(dataset_data, f, allow_unicode=True, default_flow_style=False)

        console.print(f"[green]✓ 数据集已创建: {dataset_id}[/green]")
        console.print(f"[dim]文件: {dataset_file}[/dim]")

        # 显示详情
        if output_format == "table":
            _print_dataset_detail(dataset_data, dataset_file)
        elif output_format == "json":
            print(json.dumps(dataset_data, ensure_ascii=False, indent=2))
        elif output_format == "yaml":
            print(yaml.dump(dataset_data, allow_unicode=True, default_flow_style=False))

    except Exception as e:
        console.print(f"[red]✗ 创建失败: {e}[/red]")
        raise


def _interactive_create_dataset(dataset_id: str, name: str = None, description: str = None) -> dict:
    """交互式创建数据集。"""
    from rich.prompt import Prompt

    dataset_name = name or Prompt.ask("数据集名称", default=dataset_id.replace("-", " ").title())
    dataset_desc = description or Prompt.ask("数据集描述", default="")

    console.print("\n[yellow]⚠️  样本需要在 YAML 文件中手动添加[/yellow]")
    console.print("[dim]样本格式:[/dim]")
    console.print("[dim]  - input: {module: 'equipment', page: 'page1'}[/dim]")
    console.print("[dim]    expected_output: {action_count: 5}[/dim]")

    return {
        "id": dataset_id,
        "name": dataset_name,
        "description": dataset_desc,
        "samples": [],
        "tags": [],
        "metadata": {},
    }


def _print_dataset_detail(dataset_data: dict, file_path: Path):
    """打印数据集详细信息。"""
    console.print(f"\n[bold cyan]{dataset_data.get('id', 'Dataset')}[/bold cyan]")
    console.print(f"[bold]{dataset_data.get('name', '')}[/bold]")
    if dataset_data.get("description"):
        console.print(f"[dim]{dataset_data['description']}[/dim]")
    console.print(f"[dim]文件: {file_path}[/dim]\n")

    # 样本统计
    samples = dataset_data.get("samples", [])
    console.print(f"[bold]样本数:[/bold] {len(samples)}")

    if samples:
        console.print(f"\n[bold]样本预览（前 3 个）:[/bold]")
        for i, sample in enumerate(samples[:3], 1):
            console.print(f"\n[cyan]{i}.[/cyan]")
            console.print(f"  Input: {sample.get('input', {})}")
            console.print(f"  Expected: {sample.get('expected_output', {})}")

    # 标签
    tags = dataset_data.get("tags", [])
    if tags:
        console.print(f"\n[bold]标签:[/bold] {', '.join(tags)}")

    # 元数据
    metadata = dataset_data.get("metadata", {})
    if metadata:
        console.print(f"\n[bold]元数据:[/bold]")
        for key, value in metadata.items():
            console.print(f"  {key}: {value}")

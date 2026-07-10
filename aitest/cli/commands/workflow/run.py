"""workflow run 命令 — 执行 Workflow。

执行 Workflow 定义的测试流程，支持参数传递和结果输出。
"""

import json
from pathlib import Path
from rich.console import Console

console = Console()


def run_command(
    workflow_id: str,
    input_data: str = None,
    input_file: str = None,
    module: str = None,
    pages: str = None,
    env: str = None,
    provider: str = None,
    mock_llm: bool = False,
    wait: bool = True,
    output_format: str = "table",
):
    """执行 Workflow。

    示例:
        # 基本执行
        aitest workflow run my-workflow

        # 传递输入数据
        aitest workflow run my-workflow --input-data='{"module": "equipment"}'

        # 从文件读取输入
        aitest workflow run my-workflow --input-file=input.json

        # 指定模块和页面
        aitest workflow run my-workflow --module=equipment --pages=page1,page2
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
            raise ValueError(f"Workflow 不存在: {workflow_id}")

        console.print(f"[bold]执行 Workflow: {workflow_id}[/bold]\n")

        # 准备输入数据
        workflow_input = {}

        # 1. 从命令行参数构建
        if module:
            workflow_input["module"] = module
        if pages:
            workflow_input["pages"] = [p.strip() for p in pages.split(",")]
        if env:
            workflow_input["env"] = env

        # 2. 从 JSON 字符串读取
        if input_data:
            import json
            workflow_input.update(json.loads(input_data))

        # 3. 从文件读取
        if input_file:
            file_path = Path(input_file)
            if file_path.exists():
                with open(file_path, "r", encoding="utf-8") as f:
                    if file_path.suffix == ".json":
                        workflow_input.update(json.load(f))
                    elif file_path.suffix in [".yaml", ".yml"]:
                        import yaml
                        workflow_input.update(yaml.safe_load(f))
            else:
                console.print(f"[yellow]⚠️  输入文件不存在: {input_file}[/yellow]")

        console.print("[dim]输入参数:[/dim]")
        console.print(f"[dim]{json.dumps(workflow_input, ensure_ascii=False, indent=2)}[/dim]\n")

        # 转换为 run create 命令
        console.print("[dim]将 Workflow 转换为 Run...[/dim]")

        # 调用 run create
        from aitest.cli.commands.run.create import run_create
        run_create(
            target=f"workflow:{workflow_id}",
            module=module,
            pages=pages,
            env=env,
            provider=provider,
            mock_llm=mock_llm,
            wait=wait,
            output=output_format,
        )

    except Exception as e:
        console.print(f"[red]✗ 执行失败: {e}[/red]")
        raise

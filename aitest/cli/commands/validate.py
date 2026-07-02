"""
validate 命令 — 检查项目配置是否合法。

用法:
    alice validate --project-path ...
"""

from pathlib import Path

from rich.console import Console
from rich.table import Table

console = Console()


def validate_command(project_path: str):
    """检查项目配置是否合法。"""
    project_dir = Path(project_path)

    console.print(f"\n[bold]检查项目: {project_path}[/bold]\n")

    # 检查结果
    results = []

    # 1. 检查项目目录
    if project_dir.exists():
        results.append(("项目目录", "✅", "存在"))
    else:
        results.append(("项目目录", "❌", "不存在"))
        _print_results(results)
        return

    # 2. 检查 .tlo 目录
    tlo_dir = project_dir / ".tlo"
    if tlo_dir.exists():
        results.append((".tlo 目录", "✅", "存在"))
    else:
        results.append((".tlo 目录", "⚠️", "不存在 (将创建)"))

    # 3. 检查 project.yaml
    project_yaml = tlo_dir / "project.yaml"
    if project_yaml.exists():
        results.append(("project.yaml", "✅", "存在"))

        # 验证 YAML 格式
        try:
            import yaml
            with open(project_yaml, "r", encoding="utf-8") as f:
                data = yaml.safe_load(f)

            # 检查必填字段
            if data.get("project", {}).get("id"):
                results.append(("项目 ID", "✅", data["project"]["id"]))
            else:
                results.append(("项目 ID", "❌", "缺失"))

            if data.get("connection", {}).get("base_url"):
                results.append(("目标 URL", "✅", data["connection"]["base_url"]))
            else:
                results.append(("目标 URL", "❌", "缺失"))

            if data.get("application", {}).get("type"):
                results.append(("应用类型", "✅", data["application"]["type"]))
            else:
                results.append(("应用类型", "⚠️", "未配置"))

            if data.get("test_project", {}).get("type"):
                results.append(("测试框架", "✅", data["test_project"]["type"]))
            else:
                results.append(("测试框架", "⚠️", "未配置"))

        except Exception as e:
            results.append(("project.yaml", "❌", f"格式错误: {e}"))
    else:
        results.append(("project.yaml", "❌", "不存在"))

    # 4. 检查 test_accounts.yaml
    accounts_yaml = tlo_dir / "context" / "test_accounts.yaml"
    if accounts_yaml.exists():
        results.append(("test_accounts.yaml", "✅", "存在"))
    else:
        results.append(("test_accounts.yaml", "⚠️", "不存在 (可选)"))

    # 5. 检查 knowledge 目录
    knowledge_dir = tlo_dir / "knowledge" / "modules"
    if knowledge_dir.exists():
        modules = [d.name for d in knowledge_dir.iterdir() if d.is_dir()]
        results.append(("模块目录", "✅", f"{len(modules)} 个模块"))
    else:
        results.append(("模块目录", "⚠️", "不存在 (将创建)"))

    # 6. 检查 API 文档
    api_file = tlo_dir / "api" / "openapi.json"
    if api_file.exists():
        results.append(("API 文档", "✅", "存在"))
    else:
        results.append(("API 文档", "⚠️", "不存在 (可选)"))

    # 打印结果
    _print_results(results)


def _print_results(results: list):
    """打印检查结果表格。"""
    table = Table(title="项目配置检查")

    table.add_column("检查项", style="bold")
    table.add_column("状态", justify="center")
    table.add_column("说明")

    for item, status, detail in results:
        status_style = "green" if status == "✅" else ("yellow" if status == "⚠️" else "red")
        table.add_row(item, f"[{status_style}]{status}[/{status_style}]", detail)

    console.print(table)

    # 总结
    errors = sum(1 for _, status, _ in results if status == "❌")
    warnings = sum(1 for _, status, _ in results if status == "⚠️")

    console.print()
    if errors > 0:
        console.print(f"[red]❌ 发现 {errors} 个错误，需要修复[/red]")
    elif warnings > 0:
        console.print(f"[yellow]⚠️  发现 {warnings} 个警告，建议处理[/yellow]")
    else:
        console.print("[green]✅ 配置检查通过[/green]")

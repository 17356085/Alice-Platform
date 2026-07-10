"""
aitest agent versions — Agent 版本管理。

列出 Agent 的所有版本、对比版本差异。
"""

import typer
from typing import Optional
from rich.console import Console
from rich.table import Table
import yaml
from pathlib import Path

console = Console()


def versions_command(
    agent_id: str,
    output: str = "table",
):
    """列出 Agent 的所有版本。

    示例:
        aitest agent versions page-observer
        aitest agent versions page-observer --output json
    """
    from aitest.cli.config import CLIConfig

    config = CLIConfig()

    try:
        project_path = config.active_project_path
        if not project_path:
            console.print("[red]✗ 未找到活跃项目[/red]")
            raise ValueError("未找到活跃项目")

        # 查找 Agent 定义文件
        agent_locations = [
            Path(project_path) / ".tlo" / "agents" / f"{agent_id}.yaml",
            Path(project_path) / "governance" / "agents" / f"{agent_id}.yaml",
        ]

        agent_file = None
        for loc in agent_locations:
            if loc.exists():
                agent_file = loc
                break

        if not agent_file:
            console.print(f"[red]✗ Agent 不存在: {agent_id}[/red]")
            console.print("\n可用位置:")
            for loc in agent_locations:
                console.print(f"  {loc}")
            raise ValueError(f"Agent 不存在: {agent_id}")

        # 加载 Agent 定义
        with open(agent_file, "r", encoding="utf-8") as f:
            agent_data = yaml.safe_load(f)

        # 获取版本历史
        current_version = agent_data.get("version", "1.0.0")
        version_history = agent_data.get("version_history", [])

        # 如果没有历史记录，创建当前版本记录
        if not version_history:
            version_history = [{
                "version": current_version,
                "description": "当前版本",
                "date": agent_data.get("updated_at", "N/A"),
            }]

        # 输出
        if output == "json":
            import json
            result = {
                "agent_id": agent_id,
                "current_version": current_version,
                "versions": version_history,
            }
            print(json.dumps(result, ensure_ascii=False, indent=2))
            return
        elif output == "yaml":
            result = {
                "agent_id": agent_id,
                "current_version": current_version,
                "versions": version_history,
            }
            print(yaml.dump(result, allow_unicode=True, default_flow_style=False))
            return

        # 表格输出
        console.print(f"\n[bold]Agent: {agent_id}[/bold]")
        console.print(f"[dim]当前版本: {current_version}[/dim]\n")

        table = Table(title="版本历史")
        table.add_column("版本", style="cyan")
        table.add_column("描述")
        table.add_column("日期", style="dim")
        table.add_column("状态")

        for ver in version_history:
            version = ver.get("version", "")
            is_current = version == current_version
            status = "[green]✓ 当前[/green]" if is_current else ""

            table.add_row(
                version,
                ver.get("description", ""),
                ver.get("date", "")[:10] if ver.get("date") else "",
                status,
            )

        console.print(table)
        console.print(f"\n[dim]总计: {len(version_history)} 个版本[/dim]")

    except Exception as e:
        console.print(f"[red]✗ 列出版本失败: {e}[/red]")
        raise


def diff_command(
    agent_id: str,
    from_version: str,
    to_version: str,
    output: str = "table",
):
    """对比两个版本的差异。

    示例:
        aitest agent diff page-observer --from 1.0.0 --to 2.0.0
    """
    from aitest.cli.config import CLIConfig

    config = CLIConfig()

    try:
        project_path = config.active_project_path
        if not project_path:
            console.print("[red]✗ 未找到活跃项目[/red]")
            raise ValueError("未找到活跃项目")

        # 查找 Agent 定义文件
        agent_locations = [
            Path(project_path) / ".tlo" / "agents" / f"{agent_id}.yaml",
            Path(project_path) / "governance" / "agents" / f"{agent_id}.yaml",
        ]

        agent_file = None
        for loc in agent_locations:
            if loc.exists():
                agent_file = loc
                break

        if not agent_file:
            console.print(f"[red]✗ Agent 不存在: {agent_id}[/red]")
            raise ValueError(f"Agent 不存在: {agent_id}")

        console.print(f"\n[bold]Agent: {agent_id}[/bold]")
        console.print(f"[dim]对比版本: {from_version} → {to_version}[/dim]\n")

        console.print("[yellow]⚠️  版本对比功能需要完整的版本历史记录[/yellow]")
        console.print("[dim]提示: 在 Agent YAML 中添加 version_history 字段来跟踪变更[/dim]\n")

        # 模拟差异（简化版）
        console.print("[bold]主要变更:[/bold]")
        console.print("  • 版本号更新")
        console.print("  • 详细差异需要查看版本历史记录")

        console.print(f"\n[dim]建议: 使用 'git diff' 查看具体文件变更[/dim]")

    except Exception as e:
        console.print(f"[red]✗ 对比失败: {e}[/red]")
        raise

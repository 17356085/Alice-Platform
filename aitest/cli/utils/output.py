"""
CLI 输出格式化工具。

支持 table/json/yaml 三种输出格式。
"""

import json
import yaml
from typing import Any, List, Dict, Optional
from rich.console import Console
from rich.table import Table
from rich import box


console = Console()


def format_output(
    data: Any,
    output_format: str = "table",
    columns: Optional[List[str]] = None,
    title: Optional[str] = None,
):
    """
    统一输出格式化。

    Args:
        data: 数据（dict 或 list of dict）
        output_format: 输出格式 (table/json/yaml)
        columns: 表格列名（仅 table 格式）
        title: 表格标题（仅 table 格式）
    """
    if output_format == "json":
        print(json.dumps(data, indent=2, ensure_ascii=False))
    elif output_format == "yaml":
        print(yaml.dump(data, allow_unicode=True, default_flow_style=False))
    elif output_format == "table":
        _print_table(data, columns=columns, title=title)
    else:
        raise ValueError(f"不支持的输出格式: {output_format}")


def _print_table(
    data: Any,
    columns: Optional[List[str]] = None,
    title: Optional[str] = None,
):
    """
    打印表格。

    Args:
        data: 数据（dict 或 list of dict）
        columns: 列名（None 表示自动检测）
        title: 表格标题
    """
    # 标准化为 list of dict
    if isinstance(data, dict):
        rows = [data]
    elif isinstance(data, list):
        rows = data
    else:
        console.print(str(data))
        return

    if not rows:
        console.print("[yellow]无数据[/yellow]")
        return

    # 自动检测列名
    if columns is None:
        columns = list(rows[0].keys())

    # 创建表格
    table = Table(
        title=title,
        box=box.ROUNDED,
        show_header=True,
        header_style="bold cyan",
    )

    # 添加列
    for col in columns:
        table.add_column(col, style="white")

    # 添加行
    for row in rows:
        table.add_row(*[_format_cell(row.get(col)) for col in columns])

    console.print(table)


def _format_cell(value: Any) -> str:
    """
    格式化单元格值。

    Args:
        value: 单元格值

    Returns:
        格式化后的字符串
    """
    if value is None:
        return "[dim]N/A[/dim]"
    elif isinstance(value, bool):
        return "[green]✓[/green]" if value else "[red]✗[/red]"
    elif isinstance(value, (list, dict)):
        return json.dumps(value, ensure_ascii=False)[:50] + "..."
    else:
        return str(value)


def print_success(message: str):
    """打印成功消息。"""
    console.print(f"[green]✓[/green] {message}")


def print_error(message: str):
    """打印错误消息。"""
    console.print(f"[red]✗[/red] {message}")


def print_warning(message: str):
    """打印警告消息。"""
    console.print(f"[yellow]⚠[/yellow] {message}")


def print_info(message: str):
    """打印信息消息。"""
    console.print(f"[blue]ℹ[/blue] {message}")


def print_deprecation_warning(old_command: str, new_command: str, removal_date: str = "2026-12-31"):
    """
    打印废弃警告。

    Args:
        old_command: 旧命令
        new_command: 新命令
        removal_date: 移除日期
    """
    console.print()
    console.print(f"[yellow]⚠️  '{old_command}' 已废弃（将在 {removal_date} 移除）[/yellow]")
    console.print(f"[yellow]   请使用: {new_command}[/yellow]")
    console.print()

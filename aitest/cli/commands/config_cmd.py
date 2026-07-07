"""config 命令 — 管理 CLI 配置。

用法:
    alice config show                          # 显示完整配置
    alice config get <key>                     # 获取配置值
    alice config set <key> <value>             # 设置配置值
    alice config reset                         # 恢复默认配置
"""

from rich.console import Console
from rich.table import Table

console = Console()


def config_command(
    action: str,
    key: str | None = None,
    value: str | None = None,
):
    """管理 CLI 配置。"""
    from aitest.cli.config import CLIConfig, CONFIG_FILE

    config = CLIConfig()

    if action == "show":
        _show_config(config)
    elif action == "get":
        if not key:
            console.print("[red]❌ 请指定配置键[/red]")
            console.print("  用法: alice config get <key>")
            return
        _get_config(config, key)
    elif action == "set":
        if not key or not value:
            console.print("[red]❌ 请指定配置键和值[/red]")
            console.print("  用法: alice config set <key> <value>")
            return
        _set_config(config, key, value)
    elif action == "reset":
        _reset_config(config)
    else:
        console.print(f"[red]❌ 未知操作: {action}[/red]")
        console.print("  可用操作: show, get, set, reset")


def _show_config(config):
    """显示完整配置。"""
    data = config.get_all()

    table = Table(title="CLI 配置")
    table.add_column("键", style="bold")
    table.add_column("值")

    _flatten_dict(data, "", table)

    console.print(table)
    console.print(f"\n[dim]配置文件: {config.CONFIG_FILE if hasattr(config, 'CONFIG_FILE') else '~/.alice/config.yaml'}[/dim]")


def _flatten_dict(data: dict, prefix: str, table: Table):
    """递归展平字典到表格行。"""
    for key, value in data.items():
        full_key = f"{prefix}.{key}" if prefix else key
        if isinstance(value, dict):
            _flatten_dict(value, full_key, table)
        else:
            table.add_row(full_key, str(value))


def _get_config(config, key: str):
    """获取配置值。"""
    value = config.get(key)
    if value is not None:
        console.print(f"{key} = {value}")
    else:
        console.print(f"[yellow]⚠️  配置项 {key} 不存在[/yellow]")


def _set_config(config, key: str, value: str):
    """设置配置值。"""
    # 类型转换
    if value.lower() == "true":
        value = True
    elif value.lower() == "false":
        value = False
    elif value.isdigit():
        value = int(value)

    config.set(key, value)
    console.print(f"[green]✅ {key} = {value}[/green]")


def _reset_config(config):
    """恢复默认配置。"""
    from aitest.cli.config import DEFAULTS, CONFIG_FILE
    import yaml

    from rich.prompt import Confirm
    if not Confirm.ask("确认恢复默认配置?"):
        console.print("[yellow]已取消[/yellow]")
        return

    CONFIG_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(CONFIG_FILE, "w", encoding="utf-8") as f:
        yaml.dump(DEFAULTS, f, allow_unicode=True, default_flow_style=False)

    console.print("[green]✅ 配置已恢复默认[/green]")

"""provider list/show 命令 — ModelProvider 资源管理。

Provider 管理 LLM 模型连接配置。
"""

import json
import yaml
from pathlib import Path
from rich.console import Console
from rich.table import Table

console = Console()


def list_command(output_format: str = "table"):
    """列出所有 Provider。

    示例:
        aitest provider list
        aitest provider list --output json
    """
    from aitest.cli.config import CLIConfig

    config = CLIConfig()

    try:
        project_path = config.active_project_path
        if not project_path:
            console.print("[red]✗ 未找到活跃项目[/red]")
            raise ValueError("未找到活跃项目")

        provider_dir = Path(project_path) / ".tlo" / "providers"

        # 内置 Provider
        builtin_providers = [
            {
                "id": "deepseek",
                "name": "DeepSeek",
                "type": "openai-compatible",
                "model": "deepseek-chat",
                "source": "builtin",
                "enabled": True,
            },
            {
                "id": "claude",
                "name": "Anthropic Claude",
                "type": "anthropic",
                "model": "claude-3-5-sonnet-20241022",
                "source": "builtin",
                "enabled": True,
            },
            {
                "id": "openai",
                "name": "OpenAI",
                "type": "openai",
                "model": "gpt-4o",
                "source": "builtin",
                "enabled": True,
            },
            {
                "id": "gemini",
                "name": "Google Gemini",
                "type": "google",
                "model": "gemini-2.0-flash-exp",
                "source": "builtin",
                "enabled": True,
            },
        ]

        providers = builtin_providers.copy()

        # 扫描自定义 Provider
        if provider_dir.exists():
            for file_path in provider_dir.glob("*.yaml"):
                try:
                    with open(file_path, "r", encoding="utf-8") as f:
                        data = yaml.safe_load(f)
                        if data:
                            providers.append({
                                "id": data.get("id", file_path.stem),
                                "name": data.get("name", ""),
                                "type": data.get("type", ""),
                                "model": data.get("model", ""),
                                "source": "custom",
                                "enabled": data.get("enabled", True),
                            })
                except Exception as e:
                    console.print(f"[yellow]⚠️  无法解析 {file_path.name}: {e}[/yellow]")

        # 输出
        if output_format == "json":
            print(json.dumps(providers, ensure_ascii=False, indent=2))
            return
        elif output_format == "yaml":
            print(yaml.dump(providers, allow_unicode=True, default_flow_style=False))
            return

        # 表格输出
        table = Table(title=f"Model Providers ({len(providers)})")
        table.add_column("ID", style="bold cyan")
        table.add_column("名称")
        table.add_column("类型")
        table.add_column("模型", style="dim")
        table.add_column("来源")
        table.add_column("状态")

        for pv in providers:
            status_str = "[green]✓[/green]" if pv["enabled"] else "[dim]✗[/dim]"
            source_color = "yellow" if pv["source"] == "custom" else "dim"

            table.add_row(
                pv["id"],
                pv["name"],
                pv["type"],
                pv["model"],
                f"[{source_color}]{pv['source']}[/{source_color}]",
                status_str,
            )

        console.print(table)

        # 当前配置
        active_provider = config.resolve_llm_provider()
        console.print(f"\n[dim]当前配置: {active_provider}[/dim]")
        console.print(f"[dim]环境变量: LLM_PROVIDER={active_provider}[/dim]")

    except Exception as e:
        console.print(f"[red]✗ 列出失败: {e}[/red]")
        raise


def show_command(provider_id: str, output_format: str = "table"):
    """显示 Provider 详情。

    示例:
        aitest provider show deepseek
        aitest provider show my-provider --output json
    """
    from aitest.cli.config import CLIConfig

    config = CLIConfig()

    try:
        # 内置 Provider 配置
        builtin_configs = {
            "deepseek": {
                "id": "deepseek",
                "name": "DeepSeek",
                "type": "openai-compatible",
                "model": "deepseek-chat",
                "base_url": "https://api.deepseek.com/v1",
                "api_key_env": "DEEPSEEK_API_KEY",
                "temperature": 0.7,
                "max_tokens": 4096,
                "source": "builtin",
            },
            "claude": {
                "id": "claude",
                "name": "Anthropic Claude",
                "type": "anthropic",
                "model": "claude-3-5-sonnet-20241022",
                "base_url": "https://api.anthropic.com",
                "api_key_env": "ANTHROPIC_API_KEY",
                "temperature": 0.7,
                "max_tokens": 8192,
                "source": "builtin",
            },
            "openai": {
                "id": "openai",
                "name": "OpenAI",
                "type": "openai",
                "model": "gpt-4o",
                "base_url": "https://api.openai.com/v1",
                "api_key_env": "OPENAI_API_KEY",
                "temperature": 0.7,
                "max_tokens": 4096,
                "source": "builtin",
            },
            "gemini": {
                "id": "gemini",
                "name": "Google Gemini",
                "type": "google",
                "model": "gemini-2.0-flash-exp",
                "api_key_env": "GOOGLE_API_KEY",
                "temperature": 0.7,
                "max_tokens": 8192,
                "source": "builtin",
            },
        }

        # 优先从内置配置获取
        if provider_id in builtin_configs:
            provider_data = builtin_configs[provider_id]
        else:
            # 从自定义配置获取
            project_path = config.active_project_path
            if not project_path:
                console.print("[red]✗ 未找到活跃项目[/red]")
                raise ValueError("未找到活跃项目")

            provider_dir = Path(project_path) / ".tlo" / "providers"
            provider_file = provider_dir / f"{provider_id}.yaml"

            if not provider_file.exists():
                console.print(f"[red]✗ Provider 不存在: {provider_id}[/red]")
                console.print("\n可用的内置 Provider:")
                for pid in builtin_configs.keys():
                    console.print(f"  - {pid}")
                raise ValueError(f"Provider 不存在: {provider_id}")

            with open(provider_file, "r", encoding="utf-8") as f:
                provider_data = yaml.safe_load(f)

        # 输出
        if output_format == "json":
            print(json.dumps(provider_data, ensure_ascii=False, indent=2))
            return
        elif output_format == "yaml":
            print(yaml.dump(provider_data, allow_unicode=True, default_flow_style=False))
            return

        # 表格输出
        _print_provider_detail(provider_data)

    except Exception as e:
        console.print(f"[red]✗ 显示失败: {e}[/red]")
        raise


def _print_provider_detail(provider_data: dict):
    """打印 Provider 详细信息。"""
    console.print(f"\n[bold cyan]{provider_data.get('id', 'Provider')}[/bold cyan]")
    console.print(f"[bold]{provider_data.get('name', '')}[/bold]")
    console.print(f"[dim]来源: {provider_data.get('source', 'custom')}[/dim]\n")

    console.print("[bold]配置:[/bold]")
    console.print(f"  类型: {provider_data.get('type', '')}")
    console.print(f"  模型: {provider_data.get('model', '')}")

    if provider_data.get("base_url"):
        console.print(f"  Base URL: {provider_data['base_url']}")

    if provider_data.get("api_key_env"):
        import os
        api_key_set = "✓ 已设置" if os.getenv(provider_data["api_key_env"]) else "✗ 未设置"
        console.print(f"  API Key: ${provider_data['api_key_env']} ({api_key_set})")

    console.print(f"\n[bold]参数:[/bold]")
    console.print(f"  Temperature: {provider_data.get('temperature', 0.7)}")
    console.print(f"  Max Tokens: {provider_data.get('max_tokens', 4096)}")

    if provider_data.get("extra_params"):
        console.print(f"\n[bold]额外参数:[/bold]")
        for key, value in provider_data["extra_params"].items():
            console.print(f"  {key}: {value}")

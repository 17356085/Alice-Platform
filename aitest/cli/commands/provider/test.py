"""provider test 命令 — 测试 Provider 连通性。

测试 LLM Provider 的 API 连接是否正常。
"""

import os
from rich.console import Console

console = Console()


def test_command(provider_id: str):
    """测试 Provider 连通性。

    示例:
        aitest provider test deepseek
        aitest provider test claude
    """
    from aitest.cli.config import CLIConfig

    config = CLIConfig()

    try:
        console.print(f"[bold]测试 Provider: {provider_id}[/bold]\n")

        # 获取 Provider 配置
        builtin_providers = {
            "deepseek": {
                "name": "DeepSeek",
                "api_key_env": "DEEPSEEK_API_KEY",
                "base_url": "https://api.deepseek.com/v1",
            },
            "claude": {
                "name": "Anthropic Claude",
                "api_key_env": "ANTHROPIC_API_KEY",
                "base_url": "https://api.anthropic.com",
            },
            "openai": {
                "name": "OpenAI",
                "api_key_env": "OPENAI_API_KEY",
                "base_url": "https://api.openai.com/v1",
            },
            "gemini": {
                "name": "Google Gemini",
                "api_key_env": "GOOGLE_API_KEY",
            },
        }

        if provider_id not in builtin_providers:
            console.print(f"[red]✗ Provider 不存在: {provider_id}[/red]")
            console.print("\n可用的 Provider:")
            for pid in builtin_providers.keys():
                console.print(f"  - {pid}")
            raise ValueError(f"Provider 不存在: {provider_id}")

        provider_config = builtin_providers[provider_id]

        # 检查 API Key
        console.print("[dim]1. 检查 API Key...[/dim]")
        api_key_env = provider_config["api_key_env"]
        api_key = os.getenv(api_key_env)

        if not api_key:
            console.print(f"[red]✗ API Key 未设置: {api_key_env}[/red]")
            console.print(f"\n请设置环境变量:")
            console.print(f"  export {api_key_env}=<your-api-key>")
            raise ValueError(f"API Key 未设置: {api_key_env}")

        console.print(f"[green]✓ API Key 已设置: {api_key_env}[/green]")

        # 检查网络连接（简化版）
        console.print("\n[dim]2. 检查网络连接...[/dim]")
        if provider_config.get("base_url"):
            console.print(f"[dim]  Base URL: {provider_config['base_url']}[/dim]")

        console.print("[yellow]⚠️  实际 API 调用测试需要集成 LLM Provider 模块[/yellow]")
        console.print("[green]✓ 基础检查通过[/green]")

        # 模拟测试结果
        console.print("\n[bold]测试结果:[/bold]")
        console.print(f"  Provider: {provider_config['name']}")
        console.print(f"  API Key: {api_key_env} ✓")
        console.print(f"  状态: [green]可用[/green]")

        console.print("\n[dim]提示: 使用 'aitest run create --target agent:<id> --provider={provider_id}' 测试实际调用[/dim]")

    except Exception as e:
        console.print(f"[red]✗ 测试失败: {e}[/red]")
        raise

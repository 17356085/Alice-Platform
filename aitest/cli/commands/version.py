"""version 命令 — 显示版本信息。"""

from rich.console import Console

console = Console()


def version_command():
    """显示版本信息。"""
    # 版本号
    try:
        from importlib.metadata import version
        cli_version = version("aitest")
    except Exception:
        cli_version = "dev"

    # 依赖版本
    deps = {}
    for pkg in ["typer", "rich", "httpx", "fastapi", "langgraph"]:
        try:
            from importlib.metadata import version as get_version
            deps[pkg] = get_version(pkg)
        except Exception:
            deps[pkg] = "N/A"

    console.print(f"\n[bold blue]Alice Engine[/bold blue] v{cli_version}")
    console.print()
    console.print("依赖:")
    for pkg, ver in deps.items():
        console.print(f"  {pkg}: {ver}")
    console.print()
    console.print("文档: https://github.com/your-org/alice-engine")
    console.print("配置: ~/.alice/config.yaml")

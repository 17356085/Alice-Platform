"""ecosystem 命令 — 查看平台/项目/扩展兼容性快照。"""

import json
from rich.console import Console
from rich.table import Table

console = Console()


def ecosystem_command(output_format: str | None = None):
    from aitest.platform.ecosystem import collect_ecosystem_snapshot
    snapshot = collect_ecosystem_snapshot()

    if output_format == "json":
        print(json.dumps(snapshot, ensure_ascii=False, indent=2))
        return

    table = Table(title="生态控制面快照")
    table.add_column("项目")
    table.add_column("Schema")
    table.add_column("发现策略")
    table.add_column("模块数", justify="right")
    table.add_column("兼容性")

    for project in snapshot.get("projects", []):
        compat = project.get("compatibility", {})
        table.add_row(
            f"{project.get('name', '')} ({project.get('project_id', '')})",
            str(project.get("schema_version", "")),
            project.get("discovery_strategy", ""),
            str(project.get("module_count", 0)),
            f"{compat.get('status', '')}: {compat.get('detail', '')}",
        )

    console.print(table)
    console.print(
        f"\n[dim]平台版本: {snapshot.get('platform_version', '')} | "
        f"发现策略: {snapshot.get('discovery_strategy_count', 0)} 个 | "
        f"项目数: {snapshot.get('project_count', 0)}[/dim]"
    )


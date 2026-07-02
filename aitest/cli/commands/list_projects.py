"""
list-projects 命令 — 列出所有项目。

用法:
    alice list-projects --workspace ...
"""

from pathlib import Path

from rich.console import Console
from rich.table import Table

console = Console()


def list_projects_command(workspace: str):
    """列出所有项目。"""
    workspace_dir = Path(workspace)

    console.print(f"\n[bold]扫描工作目录: {workspace}[/bold]\n")

    if not workspace_dir.exists():
        console.print(f"[red]❌ 工作目录不存在: {workspace}[/red]")
        return

    # 扫描项目
    projects = []

    # 方式 1: 扫描 governance/context/projects/
    governance_projects = workspace_dir / "governance" / "context" / "projects"
    if governance_projects.exists():
        for d in governance_projects.iterdir():
            if d.is_dir() and (d / "project.yaml").exists():
                projects.append(_load_project_info(d))

    # 方式 2: 扫描 .tlo/project.yaml
    for d in workspace_dir.iterdir():
        if d.is_dir():
            tlo = d / ".tlo"
            if tlo.exists() and (tlo / "project.yaml").exists():
                projects.append(_load_project_info_from_tlo(d))

    if not projects:
        console.print("[yellow]⚠️  未找到任何项目[/yellow]")
        return

    # 显示项目列表
    table = Table(title="项目列表")

    table.add_column("ID", style="bold")
    table.add_column("名称")
    table.add_column("URL")
    table.add_column("类型")
    table.add_column("路径")

    for project in projects:
        table.add_row(
            project.get("id", ""),
            project.get("name", ""),
            project.get("url", ""),
            project.get("type", ""),
            project.get("path", ""),
        )

    console.print(table)


def _load_project_info(project_dir: Path) -> dict:
    """从 governance/context/projects/<id>/ 加载项目信息。"""
    import yaml

    project_yaml = project_dir / "project.yaml"
    try:
        with open(project_yaml, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f)

        return {
            "id": data.get("project", {}).get("id", project_dir.name),
            "name": data.get("project", {}).get("name", ""),
            "url": data.get("connection", {}).get("base_url", ""),
            "type": data.get("application", {}).get("type", ""),
            "path": str(project_dir),
        }
    except Exception:
        return {"id": project_dir.name, "path": str(project_dir)}


def _load_project_info_from_tlo(project_dir: Path) -> dict:
    """从 .tlo/project.yaml 加载项目信息。"""
    import yaml

    project_yaml = project_dir / ".tlo" / "project.yaml"
    try:
        with open(project_yaml, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f)

        return {
            "id": data.get("project", {}).get("id", project_dir.name),
            "name": data.get("project", {}).get("name", ""),
            "url": data.get("connection", {}).get("base_url", ""),
            "type": data.get("application", {}).get("type", ""),
            "path": str(project_dir),
        }
    except Exception:
        return {"id": project_dir.name, "path": str(project_dir)}

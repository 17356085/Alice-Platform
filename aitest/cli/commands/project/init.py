"""project init 命令 — 交互式项目配置 (Phase 0)。

当 project.yaml 不存在时，引导用户创建项目配置。
支持 InquirerPy TUI 和 Rich Prompt 两种模式。
"""

import sys
from pathlib import Path
from typing import Optional

import yaml
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

console = Console()


# ── 技术栈预设 ──────────────────────────────────────────────

PRESETS = [
    {"name": "Vue 3 + Element Plus (国内主流)", "category": "frontend", "framework": "vue3", "ui": "Element Plus"},
    {"name": "Vue 3 + Ant Design Vue", "category": "frontend", "framework": "vue3", "ui": "Ant Design Vue"},
    {"name": "React + Ant Design", "category": "frontend", "framework": "react", "ui": "Ant Design"},
    {"name": "React + Material UI", "category": "frontend", "framework": "react", "ui": "Material UI"},
    {"name": "Angular + Angular Material", "category": "frontend", "framework": "angular", "ui": "Angular Material"},
]


def init_command(project_path: str | None = None):
    """交互式项目配置。"""
    # 确定项目路径
    if not project_path:
        from rich.prompt import Prompt
        project_path = Prompt.ask("项目路径", default=str(Path.cwd()))

    project_dir = Path(project_path)
    tlo_dir = project_dir / ".tlo"
    project_yaml = tlo_dir / "project.yaml"

    if project_yaml.exists():
        console.print(f"[yellow][WARN]  项目配置已存在: {project_yaml}[/yellow]")
        from rich.prompt import Confirm
        if not Confirm.ask("是否覆盖?"):
            return

    console.print(Panel("[bold]Phase 0: Project Setup[/bold]", border_style="blue"))
    console.print()

    # 收集信息 (尝试 InquirerPy，fallback 到 Rich)
    try:
        config = _collect_with_inquirer()
    except ImportError:
        config = _collect_with_rich()

    if not config:
        console.print("[yellow]已取消[/yellow]")
        return

    # 显示摘要
    _show_summary(config)

    # 确认
    from rich.prompt import Confirm
    if not Confirm.ask("\n确认配置?"):
        console.print("[yellow]已取消[/yellow]")
        return

    # 生成文件
    _generate_files(str(project_dir), config)

    # 注册到 CLI config
    from aitest.cli.config import CLIConfig
    cli_config = CLIConfig()
    project_id = config.get("project_name", "").lower().replace(" ", "-")
    cli_config.register_project(project_id, str(project_dir), config.get("project_name", ""))

    console.print("[green][OK] Phase 0 配置完成[/green]")


def _collect_with_inquirer() -> dict | None:
    """使用 InquirerPy 收集信息。"""
    from InquirerPy import inquirer
    from InquirerPy.separator import Separator

    config = {}

    # 项目名称
    config["project_name"] = inquirer.text(
        message="项目名称:",
        validate=lambda x: 2 <= len(x) <= 50 or "需要 2-50 个字符",
    ).execute()

    # 技术栈
    choices = [{"name": p["name"], "value": i} for i, p in enumerate(PRESETS)]
    choices.append(Separator())
    choices.append({"name": "自定义", "value": -1})

    preset_idx = inquirer.select(message="技术栈:", choices=choices, default=0).execute()

    if preset_idx >= 0:
        preset = PRESETS[preset_idx]
        config["tech_stack"] = {
            "category": preset["category"],
            "framework": preset["framework"],
            "ui_library": preset["ui"],
        }
    else:
        config["tech_stack"] = {"category": "frontend", "framework": "custom", "ui_library": None}

    # 目标 URL
    config["base_url"] = inquirer.text(
        message="目标 URL:",
        validate=lambda x: x.startswith("http") or "需要 http:// 或 https:// 开头",
    ).execute()

    # 环境
    env_choices = [
        {"name": "dev (开发)", "value": "dev"},
        {"name": "staging (预发布)", "value": "staging"},
        {"name": "prod (生产)", "value": "prod"},
    ]
    config["environment"] = inquirer.select(message="环境类型:", choices=env_choices, default=1).execute()

    # 登录
    config["login_required"] = inquirer.confirm(message="需要登录?", default=True).execute()

    if config["login_required"]:
        login_choices = [
            {"name": "form (表单登录)", "value": "form"},
            {"name": "api (API 登录)", "value": "api"},
            {"name": "sso (SSO 单点登录)", "value": "sso"},
        ]
        config["login_method"] = inquirer.select(message="登录方式:", choices=login_choices, default=0).execute()

        # 测试账号
        accounts_str = inquirer.text(
            message="测试账号 (格式: 角色:用户名:密码，多个用分号分隔):",
        ).execute()
        config["test_accounts"] = _parse_accounts(accounts_str)
    else:
        config["login_method"] = None
        config["test_accounts"] = []

    # 测试框架
    fw_choices = [
        {"name": "pytest-selenium (Python + Selenium)", "value": "pytest-selenium"},
        {"name": "playwright (Python + Playwright)", "value": "playwright"},
        {"name": "cypress (JavaScript + Cypress)", "value": "cypress"},
    ]
    config["test_framework"] = inquirer.select(message="测试框架:", choices=fw_choices, default=0).execute()

    # 模块列表
    modules_str = inquirer.text(message="模块列表 (逗号分隔):").execute()
    config["modules"] = [m.strip() for m in modules_str.split(",") if m.strip()]

    return config


def _collect_with_rich() -> dict | None:
    """使用 Rich Prompt 收集信息 (fallback)。"""
    from rich.prompt import Prompt, Confirm

    config = {}

    # 项目名称
    config["project_name"] = Prompt.ask("项目名称")

    # 技术栈
    console.print("\n预设模板:")
    for i, preset in enumerate(PRESETS, 1):
        console.print(f"  [{i}] {preset['name']}")
    console.print("  [6] 自定义")

    choice = Prompt.ask("选择", choices=["1", "2", "3", "4", "5", "6"], default="1")
    if choice != "6":
        preset = PRESETS[int(choice) - 1]
        config["tech_stack"] = {
            "category": preset["category"],
            "framework": preset["framework"],
            "ui_library": preset["ui"],
        }
    else:
        config["tech_stack"] = {"category": "frontend", "framework": "custom", "ui_library": None}

    # 目标 URL
    config["base_url"] = Prompt.ask("目标 URL")

    # 环境
    console.print("\n环境类型:")
    console.print("  [1] dev  [2] staging  [3] prod")
    env_choice = Prompt.ask("选择", choices=["1", "2", "3"], default="2")
    config["environment"] = {"1": "dev", "2": "staging", "3": "prod"}[env_choice]

    # 登录
    config["login_required"] = Confirm.ask("需要登录?", default=True)
    if config["login_required"]:
        console.print("登录方式: [1] form  [2] api  [3] sso")
        login_choice = Prompt.ask("选择", choices=["1", "2", "3"], default="1")
        config["login_method"] = {"1": "form", "2": "api", "3": "sso"}[login_choice]

        console.print("测试账号 (格式: 角色:用户名:密码，留空结束):")
        accounts = []
        while True:
            line = Prompt.ask(">")
            if not line:
                break
            parsed = _parse_accounts(line)
            if parsed:
                accounts.extend(parsed)
                for a in parsed:
                    console.print(f"  [green][OK] 已添加: {a['role']} ({a['username']})[/green]")
        config["test_accounts"] = accounts
    else:
        config["login_method"] = None
        config["test_accounts"] = []

    # 测试框架
    console.print("\n测试框架:")
    console.print("  [1] pytest-selenium  [2] playwright  [3] cypress")
    fw_choice = Prompt.ask("选择", choices=["1", "2", "3"], default="1")
    config["test_framework"] = {"1": "pytest-selenium", "2": "playwright", "3": "cypress"}[fw_choice]

    # 模块列表
    modules_str = Prompt.ask("模块列表 (逗号分隔)")
    config["modules"] = [m.strip() for m in modules_str.split(",") if m.strip()]

    return config


def _parse_accounts(text: str) -> list:
    """解析测试账号字符串。"""
    accounts = []
    for part in text.split(";"):
        part = part.strip()
        if not part:
            continue
        parts = part.split(":")
        if len(parts) == 3:
            accounts.append({
                "role": parts[0].strip(),
                "username": parts[1].strip(),
                "password": parts[2].strip(),
            })
    return accounts


def _show_summary(config: dict):
    """显示配置摘要。"""
    table = Table(title="配置摘要")
    table.add_column("配置项", style="bold")
    table.add_column("值")

    table.add_row("项目名称", config.get("project_name", ""))
    table.add_row("技术栈", _format_tech_stack(config.get("tech_stack", {})))
    table.add_row("目标 URL", config.get("base_url", ""))
    table.add_row("环境", config.get("environment", ""))
    table.add_row("登录", "是" if config.get("login_required") else "否")
    if config.get("login_required"):
        table.add_row("登录方式", config.get("login_method", ""))
        table.add_row("测试账号", f"{len(config.get('test_accounts', []))} 个")
    table.add_row("测试框架", config.get("test_framework", ""))
    table.add_row("模块", ", ".join(config.get("modules", [])))

    console.print(table)


def _format_tech_stack(tech_stack: dict) -> str:
    """格式化技术栈。"""
    parts = []
    framework = tech_stack.get("framework", "")
    ui = tech_stack.get("ui_library")
    if framework:
        parts.append(framework)
    if ui:
        parts.append(ui)
    return " + ".join(parts) if parts else "未配置"


def _generate_files(project_path: str, config: dict):
    """生成配置文件。"""
    project_dir = Path(project_path)
    tlo_dir = project_dir / ".tlo"

    # 创建目录
    tlo_dir.mkdir(parents=True, exist_ok=True)
    (tlo_dir / "context").mkdir(exist_ok=True)
    (tlo_dir / "knowledge" / "modules").mkdir(parents=True, exist_ok=True)
    (tlo_dir / "runtime" / "sop-status").mkdir(parents=True, exist_ok=True)

    # 生成 project.yaml
    project_yaml = _build_project_yaml(config)
    with open(tlo_dir / "project.yaml", "w", encoding="utf-8") as f:
        yaml.dump(project_yaml, f, allow_unicode=True, default_flow_style=False)
    console.print("  [green][OK] .tlo/project.yaml 已生成[/green]")

    # 生成 test_accounts.yaml
    if config.get("test_accounts"):
        accounts_data = {"accounts": config["test_accounts"]}
        with open(tlo_dir / "context" / "test_accounts.yaml", "w", encoding="utf-8") as f:
            yaml.dump(accounts_data, f, allow_unicode=True, default_flow_style=False)
        console.print("  [green][OK] .tlo/context/test_accounts.yaml 已生成[/green]")

    # 创建模块目录
    for module in config.get("modules", []):
        module_dir = tlo_dir / "knowledge" / "modules" / module
        module_dir.mkdir(parents=True, exist_ok=True)
        (module_dir / "pages").mkdir(exist_ok=True)

    console.print(f"  [green][OK] {len(config.get('modules', []))} 个模块目录已创建[/green]")


def _build_project_yaml(config: dict) -> dict:
    """构建 project.yaml 数据。"""
    tech_stack = config.get("tech_stack", {})
    project_id = config.get("project_name", "").lower().replace(" ", "-")

    return {
        "version": 1,
        "project": {
            "id": project_id,
            "name": config.get("project_name", ""),
            "type": "web",
        },
        "application": {
            "type": "web",
            "tech_stack": {
                "frontend": {
                    "framework": tech_stack.get("framework", ""),
                    "ui_library": tech_stack.get("ui_library", ""),
                },
            },
        },
        "connection": {
            "base_url": config.get("base_url", ""),
            "environment": config.get("environment", "staging"),
            "login_required": config.get("login_required", False),
            "login_method": config.get("login_method", "form"),
        },
        "runtime": {
            "browser": "chrome",
            "headless": True,
            "window_size": "1920x1080",
        },
        "test_project": {
            "type": config.get("test_framework", "pytest-selenium"),
        },
    }

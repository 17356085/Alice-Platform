"""
Phase 0: Project Setup — 交互式项目配置。

当 project.yaml 不存在时，引导用户创建项目配置。

用法:
    在 run 命令中自动触发:
    alice run --project-path D:/.../NewProject --module equipment
"""

from pathlib import Path
from typing import Optional
import yaml

from rich.console import Console
from rich.panel import Panel
from rich.prompt import Prompt, Confirm
from rich.table import Table

console = Console()


# ── 技术栈分类 ──────────────────────────────────────────────────

TECH_STACKS = {
    "frontend": {
        "name": "前端",
        "frameworks": {
            "vue2": {"name": "Vue 2", "ui": ["Element UI", "Ant Design Vue", "Vuetify"], "default_state": "vuex", "default_lang": "javascript"},
            "vue3": {"name": "Vue 3", "ui": ["Element Plus", "Ant Design Vue", "Naive UI", "Vuetify"], "default_state": "pinia", "default_lang": "typescript"},
            "react": {"name": "React", "ui": ["Ant Design", "Material UI", "Chakra UI"], "default_state": "redux", "default_lang": "typescript"},
            "angular": {"name": "Angular", "ui": ["Angular Material", "NG-ZORRO", "PrimeNG"], "default_state": "ngrx", "default_lang": "typescript"},
            "svelte": {"name": "Svelte", "ui": ["Skeleton", "Flowbite"], "default_state": "svelte-store", "default_lang": "javascript"},
            "nextjs": {"name": "Next.js", "ui": ["Ant Design", "Material UI", "shadcn/ui"], "default_state": "redux", "default_lang": "typescript"},
            "nuxtjs": {"name": "Nuxt.js", "ui": ["Element Plus", "Vuetify", "Naive UI"], "default_state": "pinia", "default_lang": "typescript"},
        },
    },
    "backend": {
        "name": "后端",
        "frameworks": {
            "springboot": {"name": "Spring Boot", "lang": "Java"},
            "django": {"name": "Django", "lang": "Python"},
            "flask": {"name": "Flask", "lang": "Python"},
            "express": {"name": "Express", "lang": "Node.js"},
            "fastapi": {"name": "FastAPI", "lang": "Python"},
            "gin": {"name": "Gin", "lang": "Go"},
        },
    },
    "mobile": {
        "name": "移动端",
        "frameworks": {
            "reactnative": {"name": "React Native"},
            "flutter": {"name": "Flutter"},
            "swift": {"name": "Swift (iOS)"},
            "kotlin": {"name": "Kotlin (Android)"},
        },
    },
    "desktop": {
        "name": "桌面端",
        "frameworks": {
            "electron": {"name": "Electron"},
            "qt": {"name": "Qt"},
            "tauri": {"name": "Tauri"},
        },
    },
    "miniapp": {
        "name": "小程序",
        "frameworks": {
            "wechat": {"name": "微信小程序"},
            "alipay": {"name": "支付宝小程序"},
            "baidu": {"name": "百度小程序"},
            "uniapp": {"name": "uni-app"},
            "taro": {"name": "Taro"},
        },
    },
}

PRESETS = [
    {"name": "Vue 3 + Element Plus (国内主流)", "category": "frontend", "framework": "vue3", "ui": "Element Plus"},
    {"name": "Vue 3 + Ant Design Vue", "category": "frontend", "framework": "vue3", "ui": "Ant Design Vue"},
    {"name": "React + Ant Design", "category": "frontend", "framework": "react", "ui": "Ant Design"},
    {"name": "React + Material UI", "category": "frontend", "framework": "react", "ui": "Material UI"},
    {"name": "Angular + Angular Material", "category": "frontend", "framework": "angular", "ui": "Angular Material"},
]


# ── Phase 0 主流程 ──────────────────────────────────────────────

def phase0_interactive(project_path: str) -> dict:
    """Phase 0 交互式项目配置。

    Args:
        project_path: 项目路径

    Returns:
        生成的配置数据
    """
    console.print(Panel("[bold]Phase 0: Project Setup[/bold]", border_style="blue"))
    console.print()

    # 收集信息
    config = {}

    # 1. 项目名称
    config["project_name"] = _ask_project_name()

    # 2. 技术栈
    config["tech_stack"] = _ask_tech_stack()

    # 3. 目标 URL
    config["base_url"] = _ask_base_url()

    # 4. 环境类型
    config["environment"] = _ask_environment()

    # 5. 登录配置
    config["login"] = _ask_login()

    # 6. 测试账号
    if config["login"]["required"]:
        config["test_accounts"] = _ask_test_accounts()
    else:
        config["test_accounts"] = []

    # 7. 测试框架
    config["test_framework"] = _ask_test_framework()

    # 8. 模块列表
    config["modules"] = _ask_modules()

    # 9. API 文档 (可选)
    config["api_doc"] = _ask_api_doc()

    # 10. 质量门禁 (默认值)
    config["gates"] = {
        "pass_rate_threshold": 80,
        "skip_rate_threshold": 10,
        "p0_must_pass": True,
        "consider_bug_analysis": True,
    }

    # 显示配置摘要
    _show_summary(config)

    # 确认
    if not Confirm.ask("\n确认配置?"):
        console.print("[yellow]已取消[/yellow]")
        return None

    # 生成文件
    _generate_files(project_path, config)

    console.print("[green]✅ Phase 0 配置完成[/green]")
    return config


# ── 信息收集 ──────────────────────────────────────────────────

def _ask_project_name() -> str:
    """询问项目名称。"""
    while True:
        name = Prompt.ask("项目名称")
        if 2 <= len(name) <= 50:
            return name
        console.print("[red]⚠️  项目名称需要 2-50 个字符[/red]")


def _ask_tech_stack() -> dict:
    """询问技术栈。"""
    console.print("\n[bold]技术栈配置[/bold]")

    # 显示预设
    console.print("\n预设模板:")
    for i, preset in enumerate(PRESETS, 1):
        console.print(f"  [{i}] {preset['name']}")
    console.print("  [6] 自定义")

    choice = Prompt.ask("选择", choices=["1", "2", "3", "4", "5", "6"], default="1")

    if choice != "6":
        preset = PRESETS[int(choice) - 1]
        return {
            "category": preset["category"],
            "framework": preset["framework"],
            "ui_library": preset["ui"],
            "css_framework": None,
            "routing": "hash" if "vue" in preset["framework"] else "history",
            "state_management": TECH_STACKS["frontend"]["frameworks"][preset["framework"]]["default_state"],
            "typescript": TECH_STACKS["frontend"]["frameworks"][preset["framework"]]["default_lang"] == "typescript",
        }

    # 自定义
    return _ask_custom_tech_stack()


def _ask_custom_tech_stack() -> dict:
    """自定义技术栈。"""
    # 分类
    console.print("\n技术栈分类:")
    categories = list(TECH_STACKS.keys())
    for i, cat in enumerate(categories, 1):
        console.print(f"  [{i}] {TECH_STACKS[cat]['name']}")

    cat_choice = Prompt.ask("选择分类", choices=[str(i) for i in range(1, len(categories) + 1)])
    category = categories[int(cat_choice) - 1]

    # 框架
    frameworks = TECH_STACKS[category]["frameworks"]
    console.print(f"\n{TECH_STACKS[category]['name']}框架:")
    framework_keys = list(frameworks.keys())
    for i, key in enumerate(framework_keys, 1):
        console.print(f"  [{i}] {frameworks[key]['name']}")

    fw_choice = Prompt.ask("选择框架", choices=[str(i) for i in range(1, len(framework_keys) + 1)])
    framework = framework_keys[int(fw_choice) - 1]

    result = {
        "category": category,
        "framework": framework,
        "ui_library": None,
        "css_framework": None,
        "routing": None,
        "state_management": None,
        "typescript": None,
    }

    # UI 库 (仅前端)
    if category == "frontend" and "ui" in frameworks[framework]:
        ui_list = frameworks[framework]["ui"]
        console.print("\nUI 组件库:")
        for i, ui in enumerate(ui_list, 1):
            console.print(f"  [{i}] {ui}")
        console.print(f"  [{len(ui_list) + 1}] 跳过")

        ui_choice = Prompt.ask("选择", choices=[str(i) for i in range(1, len(ui_list) + 2)])
        if int(ui_choice) <= len(ui_list):
            result["ui_library"] = ui_list[int(ui_choice) - 1]

        # 默认值
        result["routing"] = "hash" if "vue" in framework else "history"
        result["state_management"] = frameworks[framework].get("default_state", "")
        result["typescript"] = frameworks[framework].get("default_lang", "javascript") == "typescript"

    return result


def _ask_base_url() -> str:
    """询问目标 URL。"""
    while True:
        url = Prompt.ask("目标 URL")
        if url.startswith("http://") or url.startswith("https://"):
            # 检查可访问性
            console.print(f"🔍 检查 URL 可访问性...")
            try:
                import httpx
                response = httpx.get(url, timeout=10, follow_redirects=True)
                if response.status_code < 500:
                    console.print("[green]✅ URL 可访问[/green]")
                    return url
                else:
                    console.print(f"[yellow]⚠️  URL 返回状态码 {response.status_code}[/yellow]")
                    if Confirm.ask("继续?"):
                        return url
            except Exception as e:
                console.print(f"[red]❌ URL 不可访问: {e}[/red]")
                console.print("[yellow]请检查 URL 是否正确，或网络是否通畅[/yellow]")
        else:
            console.print("[red]⚠️  URL 需要 http:// 或 https:// 开头[/red]")


def _ask_environment() -> str:
    """询问环境类型。"""
    console.print("\n环境类型:")
    console.print("  [1] dev (开发)")
    console.print("  [2] staging (预发布)")
    console.print("  [3] prod (生产)")

    choice = Prompt.ask("选择", choices=["1", "2", "3"], default="2")
    return {"1": "dev", "2": "staging", "3": "prod"}[choice]


def _ask_login() -> dict:
    """询问登录配置。"""
    required = Confirm.ask("\n需要登录?", default=True)

    if not required:
        return {"required": False, "method": None}

    console.print("\n登录方式:")
    console.print("  [1] form (表单登录)")
    console.print("  [2] api (API 登录)")
    console.print("  [3] sso (SSO 单点登录)")

    choice = Prompt.ask("选择", choices=["1", "2", "3"], default="1")
    method = {"1": "form", "2": "api", "3": "sso"}[choice]

    return {"required": True, "method": method}


def _ask_test_accounts() -> list:
    """询问测试账号。"""
    console.print("\n[bold]测试账号[/bold]")
    console.print("格式: 角色:用户名:密码 (留空结束)")

    accounts = []
    while True:
        line = Prompt.ask(">")
        if not line:
            break

        parts = line.split(":")
        if len(parts) != 3:
            console.print("[red]⚠️  格式不正确，需要: 角色:用户名:密码[/red]")
            continue

        role, username, password = parts
        accounts.append({
            "role": role.strip(),
            "username": username.strip(),
            "password": password.strip(),
        })
        console.print(f"[green]✅ 已添加: {role} ({username})[/green]")

    return accounts


def _ask_test_framework() -> str:
    """询问测试框架。"""
    console.print("\n测试框架:")
    console.print("  [1] pytest-selenium (Python + Selenium)")
    console.print("  [2] playwright (Python + Playwright)")
    console.print("  [3] cypress (JavaScript + Cypress)")

    choice = Prompt.ask("选择", choices=["1", "2", "3"], default="1")
    return {"1": "pytest-selenium", "2": "playwright", "3": "cypress"}[choice]


def _ask_modules() -> list:
    """询问模块列表。"""
    console.print("\n[bold]模块列表[/bold]")
    console.print("输入模块名 (逗号分隔):")

    modules_str = Prompt.ask("模块")
    modules = [m.strip() for m in modules_str.split(",") if m.strip()]

    return modules


def _ask_api_doc() -> dict:
    """询问 API 文档。"""
    from aitest.cli.commands.api_import import ask_api_doc
    return ask_api_doc()


# ── 显示摘要 ──────────────────────────────────────────────────

def _show_summary(config: dict):
    """显示配置摘要。"""
    console.print("\n")
    table = Table(title="配置摘要")

    table.add_column("配置项", style="bold")
    table.add_column("值")

    table.add_row("项目名称", config["project_name"])
    table.add_row("技术栈", _format_tech_stack(config["tech_stack"]))
    table.add_row("目标 URL", config["base_url"])
    table.add_row("环境", config["environment"])
    table.add_row("登录", "是" if config["login"]["required"] else "否")
    if config["login"]["required"]:
        table.add_row("登录方式", config["login"]["method"])
        table.add_row("测试账号", f"{len(config['test_accounts'])} 个")
    table.add_row("测试框架", config["test_framework"])
    table.add_row("模块", ", ".join(config["modules"]))
    table.add_row("API 文档", "有" if config["api_doc"] else "无")

    console.print(table)


def _format_tech_stack(tech_stack: dict) -> str:
    """格式化技术栈。"""
    parts = []

    # 框架
    category = tech_stack.get("category", "")
    framework = tech_stack.get("framework", "")
    if category and framework:
        framework_info = TECH_STACKS.get(category, {}).get("frameworks", {}).get(framework, {})
        parts.append(framework_info.get("name", framework))

    # UI 库
    ui = tech_stack.get("ui_library")
    if ui:
        parts.append(ui)

    return " + ".join(parts) if parts else "未配置"


# ── 生成文件 ──────────────────────────────────────────────────

def _generate_files(project_path: str, config: dict):
    """生成配置文件。"""
    project_dir = Path(project_path)
    tlo_dir = project_dir / ".tlo"

    # 创建目录
    tlo_dir.mkdir(parents=True, exist_ok=True)
    (tlo_dir / "context").mkdir(exist_ok=True)
    (tlo_dir / "knowledge" / "modules").mkdir(parents=True, exist_ok=True)
    if config.get("api_doc"):
        (tlo_dir / "api").mkdir(exist_ok=True)

    # 生成 project.yaml
    project_yaml = _build_project_yaml(config)
    with open(tlo_dir / "project.yaml", "w", encoding="utf-8") as f:
        yaml.dump(project_yaml, f, allow_unicode=True, default_flow_style=False)
    console.print("  [green]✅ .tlo/project.yaml 已生成[/green]")

    # 生成 test_accounts.yaml
    if config.get("test_accounts"):
        accounts_data = {"accounts": config["test_accounts"]}
        with open(tlo_dir / "context" / "test_accounts.yaml", "w", encoding="utf-8") as f:
            yaml.dump(accounts_data, f, allow_unicode=True, default_flow_style=False)
        console.print("  [green]✅ .tlo/context/test_accounts.yaml 已生成[/green]")

    # 创建模块目录
    for module in config.get("modules", []):
        module_dir = tlo_dir / "knowledge" / "modules" / module
        module_dir.mkdir(parents=True, exist_ok=True)
        (module_dir / "pages").mkdir(exist_ok=True)

    console.print(f"  [green]✅ {len(config.get('modules', []))} 个模块目录已创建[/green]")

    # 导入 API 文档
    if config.get("api_doc"):
        from aitest.cli.commands.api_import import import_api_doc
        import_api_doc(config["api_doc"], tlo_dir)


def _build_project_yaml(config: dict) -> dict:
    """构建 project.yaml 数据。"""
    tech_stack = config.get("tech_stack", {})

    return {
        "project": {
            "id": config.get("project_name", "").lower().replace(" ", "-"),
            "name": config.get("project_name", ""),
        },
        "application": {
            "type": "web",
            "tech_stack": {
                "frontend": {
                    "framework": tech_stack.get("framework", ""),
                    "ui_library": tech_stack.get("ui_library", ""),
                    "css_framework": tech_stack.get("css_framework", ""),
                    "routing": tech_stack.get("routing", ""),
                    "state_management": tech_stack.get("state_management", ""),
                    "typescript": tech_stack.get("typescript", False),
                },
            },
        },
        "connection": {
            "base_url": config.get("base_url", ""),
            "environment": config.get("environment", "staging"),
            "login_required": config.get("login", {}).get("required", False),
            "login_method": config.get("login", {}).get("method", "form"),
        },
        "runtime": {
            "browser": "chrome",
            "headless": True,
            "window_size": "1920x1080",
            "screenshot_on_failure": True,
        },
        "test_project": {
            "type": config.get("test_framework", "pytest-selenium"),
        },
        "data": {
            "cleanup_strategy": "api",
            "cleanup_after_test": True,
            "protected_resources": ["生产数据", "系统配置"],
            "custom_cleanup_requires_confirm": True,
        },
        "gates": config.get("gates", {}),
    }

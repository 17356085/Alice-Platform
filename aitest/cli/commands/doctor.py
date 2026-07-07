"""doctor 命令 — 环境诊断。

检查项:
  - Python 版本
  - pip 依赖
  - API Key
  - Chrome/ChromeDriver
  - Docker
  - PostgreSQL
  - 活跃项目
  - .tlo 结构
  - LangGraph
  - 前端构建
  - 端口冲突
  - 治理文件
"""

import sys
import socket
import importlib
from pathlib import Path
from dataclasses import dataclass
from typing import Callable

from rich.console import Console
from rich.table import Table

console = Console()


@dataclass
class CheckResult:
    """检查结果。"""
    status: str  # ok / warn / error
    detail: str
    fixable: bool = False
    fix_hint: str = ""


def doctor_command(
    fix: bool = False,
    output_format: str | None = None,
):
    """环境诊断。"""
    import json
    from aitest.cli.config import CLIConfig

    config = CLIConfig()
    resolved_format = config.resolve_output_format(output_format)

    checks = [
        ("Python 版本", check_python_version),
        ("pip 依赖", check_pip_dependencies),
        ("ANTHROPIC_API_KEY", check_anthropic_key),
        ("DEEPSEEK_API_KEY", check_deepseek_key),
        ("Chrome", check_chrome),
        ("ChromeDriver", check_chromedriver),
        ("Docker", check_docker),
        ("PostgreSQL", check_postgres),
        ("活跃项目", check_active_project),
        (".tlo 结构", check_tlo_structure),
        ("LangGraph", check_langgraph),
        ("前端构建", check_frontend_build),
        ("端口 8000", check_port),
        ("治理文件", check_governance),
    ]

    results = []
    for name, check_fn in checks:
        try:
            result = check_fn(fix=fix)
            results.append({"name": name, "status": result.status, "detail": result.detail})
        except Exception as e:
            results.append({"name": name, "status": "[FAIL]", "detail": str(e)})

    if resolved_format == "json":
        print(json.dumps(results, ensure_ascii=False, indent=2))
        return

    # table 格式
    table = Table(title="环境诊断")
    table.add_column("检查项", style="bold")
    table.add_column("状态", justify="center")
    table.add_column("说明")

    status_icons = {"ok": "[OK]", "warn": "[WARN]", "error": "[FAIL]"}

    for r in results:
        status = r["status"]
        icon = status_icons.get(status, status)
        status_style = "green" if status == "ok" else ("yellow" if status == "warn" else "red")
        table.add_row(
            r["name"],
            f"[{status_style}]{icon}[/{status_style}]",
            r["detail"],
        )

    console.print(table)

    # 总结
    ok = sum(1 for r in results if r["status"] == "ok")
    warn = sum(1 for r in results if r["status"] == "warn")
    err = sum(1 for r in results if r["status"] == "error")

    console.print(f"\n  [OK] {ok} 通过  [WARN] {warn} 警告  [FAIL] {err} 错误")

    if err > 0 or warn > 0:
        console.print("\n  修复建议:")
        for r in results:
            if r["status"] == "error":
                console.print(f"  [FAIL] {r['name']}: {r['detail']}")
            elif r["status"] == "warn":
                console.print(f"  [WARN]  {r['name']}: {r['detail']}")


# ── 检查函数 ──────────────────────────────────────────────

def check_python_version(fix: bool = False) -> CheckResult:
    """检查 Python 版本。"""
    version = sys.version_info
    if version >= (3, 10):
        return CheckResult("ok", f"{version.major}.{version.minor}.{version.micro}")
    else:
        return CheckResult("error", f"{version.major}.{version.minor}.{version.micro} (需要 >= 3.10)")


def check_pip_dependencies(fix: bool = False) -> CheckResult:
    """检查核心依赖。"""
    core_packages = [
        "typer", "rich", "httpx", "yaml", "fastapi", "uvicorn",
        "langchain", "langgraph", "chromadb",
    ]
    missing = []
    for pkg in core_packages:
        try:
            importlib.import_module(pkg)
        except ImportError:
            missing.append(pkg)

    if not missing:
        return CheckResult("ok", f"{len(core_packages)}/{len(core_packages)} 已安装")
    else:
        return CheckResult("warn", f"缺失: {', '.join(missing)}", fixable=True,
                          fix_hint="pip install -r requirements.txt")


def check_anthropic_key(fix: bool = False) -> CheckResult:
    """检查 Anthropic API Key。"""
    import os
    key = os.environ.get("ANTHROPIC_API_KEY", "")
    if key:
        masked = key[:8] + "***"
        return CheckResult("ok", masked)
    return CheckResult("warn", "未配置")


def check_deepseek_key(fix: bool = False) -> CheckResult:
    """检查 DeepSeek API Key。"""
    import os
    key = os.environ.get("DEEPSEEK_API_KEY", "")
    if key:
        masked = key[:8] + "***"
        return CheckResult("ok", masked)
    return CheckResult("warn", "未配置")


def check_chrome(fix: bool = False) -> CheckResult:
    """检查 Chrome。"""
    import subprocess
    try:
        if sys.platform == "win32":
            result = subprocess.run(
                ["where", "chrome"],
                capture_output=True, text=True, timeout=5,
            )
            if result.returncode == 0:
                return CheckResult("ok", "已安装")
        # 尝试直接启动
        from selenium import webdriver
        options = webdriver.ChromeOptions()
        options.add_argument("--headless")
        driver = webdriver.Chrome(options=options)
        version = driver.capabilities.get("browserVersion", "unknown")
        driver.quit()
        return CheckResult("ok", f"Chrome {version}")
    except Exception as e:
        return CheckResult("warn", f"未检测到: {e}")


def check_chromedriver(fix: bool = False) -> CheckResult:
    """检查 ChromeDriver。"""
    try:
        from selenium import webdriver
        options = webdriver.ChromeOptions()
        options.add_argument("--headless")
        driver = webdriver.Chrome(options=options)
        driver_version = driver.capabilities.get("chrome", {}).get("chromedriverVersion", "unknown")
        driver.quit()
        return CheckResult("ok", f"ChromeDriver {driver_version}")
    except Exception as e:
        return CheckResult("warn", f"未检测到: {e}")


def check_docker(fix: bool = False) -> CheckResult:
    """检查 Docker。"""
    import subprocess
    try:
        result = subprocess.run(
            ["docker", "--version"],
            capture_output=True, text=True, timeout=5,
        )
        if result.returncode == 0:
            return CheckResult("ok", result.stdout.strip())
        return CheckResult("warn", "未安装")
    except FileNotFoundError:
        return CheckResult("warn", "未安装")
    except Exception as e:
        return CheckResult("warn", str(e))


def check_postgres(fix: bool = False) -> CheckResult:
    """检查 PostgreSQL 连接。"""
    try:
        with socket.create_connection(("localhost", 5432), timeout=3):
            return CheckResult("ok", "localhost:5432 可达")
    except (ConnectionRefusedError, socket.timeout, OSError):
        return CheckResult("warn", "localhost:5432 不可达")


def check_active_project(fix: bool = False) -> CheckResult:
    """检查活跃项目。"""
    from aitest.cli.config import CLIConfig
    config = CLIConfig()
    project_id = config.active_project
    if project_id:
        path = config.active_project_path
        if path and Path(path).exists():
            return CheckResult("ok", project_id)
        return CheckResult("warn", f"{project_id} (路径不存在)")
    return CheckResult("warn", "未设置活跃项目")


def check_tlo_structure(fix: bool = False) -> CheckResult:
    """检查 .tlo 结构。"""
    from aitest.cli.config import CLIConfig
    config = CLIConfig()
    path = config.active_project_path
    if not path:
        return CheckResult("warn", "无活跃项目")

    tlo_dir = Path(path) / ".tlo"
    if not tlo_dir.exists():
        return CheckResult("error", ".tlo 目录不存在")

    project_yaml = tlo_dir / "project.yaml"
    if not project_yaml.exists():
        return CheckResult("error", "project.yaml 不存在")

    return CheckResult("ok", "project.yaml 存在")


def check_langgraph(fix: bool = False) -> CheckResult:
    """检查 LangGraph checkpoint。"""
    try:
        import langgraph.checkpoint.sqlite
        return CheckResult("ok", "sqlite checkpoint 可用")
    except ImportError:
        return CheckResult("warn", "langgraph-checkpoint-sqlite 未安装")


def check_frontend_build(fix: bool = False) -> CheckResult:
    """检查前端构建。"""
    dist_dir = Path(__file__).parent.parent.parent / "web" / "dist"
    if dist_dir.exists():
        return CheckResult("ok", "dist/ 存在")
    return CheckResult("warn", "dist/ 不存在")


def check_port(fix: bool = False) -> CheckResult:
    """检查端口 8000。"""
    try:
        with socket.create_connection(("localhost", 8000), timeout=2):
            return CheckResult("warn", "端口 8000 已被占用")
    except (ConnectionRefusedError, socket.timeout, OSError):
        return CheckResult("ok", "端口 8000 未占用")


def check_governance(fix: bool = False) -> CheckResult:
    """检查治理文件。"""
    governance_dir = Path(__file__).parent.parent.parent.parent / "governance"
    if not governance_dir.exists():
        return CheckResult("warn", "governance/ 不存在")

    agents_dir = governance_dir / "agents"
    skills_dir = governance_dir / "skills"

    agents_count = len(list(agents_dir.glob("*.yaml"))) if agents_dir.exists() else 0
    skills_count = len(list(skills_dir.glob("*.md"))) if skills_dir.exists() else 0

    if agents_count > 0 and skills_count > 0:
        return CheckResult("ok", f"{agents_count} agents, {skills_count} skills")
    return CheckResult("warn", f"agents: {agents_count}, skills: {skills_count}")

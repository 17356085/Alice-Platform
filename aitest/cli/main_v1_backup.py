"""
Alice CLI — Engine 命令行入口。

命令组:
    alice graph run/status/resume   # 测试 SOP 执行
    alice project init/list/show/... # 项目管理
    alice module list/show           # 模块管理
    alice server start/stop/status   # 测试工作台
    alice config show/set/reset      # 配置管理
    alice ecosystem                  # 生态控制面快照
    alice doctor                     # 环境诊断
    alice version                    # 版本信息

别名:
    alice run = alice graph run
    alice validate = alice project validate
    alice status = alice graph status
    alice list-projects = alice project list
    alice list-modules = alice module list
"""

import typer
from typing import Optional

app = typer.Typer(
    name="alice",
    help="Alice Engine — AI 自动化测试引擎",
    no_args_is_help=True,
)

# ── 命令组 ──────────────────────────────────────────────────

graph_app = typer.Typer(help="测试 SOP 执行", no_args_is_help=True)
project_app = typer.Typer(help="项目管理", no_args_is_help=True)
module_app = typer.Typer(help="模块管理", no_args_is_help=True)
server_app = typer.Typer(help="测试工作台", no_args_is_help=True)

app.add_typer(graph_app, name="graph")
app.add_typer(project_app, name="project")
app.add_typer(module_app, name="module")
app.add_typer(server_app, name="server")


# ══════════════════════════════════════════════════════════════
#  graph 命令组
# ══════════════════════════════════════════════════════════════

@graph_app.command("run")
def graph_run(
    module: str = typer.Option(..., "--module", "-m", help="模块名"),
    pages: Optional[str] = typer.Option(None, "--pages", "-p", help="页面列表 (逗号分隔)"),
    mode: str = typer.Option("full", "--mode", help="执行模式 (full/resume/from-automation/status)"),
    extensions: Optional[str] = typer.Option(None, "--extensions", "-e", help="Extensions (逗号分隔)"),
    mock_llm: bool = typer.Option(False, "--mock-llm", help="使用 Mock LLM"),
    llm: Optional[str] = typer.Option(None, "--llm", help="LLM Provider"),
    verbose: bool = typer.Option(False, "--verbose", "-v", help="详细输出"),
    yes: bool = typer.Option(False, "--yes", "-y", help="跳过确认"),
    output: Optional[str] = typer.Option(None, "--output", "-o", help="输出格式 (table/json/yaml)"),
    project_path: Optional[str] = typer.Option(None, "--project-path", help="项目路径 (覆盖配置)"),
):
    """执行一次完整 SOP 流水线。"""
    from aitest.cli.commands.graph.run import run_command
    run_command(
        project_path=project_path,
        module=module,
        pages=pages.split(",") if pages else None,
        mode=mode,
        extensions=extensions.split(",") if extensions else None,
        mock_llm=mock_llm,
        llm_provider=llm,
        verbose=verbose,
    )


@graph_app.command("status")
def graph_status(
    module: Optional[str] = typer.Option(None, "--module", "-m", help="模块名"),
    output: Optional[str] = typer.Option(None, "--output", "-o", help="输出格式 (table/json)"),
    project_path: Optional[str] = typer.Option(None, "--project-path", help="项目路径"),
):
    """查看执行状态。"""
    from aitest.cli.commands.graph.status import status_command
    status_command(
        module=module,
        output_format=output,
        project_path=project_path,
    )


@graph_app.command("resume")
def graph_resume(
    module: str = typer.Option(..., "--module", "-m", help="模块名"),
    pages: Optional[str] = typer.Option(None, "--pages", "-p", help="页面列表 (逗号分隔)"),
    extensions: Optional[str] = typer.Option(None, "--extensions", "-e", help="Extensions (逗号分隔)"),
    mock_llm: bool = typer.Option(False, "--mock-llm", help="使用 Mock LLM"),
    llm: Optional[str] = typer.Option(None, "--llm", help="LLM Provider"),
    yes: bool = typer.Option(False, "--yes", "-y", help="跳过确认"),
    output: Optional[str] = typer.Option(None, "--output", "-o", help="输出格式"),
    project_path: Optional[str] = typer.Option(None, "--project-path", help="项目路径"),
):
    """继续中断的执行。"""
    from aitest.cli.commands.graph.run import run_command
    run_command(
        module=module,
        pages=pages.split(",") if pages else None,
        mode="resume",
        extensions=extensions.split(",") if extensions else None,
        mock_llm=mock_llm,
        llm_provider=llm,
        yes=yes,
        output_format=output,
        project_path=project_path,
    )


# ══════════════════════════════════════════════════════════════
#  project 命令组
# ══════════════════════════════════════════════════════════════

@project_app.command("init")
def project_init(
    project_path: Optional[str] = typer.Option(None, "--project-path", "-p", help="项目路径"),
):
    """交互式项目配置 (Phase 0)。"""
    from aitest.cli.commands.project.init import init_command
    init_command(project_path=project_path)


@project_app.command("list")
def project_list(
    workspace: Optional[str] = typer.Option(None, "--workspace", "-w", help="工作目录路径"),
    output: Optional[str] = typer.Option(None, "--output", "-o", help="输出格式 (table/json)"),
):
    """列出所有项目。"""
    from aitest.cli.commands.project.list import list_command
    list_command(workspace=workspace, output_format=output)


@project_app.command("show")
def project_show(
    project_id: Optional[str] = typer.Option(None, "--id", help="项目 ID (默认活跃项目)"),
):
    """查看项目详情。"""
    from aitest.cli.commands.project.show import show_command
    show_command(project_id=project_id)


@project_app.command("set")
def project_set(
    project_id: str = typer.Option(..., "--id", help="项目 ID"),
):
    """切换活跃项目。"""
    from aitest.cli.commands.project.set import set_command
    set_command(project_id=project_id)


@project_app.command("register")
def project_register(
    path: str = typer.Option(..., "--path", help="项目路径"),
):
    """注册新项目。"""
    from aitest.cli.commands.project.register import register_command
    register_command(path=path)


@project_app.command("validate")
def project_validate(
    project_id: Optional[str] = typer.Option(None, "--id", help="项目 ID (默认活跃项目)"),
    output: Optional[str] = typer.Option(None, "--output", "-o", help="输出格式 (table/json)"),
):
    """检查项目配置是否合法。"""
    from aitest.cli.commands.project.validate import validate_command
    validate_command(project_id=project_id, output_format=output)


# ══════════════════════════════════════════════════════════════
#  module 命令组
# ══════════════════════════════════════════════════════════════

@module_app.command("list")
def module_list(
    project_id: Optional[str] = typer.Option(None, "--project", help="项目 ID"),
    output: Optional[str] = typer.Option(None, "--output", "-o", help="输出格式 (table/json)"),
):
    """列出项目中的模块。"""
    from aitest.cli.commands.module.list import list_command
    list_command(project_id=project_id, output_format=output)


@module_app.command("show")
def module_show(
    module: str = typer.Option(..., "--module", "-m", help="模块名"),
    project_id: Optional[str] = typer.Option(None, "--project", help="项目 ID"),
):
    """显示模块详情。"""
    from aitest.cli.commands.module.show import show_command
    show_command(module=module, project_id=project_id)


# ══════════════════════════════════════════════════════════════
#  server 命令组
# ══════════════════════════════════════════════════════════════

@server_app.command("start")
def server_start(
    host: str = typer.Option("0.0.0.0", "--host", help="监听地址"),
    port: int = typer.Option(8000, "--port", help="监听端口"),
    daemon: bool = typer.Option(False, "--daemon", "-d", help="后台运行"),
    reload: bool = typer.Option(False, "--reload", help="自动重载 (开发用)"),
):
    """启动测试工作台。"""
    from aitest.cli.commands.server.start import start_command
    start_command(host=host, port=port, daemon=daemon, reload=reload)


@server_app.command("stop")
def server_stop():
    """停止测试工作台。"""
    from aitest.cli.commands.server.stop import stop_command
    stop_command()


@server_app.command("status")
def server_status():
    """查看工作台状态。"""
    from aitest.cli.commands.server.status import status_command
    status_command()


@server_app.command("worker")
def server_worker(
    worker_id: str = typer.Option("", "--worker-id", help="worker 标识"),
    poll_interval: float = typer.Option(1.0, "--poll-interval", help="轮询间隔（秒）"),
):
    """启动独立执行 worker。"""
    from aitest.cli.commands.server.worker import worker_command
    worker_command(worker_id=worker_id, poll_interval=poll_interval)


# ══════════════════════════════════════════════════════════════
#  顶级命令
# ══════════════════════════════════════════════════════════════

@app.command("config")
def config_cmd(
    action: str = typer.Argument(help="操作: show/set/reset/get"),
    key: Optional[str] = typer.Argument(None, help="配置键 (如 defaults.llm_provider)"),
    value: Optional[str] = typer.Argument(None, help="配置值"),
):
    """管理 CLI 配置。"""
    from aitest.cli.commands.config_cmd import config_command
    config_command(action=action, key=key, value=value)


@app.command("ecosystem")
def ecosystem(
    output: Optional[str] = typer.Option(None, "--output", "-o", help="输出格式 (table/json)"),
):
    """查看平台/项目/扩展兼容性快照。"""
    from aitest.cli.commands.ecosystem import ecosystem_command
    ecosystem_command(output_format=output)


@app.command("doctor")
def doctor(
    fix: bool = typer.Option(False, "--fix", help="自动修复可修复的问题"),
    output: Optional[str] = typer.Option(None, "--output", "-o", help="输出格式 (table/json)"),
):
    """环境诊断。"""
    from aitest.cli.commands.doctor import doctor_command
    doctor_command(fix=fix, output_format=output)


@app.command("version")
def version():
    """显示版本信息。"""
    from aitest.cli.commands.version import version_command
    version_command()


@app.command("tui")
def tui():
    """进入交互式 TUI 界面。"""
    from aitest.cli.tui import run_tui
    run_tui()


# ══════════════════════════════════════════════════════════════
#  别名 (向后兼容)
# ══════════════════════════════════════════════════════════════

@app.command("run", hidden=True)
def run_alias(
    module: str = typer.Argument(..., help="模块名"),
    pages: Optional[str] = typer.Argument(None, help="页面列表 (逗号分隔)"),
    mode: str = typer.Option("full", "--mode", help="执行模式"),
    extensions: Optional[str] = typer.Option(None, "--extensions", "-e", help="Extensions"),
    mock_llm: bool = typer.Option(False, "--mock-llm", help="使用 Mock LLM"),
    llm: Optional[str] = typer.Option(None, "--llm", help="LLM Provider"),
    verbose: bool = typer.Option(False, "--verbose", "-v", help="详细输出"),
    yes: bool = typer.Option(False, "--yes", "-y", help="跳过确认"),
    output: Optional[str] = typer.Option(None, "--output", "-o", help="输出格式"),
    project_path: Optional[str] = typer.Option(None, "--project-path", help="项目路径"),
):
    """执行 SOP: alice run equipment [alarm-config,camera]"""
    graph_run(
        module=module, pages=pages.split(",") if pages else None, mode=mode, extensions=extensions.split(",") if extensions else None,
        mock_llm=mock_llm, llm=llm, verbose=verbose, yes=yes,
        output=output, project_path=project_path,
    )


@app.command("validate", hidden=True)
def validate_alias(
    project_path: Optional[str] = typer.Option(None, "--project-path", "-p", help="项目路径"),
    project_id: Optional[str] = typer.Option(None, "--id", help="项目 ID"),
    output: Optional[str] = typer.Option(None, "--output", "-o", help="输出格式"),
):
    """别名: alice validate = alice project validate。"""
    project_validate(project_id=project_id or project_path, output=output)


@app.command("status", hidden=True)
def status_alias(
    module: Optional[str] = typer.Argument(None, help="模块名"),
    output: Optional[str] = typer.Option(None, "--output", "-o", help="输出格式"),
    project_path: Optional[str] = typer.Option(None, "--project-path", help="项目路径"),
):
    """查看状态: alice status [equipment]"""
    graph_status(module=module, output=output, project_path=project_path)


@app.command("resume", hidden=True)
def resume_alias(
    module: str = typer.Argument(..., help="模块名"),
    pages: Optional[str] = typer.Argument(None, help="页面列表"),
    extensions: Optional[str] = typer.Option(None, "--extensions", "-e", help="Extensions"),
    mock_llm: bool = typer.Option(False, "--mock-llm", help="使用 Mock LLM"),
    llm: Optional[str] = typer.Option(None, "--llm", help="LLM Provider"),
    yes: bool = typer.Option(False, "--yes", "-y", help="跳过确认"),
    output: Optional[str] = typer.Option(None, "--output", "-o", help="输出格式"),
    project_path: Optional[str] = typer.Option(None, "--project-path", help="项目路径"),
):
    """继续执行: alice resume equipment"""
    graph_resume(
        module=module, pages=pages.split(",") if pages else None,
        extensions=extensions.split(",") if extensions else None,
        mock_llm=mock_llm, llm=llm, yes=yes,
        output=output, project_path=project_path,
    )


@app.command("view")
def view_command(
    target: str = typer.Argument(..., help="文档编号或 'all'/'last'"),
    project_path: Optional[str] = typer.Option(None, "--project-path", help="项目路径"),
):
    """查看生成的文档: view <编号> 或 view all/view last"""
    from aitest.cli.commands.view import view_command as view_cmd
    view_cmd(target=target, project_path=project_path)


@app.command("list-projects", hidden=True)
def list_projects_alias(
    workspace: Optional[str] = typer.Option(None, "--workspace", "-w", help="工作目录"),
    output: Optional[str] = typer.Option(None, "--output", "-o", help="输出格式"),
):
    """别名: alice list-projects = alice project list。"""
    project_list(workspace=workspace, output=output)


@app.command("list-modules", hidden=True)
def list_modules_alias(
    project_path: Optional[str] = typer.Option(None, "--project-path", "-p", help="项目路径"),
    output: Optional[str] = typer.Option(None, "--output", "-o", help="输出格式"),
):
    """别名: alice list-modules = alice module list。"""
    module_list(project_id=project_path, output=output)


# ══════════════════════════════════════════════════════════════
#  入口
# ══════════════════════════════════════════════════════════════

def main():
    """CLI 入口点。无参数时启动 TUI。"""
    import sys
    if len(sys.argv) == 1:
        # 无参数时启动 TUI
        from aitest.cli.tui import run_tui
        run_tui()
    else:
        app()


if __name__ == "__main__":
    main()

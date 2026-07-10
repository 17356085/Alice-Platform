"""
Alice CLI v2 — 资源化命令行入口。

新命令组（v2）:
    aitest run create/list/show/logs/stop/retry/compare        # Run 资源
    aitest agent list/show/versions                             # Agent 资源
    aitest workflow create/list/show/validate/run               # Workflow 资源 ✨
    aitest quality dataset/eval                                 # Quality 资源 ✨
    aitest provider list/show/test                              # Provider 资源 ✨
    aitest project init/list/show/set/switch/register/validate  # 项目管理
    aitest server start/stop/status/worker                      # 服务管理

旧命令组（兼容 6 个月）:
    aitest graph run/status/resume   # → aitest run create/list/retry
    aitest module list/show          # → 保留
"""

import typer
from typing import Optional
from rich.console import Console

console = Console()

app = typer.Typer(
    name="aitest",
    help="AITest Platform — AI 自动化测试引擎（资源化 CLI v2）",
    no_args_is_help=True,
)

# ══════════════════════════════════════════════════════════════
#  新命令组（v2）
# ══════════════════════════════════════════════════════════════

run_app = typer.Typer(help="Run 资源管理", no_args_is_help=True)
agent_app = typer.Typer(help="Agent 资源管理", no_args_is_help=True)
workflow_app = typer.Typer(help="Workflow 资源管理", no_args_is_help=True)
quality_app = typer.Typer(help="Quality 资源管理", no_args_is_help=True)
provider_app = typer.Typer(help="ModelProvider 资源管理", no_args_is_help=True)

app.add_typer(run_app, name="run")
app.add_typer(agent_app, name="agent")
app.add_typer(workflow_app, name="workflow")
app.add_typer(quality_app, name="quality")
app.add_typer(provider_app, name="provider")

# ── run 命令组 ──────────────────────────────────────────────

@run_app.command("create")
def run_create(
    target: str = typer.Option(..., "--target", "-t", help="执行目标 (格式: <type>:<id>)"),
    module: Optional[str] = typer.Option(None, "--module", "-m", help="模块名"),
    pages: Optional[str] = typer.Option(None, "--pages", "-p", help="页面列表 (逗号分隔)"),
    env: Optional[str] = typer.Option(None, "--env", "-e", help="环境 ID"),
    provider: Optional[str] = typer.Option(None, "--provider", help="Provider ID"),
    mock_llm: bool = typer.Option(False, "--mock-llm", help="使用 Mock LLM"),
    wait: bool = typer.Option(True, "--wait/--no-wait", help="等待执行完成"),
    output: str = typer.Option("table", "--output", "-o", help="输出格式 (table/json/yaml)"),
):
    """创建新的 Run。"""
    from aitest.cli.commands.run.create import run_create as cmd
    cmd(target, module, pages, env, provider, mock_llm, wait, output)


@run_app.command("list")
def run_list(
    status: Optional[str] = typer.Option(None, "--status", "-s", help="按状态筛选（支持逗号分隔）"),
    target_type: Optional[str] = typer.Option(None, "--target-type", help="按目标类型筛选"),
    module: Optional[str] = typer.Option(None, "--module", "-m", help="按模块筛选"),
    from_date: Optional[str] = typer.Option(None, "--from", help="开始时间 (YYYY-MM-DD)"),
    to_date: Optional[str] = typer.Option(None, "--to", help="结束时间 (YYYY-MM-DD)"),
    sort_by: str = typer.Option("created_at", "--sort", help="排序字段"),
    order: str = typer.Option("desc", "--order", help="排序顺序 (asc/desc)"),
    limit: int = typer.Option(20, "--limit", "-n", help="每页数量"),
    offset: int = typer.Option(0, "--offset", help="跳过记录数（分页）"),
    export: Optional[str] = typer.Option(None, "--export", help="导出格式 (json/csv/yaml)"),
    output: str = typer.Option("table", "--output", "-o", help="输出格式"),
):
    """列出 Run 记录（增强版：高级筛选、分页、排序、导出）。"""
    from aitest.cli.commands.run.list import run_list as cmd
    cmd(status, target_type, module, from_date, to_date, sort_by, order, limit, offset, export, output)


@run_app.command("show")
def run_show(
    run_id: str = typer.Argument(..., help="Run ID"),
    output: str = typer.Option("table", "--output", "-o", help="输出格式"),
):
    """显示 Run 详情。"""
    from aitest.cli.commands.run.show import run_show as cmd
    cmd(run_id, output)


# ── agent 命令组 ──────────────────────────────────────────

@agent_app.command("list")
def agent_list(
    output: str = typer.Option("table", "--output", "-o", help="输出格式"),
):
    """列出所有 Agent。"""
    from aitest.cli.commands.agent.list import agent_list as cmd
    cmd(output)


@agent_app.command("show")
def agent_show(
    agent_id: str = typer.Argument(..., help="Agent ID"),
    version: Optional[str] = typer.Option(None, "--version", "-v", help="Agent 版本"),
    output: str = typer.Option("table", "--output", "-o", help="输出格式"),
):
    """显示 Agent 详情。"""
    from aitest.cli.commands.agent.show import agent_show as cmd
    cmd(agent_id, version, output)


@agent_app.command("versions")
def agent_versions(
    agent_id: str = typer.Argument(..., help="Agent ID"),
    output: str = typer.Option("table", "--output", "-o", help="输出格式"),
):
    """列出 Agent 的所有版本。"""
    from aitest.cli.commands.agent.versions import versions_command
    versions_command(agent_id, output)


@agent_app.command("diff")
def agent_diff(
    agent_id: str = typer.Argument(..., help="Agent ID"),
    from_version: str = typer.Option(..., "--from", help="起始版本"),
    to_version: str = typer.Option(..., "--to", help="目标版本"),
    output: str = typer.Option("table", "--output", "-o", help="输出格式"),
):
    """对比两个版本的差异。"""
    from aitest.cli.commands.agent.versions import diff_command
    diff_command(agent_id, from_version, to_version, output)


# ── workflow 命令组 ──────────────────────────────────────────

@workflow_app.command("create")
def workflow_create(
    workflow_id: str = typer.Option(..., "--id", help="Workflow ID"),
    name: Optional[str] = typer.Option(None, "--name", help="Workflow 名称"),
    description: Optional[str] = typer.Option(None, "--description", help="Workflow 描述"),
    template: Optional[str] = typer.Option(None, "--template", help="模板名称 (page-test/module-test/simple)"),
    from_file: Optional[str] = typer.Option(None, "--from-file", help="从文件加载 (YAML/JSON)"),
    output: str = typer.Option("table", "--output", "-o", help="输出格式"),
):
    """创建新的 Workflow。"""
    from aitest.cli.commands.workflow.create import create_command
    create_command(workflow_id, name, description, template, from_file, output)


@workflow_app.command("list")
def workflow_list(
    output: str = typer.Option("table", "--output", "-o", help="输出格式"),
):
    """列出所有 Workflow。"""
    from aitest.cli.commands.workflow.list import list_command
    list_command(output)


@workflow_app.command("show")
def workflow_show(
    workflow_id: str = typer.Argument(..., help="Workflow ID"),
    output: str = typer.Option("table", "--output", "-o", help="输出格式"),
):
    """显示 Workflow 详情。"""
    from aitest.cli.commands.workflow.show import show_command
    show_command(workflow_id, output)


@workflow_app.command("validate")
def workflow_validate(
    workflow_id: str = typer.Argument(..., help="Workflow ID"),
    output: str = typer.Option("table", "--output", "-o", help="输出格式"),
):
    """验证 Workflow 配置。"""
    from aitest.cli.commands.workflow.validate import validate_command
    validate_command(workflow_id, output)


@workflow_app.command("run")
def workflow_run(
    workflow_id: str = typer.Argument(..., help="Workflow ID"),
    input_data: Optional[str] = typer.Option(None, "--input-data", help="输入数据 (JSON 字符串)"),
    input_file: Optional[str] = typer.Option(None, "--input-file", help="输入文件 (JSON/YAML)"),
    module: Optional[str] = typer.Option(None, "--module", "-m", help="模块名"),
    pages: Optional[str] = typer.Option(None, "--pages", "-p", help="页面列表"),
    env: Optional[str] = typer.Option(None, "--env", "-e", help="环境 ID"),
    provider: Optional[str] = typer.Option(None, "--provider", help="Provider ID"),
    mock_llm: bool = typer.Option(False, "--mock-llm", help="使用 Mock LLM"),
    wait: bool = typer.Option(True, "--wait/--no-wait", help="等待执行完成"),
    output: str = typer.Option("table", "--output", "-o", help="输出格式"),
):
    """执行 Workflow。"""
    from aitest.cli.commands.workflow.run import run_command
    run_command(workflow_id, input_data, input_file, module, pages, env, provider, mock_llm, wait, output)


# ── quality 命令组 ──────────────────────────────────────────

@quality_app.command("dataset")
def quality_dataset(
    action: str = typer.Argument(..., help="操作 (list/show/create)"),
    dataset_id: Optional[str] = typer.Option(None, "--id", help="数据集 ID"),
    name: Optional[str] = typer.Option(None, "--name", help="数据集名称"),
    description: Optional[str] = typer.Option(None, "--description", help="数据集描述"),
    from_file: Optional[str] = typer.Option(None, "--from-file", help="从文件加载"),
    output: str = typer.Option("table", "--output", "-o", help="输出格式"),
):
    """数据集管理。"""
    from aitest.cli.commands.quality.dataset import dataset_list, dataset_show, dataset_create

    if action == "list":
        dataset_list(output)
    elif action == "show":
        if not dataset_id:
            console.print("[red]✗ 需要指定 --id[/red]")
            raise typer.Exit(1)
        dataset_show(dataset_id, output)
    elif action == "create":
        if not dataset_id:
            console.print("[red]✗ 需要指定 --id[/red]")
            raise typer.Exit(1)
        dataset_create(dataset_id, name, description, from_file, output)
    else:
        console.print(f"[red]✗ 未知操作: {action}[/red]")
        console.print("可用操作: list, show, create")
        raise typer.Exit(1)


@quality_app.command("eval")
def quality_eval(
    action: str = typer.Argument(..., help="操作 (run/list/show)"),
    eval_id: Optional[str] = typer.Option(None, "--id", help="评估 ID"),
    agent_id: Optional[str] = typer.Option(None, "--agent", help="Agent ID"),
    dataset_id: Optional[str] = typer.Option(None, "--dataset", help="数据集 ID"),
    provider: Optional[str] = typer.Option(None, "--provider", help="Provider ID"),
    mock_llm: bool = typer.Option(False, "--mock-llm", help="使用 Mock LLM"),
    wait: bool = typer.Option(True, "--wait/--no-wait", help="等待执行完成"),
    output: str = typer.Option("table", "--output", "-o", help="输出格式"),
):
    """评估任务管理。"""
    from aitest.cli.commands.quality.eval import eval_run, eval_list, eval_show

    if action == "run":
        if not eval_id or not agent_id or not dataset_id:
            console.print("[red]✗ 需要指定 --id, --agent, --dataset[/red]")
            raise typer.Exit(1)
        eval_run(eval_id, agent_id, dataset_id, provider, mock_llm, wait, output)
    elif action == "list":
        eval_list(output)
    elif action == "show":
        if not eval_id:
            console.print("[red]✗ 需要指定 --id[/red]")
            raise typer.Exit(1)
        eval_show(eval_id, output)
    else:
        console.print(f"[red]✗ 未知操作: {action}[/red]")
        console.print("可用操作: run, list, show")
        raise typer.Exit(1)


# ── provider 命令组 ──────────────────────────────────────────

@provider_app.command("list")
def provider_list(
    output: str = typer.Option("table", "--output", "-o", help="输出格式"),
):
    """列出所有 Provider。"""
    from aitest.cli.commands.provider.list import list_command
    list_command(output)


@provider_app.command("show")
def provider_show(
    provider_id: str = typer.Argument(..., help="Provider ID"),
    output: str = typer.Option("table", "--output", "-o", help="输出格式"),
):
    """显示 Provider 详情。"""
    from aitest.cli.commands.provider.list import show_command
    show_command(provider_id, output)


@provider_app.command("test")
def provider_test(
    provider_id: str = typer.Argument(..., help="Provider ID"),
):
    """测试 Provider 连通性。"""
    from aitest.cli.commands.provider.test import test_command
    test_command(provider_id)


# ══════════════════════════════════════════════════════════════
#  旧命令组（向后兼容）
# ══════════════════════════════════════════════════════════════

graph_app = typer.Typer(help="[已废弃] 测试 SOP 执行", no_args_is_help=True, deprecated=True)
project_app = typer.Typer(help="项目管理", no_args_is_help=True)
module_app = typer.Typer(help="模块管理", no_args_is_help=True)
server_app = typer.Typer(help="测试工作台", no_args_is_help=True)

app.add_typer(graph_app, name="graph", hidden=True)
app.add_typer(project_app, name="project")
app.add_typer(module_app, name="module")
app.add_typer(server_app, name="server")


# ── graph 命令组（已废弃）──────────────────────────────────

@graph_app.command("run")
def graph_run(
    module: str = typer.Option(..., "--module", "-m", help="模块名"),
    pages: Optional[str] = typer.Option(None, "--pages", "-p", help="页面列表 (逗号分隔)"),
    mode: str = typer.Option("full", "--mode", help="执行模式"),
    extensions: Optional[str] = typer.Option(None, "--extensions", "-e", help="Extensions"),
    mock_llm: bool = typer.Option(False, "--mock-llm", help="使用 Mock LLM"),
    llm: Optional[str] = typer.Option(None, "--llm", help="LLM Provider"),
    verbose: bool = typer.Option(False, "--verbose", "-v", help="详细输出"),
    yes: bool = typer.Option(False, "--yes", "-y", help="跳过确认"),
    output: Optional[str] = typer.Option(None, "--output", "-o", help="输出格式"),
    project_path: Optional[str] = typer.Option(None, "--project-path", help="项目路径"),
):
    """[已废弃] 执行一次完整 SOP 流水线。"""
    from aitest.cli.utils.output import print_deprecation_warning
    print_deprecation_warning(
        "aitest graph run --module <m>",
        "aitest run create --target agent:page-observer --module <m>"
    )

    # 自动转换并调用新命令
    from aitest.cli.commands.run.create import run_create as cmd
    cmd(
        target="agent:page-observer",
        module=module,
        pages=pages,
        env=None,
        provider=None,
        mock_llm=mock_llm,
        wait=True,
        output=output or "table"
    )


@graph_app.command("status")
def graph_status(
    module: Optional[str] = typer.Option(None, "--module", "-m", help="模块名"),
    output: Optional[str] = typer.Option(None, "--output", "-o", help="输出格式"),
    project_path: Optional[str] = typer.Option(None, "--project-path", help="项目路径"),
):
    """[已废弃] 查看执行状态。"""
    from aitest.cli.utils.output import print_deprecation_warning
    print_deprecation_warning(
        "aitest graph status",
        "aitest run list"
    )

    # 自动转换并调用新命令
    from aitest.cli.commands.run.list import run_list as cmd
    cmd(
        status=None,
        target_type=None,
        module=module,
        limit=20,
        output=output or "table"
    )


@graph_app.command("resume")
def graph_resume(
    module: str = typer.Option(..., "--module", "-m", help="模块名"),
    pages: Optional[str] = typer.Option(None, "--pages", "-p", help="页面列表"),
    extensions: Optional[str] = typer.Option(None, "--extensions", "-e", help="Extensions"),
    mock_llm: bool = typer.Option(False, "--mock-llm", help="使用 Mock LLM"),
    llm: Optional[str] = typer.Option(None, "--llm", help="LLM Provider"),
    yes: bool = typer.Option(False, "--yes", "-y", help="跳过确认"),
    output: Optional[str] = typer.Option(None, "--output", "-o", help="输出格式"),
    project_path: Optional[str] = typer.Option(None, "--project-path", help="项目路径"),
):
    """[已废弃] 继续中断的执行。"""
    from aitest.cli.utils.output import print_deprecation_warning, print_error
    print_deprecation_warning(
        "aitest graph resume --module <m>",
        "aitest run retry <run_id>"
    )
    print_error("请先使用 'aitest run list --status failed' 找到失败的 Run ID，然后使用 'aitest run retry <run_id>'")
    raise typer.Exit(1)


# ── project 命令组（保留）──────────────────────────────────

@project_app.command("init")
def project_init(
    project_path: Optional[str] = typer.Option(None, "--project-path", "-p", help="项目路径"),
    project_name: Optional[str] = typer.Option(None, "--project-name", help="项目名称（跳过交互）"),
    base_url: Optional[str] = typer.Option(None, "--base-url", help="目标 URL（跳过交互）"),
    quick: bool = typer.Option(False, "--quick", help="快速模式（使用默认值）"),
    yes: bool = typer.Option(False, "--yes", "-y", help="自动确认（跳过确认步骤）"),
):
    """交互式项目配置。"""
    from aitest.cli.commands.project.init import init_command
    init_command(
        project_path=project_path,
        project_name=project_name,
        base_url=base_url,
        quick=quick,
        yes=yes,
    )


@project_app.command("list")
def project_list(
    workspace: Optional[str] = typer.Option(None, "--workspace", "-w", help="工作目录路径"),
    output: Optional[str] = typer.Option(None, "--output", "-o", help="输出格式"),
):
    """列出所有项目。"""
    from aitest.cli.commands.project.list import list_command
    list_command(workspace=workspace, output_format=output)


@project_app.command("show")
def project_show(
    project_id: Optional[str] = typer.Option(None, "--id", help="项目 ID"),
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


@project_app.command("switch")
def project_switch(
    project_id: str = typer.Argument(..., help="项目 ID / '-' (上一个) / 数字 (最近列表索引)"),
):
    """快速切换项目（支持 - 和数字别名）。"""
    from aitest.cli.commands.project.switch import switch_command
    switch_command(project_id=project_id)


@project_app.command("register")
def project_register(
    path: str = typer.Option(..., "--path", help="项目路径"),
):
    """注册新项目。"""
    from aitest.cli.commands.project.register import register_command
    register_command(path=path)


@project_app.command("validate")
def project_validate(
    project_id: Optional[str] = typer.Option(None, "--id", help="项目 ID"),
    output: Optional[str] = typer.Option(None, "--output", "-o", help="输出格式"),
):
    """检查项目配置是否合法。"""
    from aitest.cli.commands.project.validate import validate_command
    validate_command(project_id=project_id, output_format=output)


# ── module 命令组（保留）──────────────────────────────────

@module_app.command("list")
def module_list(
    project_id: Optional[str] = typer.Option(None, "--project", help="项目 ID"),
    output: Optional[str] = typer.Option(None, "--output", "-o", help="输出格式"),
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


# ── server 命令组（保留）──────────────────────────────────

@server_app.command("start")
def server_start(
    host: str = typer.Option("0.0.0.0", "--host", help="监听地址"),
    port: int = typer.Option(8000, "--port", help="监听端口"),
    daemon: bool = typer.Option(False, "--daemon", "-d", help="后台运行"),
    reload: bool = typer.Option(False, "--reload", help="自动重载"),
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
    key: Optional[str] = typer.Argument(None, help="配置键"),
    value: Optional[str] = typer.Argument(None, help="配置值"),
):
    """管理 CLI 配置。"""
    from aitest.cli.commands.config_cmd import config_command
    config_command(action=action, key=key, value=value)


@app.command("ecosystem")
def ecosystem(
    output: Optional[str] = typer.Option(None, "--output", "-o", help="输出格式"),
):
    """查看平台/项目/扩展兼容性快照。"""
    from aitest.cli.commands.ecosystem import ecosystem_command
    ecosystem_command(output_format=output)


@app.command("doctor")
def doctor(
    fix: bool = typer.Option(False, "--fix", help="自动修复"),
    output: Optional[str] = typer.Option(None, "--output", "-o", help="输出格式"),
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
#  别名（向后兼容）
# ══════════════════════════════════════════════════════════════

@app.command("view", hidden=True)
def view_command(
    target: str = typer.Argument(..., help="文档编号或 'all'/'last'"),
    project_path: Optional[str] = typer.Option(None, "--project-path", help="项目路径"),
):
    """查看生成的文档。"""
    from aitest.cli.commands.view import view_command as view_cmd
    view_cmd(target=target, project_path=project_path)


# ══════════════════════════════════════════════════════════════
#  入口
# ══════════════════════════════════════════════════════════════

def main():
    """CLI 入口点。无参数时启动 TUI。"""
    import sys
    if len(sys.argv) == 1:
        from aitest.cli.tui import run_tui
        run_tui()
    else:
        app()


if __name__ == "__main__":
    main()

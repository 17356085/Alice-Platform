"""
Alice CLI — Engine 命令行入口。

用法:
    alice run --project-path ... --module equipment
    alice validate --project-path ...
    alice status --project-path ... --module equipment
    alice resume --project-path ... --module equipment
    alice list-projects --workspace ...
    alice list-modules --project-path ...
"""

import typer
from typing import Optional

app = typer.Typer(
    name="alice",
    help="Alice Engine — AI 自动化测试引擎",
    no_args_is_help=True,
)


@app.command()
def run(
    project_path: str = typer.Option(..., "--project-path", "-p", help="项目路径"),
    module: str = typer.Option(..., "--module", "-m", help="模块名"),
    pages: Optional[str] = typer.Option(None, "--pages", help="页面列表 (逗号分隔)"),
    mode: str = typer.Option("full", "--mode", help="执行模式 (full/resume/from-automation/status)"),
    extensions: Optional[str] = typer.Option(None, "--extensions", "-e", help="Extensions (逗号分隔)"),
    mock_llm: bool = typer.Option(False, "--mock-llm", help="使用 Mock LLM"),
    llm_provider: Optional[str] = typer.Option(None, "--llm", help="LLM Provider"),
    verbose: bool = typer.Option(False, "--verbose", "-v", help="详细输出"),
):
    """执行一次完整 SOP 流水线。"""
    from aitest.cli.commands.run import run_command
    run_command(
        project_path=project_path,
        module=module,
        pages=pages.split(",") if pages else None,
        mode=mode,
        extensions=extensions.split(",") if extensions else None,
        mock_llm=mock_llm,
        llm_provider=llm_provider,
        verbose=verbose,
    )


@app.command()
def validate(
    project_path: str = typer.Option(..., "--project-path", "-p", help="项目路径"),
):
    """检查项目配置是否合法。"""
    from aitest.cli.commands.validate import validate_command
    validate_command(project_path=project_path)


@app.command()
def status(
    project_path: str = typer.Option(..., "--project-path", "-p", help="项目路径"),
    module: Optional[str] = typer.Option(None, "--module", "-m", help="模块名"),
):
    """查看执行状态。"""
    from aitest.cli.commands.status import status_command
    status_command(project_path=project_path, module=module)


@app.command()
def resume(
    project_path: str = typer.Option(..., "--project-path", "-p", help="项目路径"),
    module: str = typer.Option(..., "--module", "-m", help="模块名"),
    pages: Optional[str] = typer.Option(None, "--pages", help="页面列表 (逗号分隔)"),
    extensions: Optional[str] = typer.Option(None, "--extensions", "-e", help="Extensions (逗号分隔)"),
    mock_llm: bool = typer.Option(False, "--mock-llm", help="使用 Mock LLM"),
):
    """继续中断的执行。"""
    from aitest.cli.commands.run import run_command
    run_command(
        project_path=project_path,
        module=module,
        pages=pages.split(",") if pages else None,
        mode="resume",
        extensions=extensions.split(",") if extensions else None,
        mock_llm=mock_llm,
    )


@app.command()
def list_projects(
    workspace: str = typer.Option(..., "--workspace", "-w", help="工作目录路径"),
):
    """列出所有项目。"""
    from aitest.cli.commands.list_projects import list_projects_command
    list_projects_command(workspace=workspace)


@app.command()
def list_modules(
    project_path: str = typer.Option(..., "--project-path", "-p", help="项目路径"),
):
    """列出项目中的模块。"""
    from aitest.cli.commands.list_modules import list_modules_command
    list_modules_command(project_path=project_path)


def main():
    """CLI 入口点。"""
    app()


if __name__ == "__main__":
    main()

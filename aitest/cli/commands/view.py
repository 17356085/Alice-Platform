"""view 命令 — 查看生成的文档。

用法:
    view <编号>     查看指定文档
    view all        查看所有文档
    view last       查看最近生成的文档
"""

from pathlib import Path
from rich.console import Console
from rich.syntax import Syntax
from rich.panel import Panel

console = Console()

# 全局状态: 记录最近生成的文档列表
_last_docs: list[str] = []


def set_last_docs(docs: list[str]):
    """设置最近生成的文档列表。"""
    global _last_docs
    _last_docs = docs


def view_command(target: str, project_path: str | None = None):
    """查看生成的文档。"""
    global _last_docs

    if not _last_docs:
        # 尝试从项目目录查找
        if project_path:
            _last_docs = _scan_project_docs(project_path)
        else:
            from aitest.cli.config import CLIConfig
            config = CLIConfig()
            path = config.active_project_path
            if path:
                _last_docs = _scan_project_docs(path)

    if not _last_docs:
        console.print("[yellow]没有可查看的文档[/yellow]")
        console.print("先运行 alice run <module> 生成文档")
        return

    if target == "all":
        _view_all()
    elif target == "last":
        _view_file(_last_docs[-1])
    else:
        try:
            idx = int(target) - 1
            if 0 <= idx < len(_last_docs):
                _view_file(_last_docs[idx])
            else:
                console.print(f"[red]编号 {target} 超出范围 (1-{len(_last_docs)})[/red]")
        except ValueError:
            console.print(f"[red]无效的编号: {target}[/red]")


def _view_all():
    """查看所有文档。"""
    for i, doc in enumerate(_last_docs, 1):
        _view_file(doc, show_index=i)


def _view_file(file_path: str, show_index: int | None = None):
    """查看单个文档。"""
    path = Path(file_path)

    if not path.exists():
        console.print(f"[red]文件不存在: {file_path}[/red]")
        return

    # 显示标题
    if show_index:
        title = f"[{show_index}] {path.name}"
    else:
        title = str(path)

    console.print()
    console.print(f"[bold]{'─' * 60}[/bold]")
    console.print(f"[bold]{title}[/bold]")
    console.print(f"[bold]{'─' * 60}[/bold]")

    # 读取并显示内容
    try:
        content = path.read_text(encoding="utf-8")

        # 根据文件类型高亮
        if path.suffix == ".md":
            console.print(content)
        elif path.suffix in (".yaml", ".yml"):
            syntax = Syntax(content, "yaml", theme="monokai", line_numbers=True)
            console.print(syntax)
        elif path.suffix == ".py":
            syntax = Syntax(content, "python", theme="monokai", line_numbers=True)
            console.print(syntax)
        elif path.suffix == ".json":
            syntax = Syntax(content, "json", theme="monokai", line_numbers=True)
            console.print(syntax)
        else:
            console.print(content)

    except Exception as e:
        console.print(f"[red]读取失败: {e}[/red]")

    console.print()


def _scan_project_docs(project_path: str) -> list[str]:
    """扫描项目目录中的文档。"""
    from pathlib import Path

    tlo_dir = Path(project_path) / ".tlo"
    docs = []

    # 扫描所有模块的文档
    modules_dir = tlo_dir / "knowledge" / "modules"
    if modules_dir.exists():
        for module_dir in sorted(modules_dir.iterdir()):
            if module_dir.is_dir():
                # 模块上下文
                module_context = module_dir / "MODULE_CONTEXT.md"
                if module_context.exists():
                    docs.append(str(module_context))

                # 页面文档
                pages_dir = module_dir / "pages"
                if pages_dir.exists():
                    for page_dir in sorted(pages_dir.iterdir()):
                        if page_dir.is_dir():
                            for doc_name in ["PAGE_CONTEXT.md", "TEST_CASES.md", "TEST_DESIGN.md", "PAGE_INTERFACE.yaml"]:
                                doc_path = page_dir / doc_name
                                if doc_path.exists():
                                    docs.append(str(doc_path))

    return docs

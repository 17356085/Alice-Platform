"""Alice TUI — 双模式交互界面。

模式:
  - 对话模式 (默认): 自然语言输入，AI 理解并执行
  - 命令模式: 直接命令，快速执行

切换:
  /cmd    切换到命令模式
  /chat   切换到对话模式

启动:
    alice          # 进入 TUI
    alice tui      # 显式进入 TUI
"""

import io
import sys
from contextlib import redirect_stdout, redirect_stderr
from typing import Optional

from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.containers import Vertical, Horizontal
from textual.widgets import Footer, Header, Input, Static, RichLog
from textual import events
from rich.text import Text


class OutputLog(RichLog):
    """输出日志。"""

    def __init__(self, **kwargs):
        super().__init__(**kwargs, markup=True, wrap=True, highlight=True)


class CommandInput(Input):
    """命令输入框 — 支持历史。"""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._history: list[str] = []
        self._history_idx = -1

    def on_key(self, event: events.Key):
        if event.key == "up":
            if self._history and self._history_idx < len(self._history) - 1:
                self._history_idx += 1
                self.value = self._history[-(self._history_idx + 1)]
            event.prevent_default()
        elif event.key == "down":
            if self._history_idx > 0:
                self._history_idx -= 1
                self.value = self._history[-(self._history_idx + 1)]
            else:
                self._history_idx = -1
                self.value = ""
            event.prevent_default()

    def add_history(self, command: str):
        if command.strip():
            self._history.append(command.strip())
            self._history_idx = -1


class ModeIndicator(Static):
    """模式指示器 — 显示当前模式。"""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._mode = "chat"  # chat | cmd

    @property
    def mode(self) -> str:
        return self._mode

    @mode.setter
    def mode(self, value: str):
        self._mode = value
        self.refresh()

    def render(self) -> Text:
        if self._mode == "chat":
            return Text("CHAT", style="bold green")
        else:
            return Text("CMD", style="bold cyan")


class AliceTUI(App):
    """Alice TUI — 双模式交互。"""

    CSS = """
    Screen {
        layout: vertical;
    }

    #output {
        height: 1fr;
        background: $surface;
        padding: 1 2;
    }

    #input-area {
        height: 3;
        background: $surface;
        border-top: tall $primary;
        padding: 0 1;
        layout: horizontal;
    }

    #mode-indicator {
        width: 6;
        content-align: left middle;
        padding: 0 1 0 0;
    }

    #command-input {
        background: transparent;
        width: 1fr;
    }
    """

    BINDINGS = [
        Binding("ctrl+c", "quit", "Quit"),
        Binding("q", "quit", "Quit", show=False),
        Binding("f1", "show_help", "Help", show=False),
    ]

    TITLE = "Alice Engine"

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._project_id = None
        self._project_path = None
        self._mode = "chat"  # chat | cmd
        self._ctx_manager = None  # 延迟初始化
        self._load_config()

    def _load_config(self):
        """加载配置。"""
        try:
            from aitest.cli.config import CLIConfig
            from aitest.cli.context import CLIContext
            config = CLIConfig()
            self._project_id = config.active_project
            ctx = CLIContext(config)
            self._project_path = ctx.project_path
        except Exception:
            pass

    def compose(self) -> ComposeResult:
        """构建 UI。"""
        yield Header(show_clock=True)

        with Vertical(id="output"):
            yield OutputLog(id="log")

        with Horizontal(id="input-area"):
            yield ModeIndicator(id="mode-indicator")
            yield CommandInput(id="command-input")

        yield Footer()

    def on_mount(self):
        """初始化。"""
        self._init_context_manager()
        self._update_title()
        self._show_welcome()
        self._update_mode_indicator()
        self.query_one("#command-input", CommandInput).focus()

    def _init_context_manager(self):
        """初始化上下文管理器。"""
        if self._project_path:
            try:
                from aitest.cli.context_manager import ContextManager
                self._ctx_manager = ContextManager(self._project_path)
            except Exception:
                self._ctx_manager = None

    def _update_title(self):
        """更新标题栏。"""
        header = self.query_one("Header")
        if self._project_id:
            header.title = f"Alice Engine — {self._project_id}"
        else:
            header.title = "Alice Engine"

    def _update_mode_indicator(self):
        """更新模式指示器。"""
        indicator = self.query_one("#mode-indicator", ModeIndicator)
        indicator.mode = self._mode

    def _update_input_placeholder(self):
        """更新输入框提示。"""
        input_widget = self.query_one("#command-input", CommandInput)
        if self._mode == "chat":
            input_widget.placeholder = "输入问题或指令 (/cmd 切换命令模式)..."
        else:
            input_widget.placeholder = "输入命令 (help 查看帮助, /chat 切换对话模式)..."

    def _show_welcome(self):
        """显示欢迎信息。"""
        log = self.query_one("#log", OutputLog)
        log.write("Alice Engine TUI")
        log.write("─" * 40)
        log.write("")
        log.write("[bold green]对话模式[/bold green] — 输入自然语言与 AI 交互")
        log.write("[bold cyan]命令模式[/bold cyan] — 输入命令直接执行")
        log.write("")
        log.write("切换: /cmd (命令模式)  /chat (对话模式)")
        log.write("帮助: help 或 F1")
        log.write("退出: exit / quit / q / Ctrl+C")
        log.write("")

    def _switch_mode(self, mode: str):
        """切换模式。"""
        self._mode = mode
        self._update_mode_indicator()
        self._update_input_placeholder()

        log = self.query_one("#log", OutputLog)
        if mode == "chat":
            log.write("[green]已切换到对话模式[/green]")
        else:
            log.write("[cyan]已切换到命令模式[/cyan]")
        log.write("")

    def _execute_input(self, text: str):
        """执行输入 — 根据模式分发。"""
        log = self.query_one("#log", OutputLog)

        # 检查模式切换命令
        if text.strip() == "/cmd":
            self._switch_mode("cmd")
            return
        elif text.strip() == "/chat":
            self._switch_mode("chat")
            return

        # 根据模式分发
        if self._mode == "chat":
            self._handle_chat(text)
        else:
            self._handle_command(text)

    def _handle_chat(self, text: str):
        """处理对话模式输入。"""
        from rich.text import Text
        log = self.query_one("#log", OutputLog)

        # 记录用户消息
        if self._ctx_manager:
            self._ctx_manager.add_message("user", text)

        # 显示用户输入 (用 Text 对象避免 markup 解析问题)
        user_text = Text()
        user_text.append("> ", style="bold green")
        user_text.append(text, style="bold green")
        log.write(user_text)
        log.write("")

        # 简单的自然语言 → 命令映射
        command = self._parse_natural_language(text)

        if command:
            log.write(f"[dim]$ {command}[/dim]")
            log.write("")
            self._execute_command(command)
        else:
            # AI 回复 (占位)
            response = "我理解你的意思，但目前只支持以下操作:\n"
            response += "\n"
            response += "  - 运行测试: 跑一下 equipment 的测试\n"
            response += "  - 查看状态: 看一下执行状态\n"
            response += "  - 列出项目: 有哪些项目\n"
            response += "  - 列出模块: 有哪些模块\n"
            response += "  - 环境检查: 检查一下环境\n"
            response += "\n"
            response += "或输入 /cmd 切换到命令模式直接执行命令"

            log.write(response)

            # 记录 AI 回复
            if self._ctx_manager:
                self._ctx_manager.add_message("assistant", response)

        log.write("")

    def _parse_natural_language(self, text: str) -> str | None:
        """简单自然语言 → 命令映射。"""
        text = text.strip().lower()

        # 运行测试
        if any(kw in text for kw in ["跑", "运行", "执行", "run", "测试"]):
            # 提取模块名
            for module in ["equipment", "tank", "production", "warehouse", "personnel", "system"]:
                if module in text:
                    return f"graph run -m {module}"
            return "graph run"

        # 查看状态
        if any(kw in text for kw in ["状态", "status", "进度"]):
            return "graph status"

        # 列出项目
        if any(kw in text for kw in ["项目", "project", "列表"]):
            return "project list"

        # 列出模块
        if any(kw in text for kw in ["模块", "module", "有哪些"]):
            return "module list"

        # 环境检查
        if any(kw in text for kw in ["环境", "doctor", "检查", "诊断"]):
            return "doctor"

        # 启动服务器
        if any(kw in text for kw in ["启动", "start", "服务器", "server", "工作台"]):
            return "server start"

        # 停止服务器
        if any(kw in text for kw in ["停止", "stop", "关闭"]):
            return "server stop"

        return None

    def _handle_command(self, text: str):
        """处理命令模式输入。"""
        from rich.text import Text
        log = self.query_one("#log", OutputLog)

        # 记录用户消息
        if self._ctx_manager:
            self._ctx_manager.add_message("user", text)

        # 显示用户输入 (用 Text 对象避免 markup 解析问题)
        user_text = Text()
        user_text.append("> ", style="bold cyan")
        user_text.append(text, style="bold cyan")
        log.write(user_text)
        log.write("")

        # 解析命令
        parts = text.strip().split()
        if not parts:
            return

        cmd = parts[0].lower()
        args = parts[1:]

        # 命令分发
        try:
            if cmd in ("help", "h", "?"):
                self._show_help()
            elif cmd in ("exit", "quit", "q"):
                self.exit()
            elif cmd == "clear":
                log.clear()
            elif cmd == "project":
                self._cmd_project(args)
            elif cmd == "module":
                self._cmd_module(args)
            elif cmd == "graph":
                self._cmd_graph(args)
            elif cmd == "server":
                self._cmd_server(args)
            elif cmd == "config":
                self._cmd_config(args)
            elif cmd == "doctor":
                self._cmd_doctor()
            elif cmd == "version":
                self._cmd_version()
            elif cmd == "run":
                self._cmd_graph(["run"] + args)
            elif cmd == "status":
                self._cmd_graph(["status"] + args)
            elif cmd == "resume":
                self._cmd_graph(["resume"] + args)
            elif cmd == "view":
                self._cmd_view(args)
            elif cmd == "validate":
                self._cmd_project(["validate"])
            elif cmd in ("list-projects", "lp"):
                self._cmd_project(["list"])
            elif cmd in ("list-modules", "lm"):
                self._cmd_module(["list"])
            else:
                log.write(f"[red]未知命令: {cmd}[/red]")
                log.write("输入 help 查看可用命令")
        except Exception as e:
            log.write(f"[red]错误: {e}[/red]")

        log.write("")

    def _execute_command(self, command: str):
        """执行命令 (从自然语言转换)。"""
        parts = command.strip().split()
        if not parts:
            return

        cmd = parts[0].lower()
        args = parts[1:]

        try:
            if cmd == "graph":
                self._cmd_graph(args)
            elif cmd == "project":
                self._cmd_project(args)
            elif cmd == "module":
                self._cmd_module(args)
            elif cmd == "server":
                self._cmd_server(args)
            elif cmd == "doctor":
                self._cmd_doctor()
            elif cmd == "config":
                self._cmd_config(args)
        except Exception as e:
            log = self.query_one("#log", OutputLog)
            log.write(f"[red]错误: {e}[/red]")

    def _show_help(self):
        """显示帮助。"""
        log = self.query_one("#log", OutputLog)

        if self._mode == "chat":
            help_text = """[bold]对话模式帮助[/bold]

输入自然语言与 AI 交互，例如:

  [cyan]跑一下 equipment 的测试[/cyan]
  [cyan]看一下执行状态[/cyan]
  [cyan]有哪些项目[/cyan]
  [cyan]检查一下环境[/cyan]
  [cyan]启动工作台[/cyan]

切换到命令模式: [cyan]/cmd[/cyan]
"""
        else:
            help_text = """[bold]命令模式帮助[/bold]

[bold]项目管理:[/bold]
  [cyan]project[/cyan] list                列出项目
  [cyan]project[/cyan] set <id>            切换项目
  [cyan]project[/cyan] show                项目详情
  [cyan]project[/cyan] validate            检查配置

[bold]模块管理:[/bold]
  [cyan]module[/cyan] list                 列出模块
  [cyan]module[/cyan] show -m <mod>        模块详情

[bold]高频操作 (简化命令):[/bold]
  [cyan]run[/cyan] <mod>                    执行 SOP
  [cyan]status[/cyan] [<mod>]              查看状态
  [cyan]resume[/cyan] <mod>                继续执行
  [cyan]view[/cyan] <编号|all|last>        查看文档

[bold]工作台:[/bold]
  [cyan]server[/cyan] start [-d]           启动工作台
  [cyan]server[/cyan] stop                 停止工作台
  [cyan]server[/cyan] status               工作台状态

[bold]其他:[/bold]
  [cyan]config[/cyan] show                 查看配置
  [cyan]doctor[/cyan]                      环境诊断
  [cyan]version[/cyan]                     版本信息
  [cyan]clear[/cyan]                       清屏
  [cyan]exit[/cyan] / quit / q             退出

[bold]快捷命令:[/bold]
  [cyan]run[/cyan] -m <mod>                = graph run
  [cyan]status[/cyan]                      = graph status
  [cyan]lp[/cyan]                          = project list
  [cyan]lm[/cyan]                          = module list

切换到对话模式: [cyan]/chat[/cyan]
"""

        log.write(help_text)

    def _cmd_project(self, args: list):
        """project 命令。"""
        log = self.query_one("#log", OutputLog)

        if not args:
            log.write("用法: project list|set|show|validate")
            return

        subcmd = args[0]

        if subcmd == "list":
            from aitest.cli.config import CLIConfig
            from aitest.cli.context import CLIContext
            config = CLIConfig()
            ctx = CLIContext(config)
            adapter = ctx.get_project_adapter()
            projects = adapter.list_projects()

            if not projects:
                log.write("未找到项目")
                return

            for p in projects:
                active = "[green]●[/green]" if p.get("active") else " "
                name = p.get("name", "") or p["id"]
                log.write(f"  {active} {p['id']:20s} {name}")

        elif subcmd == "set":
            if len(args) < 2:
                log.write("用法: project set <id>")
                return

            project_id = args[1]
            from aitest.cli.config import CLIConfig
            from aitest.cli.context import CLIContext
            config = CLIConfig()
            ctx = CLIContext(config)
            adapter = ctx.get_project_adapter()

            try:
                adapter.set_active_project(project_id)
                self._project_id = project_id
                self._update_title()
                log.write(f"[green]活跃项目: {project_id}[/green]")
            except ValueError as e:
                log.write(f"[red]{e}[/red]")

        elif subcmd == "show":
            from aitest.cli.config import CLIConfig
            from aitest.cli.context import CLIContext
            config = CLIConfig()
            ctx = CLIContext(config)
            adapter = ctx.get_project_adapter()

            try:
                project = adapter.show_project()
                log.write(f"项目 ID:    {project.get('id', '')}")
                log.write(f"项目名称:   {project.get('name', '')}")
                log.write(f"项目路径:   {project.get('path', '')}")
                log.write(f"模块数量:   {project.get('module_count', 0)}")
                if project.get("modules"):
                    log.write(f"模块列表:   {', '.join(project['modules'])}")
            except ValueError as e:
                log.write(f"[red]{e}[/red]")

        elif subcmd == "validate":
            from aitest.cli.config import CLIConfig
            from aitest.cli.context import CLIContext
            config = CLIConfig()
            ctx = CLIContext(config)
            adapter = ctx.get_project_adapter()

            result = adapter.validate_project()
            for check in result.get("checks", []):
                status = check.get("status", "")
                icon = {"ok": "✅", "warn": "⚠️", "error": "❌"}.get(status, status)
                log.write(f"  {icon} {check.get('name', '')}: {check.get('detail', '')}")

        else:
            log.write(f"未知子命令: {subcmd}")

    def _cmd_module(self, args: list):
        """module 命令。"""
        log = self.query_one("#log", OutputLog)

        if not args:
            log.write("用法: module list|show")
            return

        subcmd = args[0]

        if subcmd == "list":
            from aitest.cli.config import CLIConfig
            from aitest.cli.context import CLIContext
            from pathlib import Path

            config = CLIConfig()
            ctx = CLIContext(config)
            project_path = Path(ctx.project_path)
            modules_dir = project_path / ".tlo" / "knowledge" / "modules"

            if not modules_dir.exists():
                log.write("未找到模块目录")
                return

            for d in sorted(modules_dir.iterdir()):
                if d.is_dir():
                    pages_dir = d / "pages"
                    pages_count = sum(1 for p in pages_dir.iterdir() if p.is_dir()) if pages_dir.exists() else 0
                    log.write(f"  {d.name:20s} {pages_count} pages")

        elif subcmd == "show":
            module = None
            for i, arg in enumerate(args):
                if arg in ("-m", "--module") and i + 1 < len(args):
                    module = args[i + 1]
                    break

            if not module:
                log.write("用法: module show -m <module>")
                return

            from aitest.cli.config import CLIConfig
            from aitest.cli.context import CLIContext
            from pathlib import Path

            config = CLIConfig()
            ctx = CLIContext(config)
            project_path = Path(ctx.project_path)
            module_dir = project_path / ".tlo" / "knowledge" / "modules" / module

            if not module_dir.exists():
                log.write(f"[red]模块 {module} 不存在[/red]")
                return

            log.write(f"模块: {module}")
            log.write(f"路径: {module_dir}")

            pages_dir = module_dir / "pages"
            if pages_dir.exists():
                pages = sorted([d.name for d in pages_dir.iterdir() if d.is_dir()])
                log.write(f"页面 ({len(pages)}):")
                for page in pages:
                    log.write(f"  - {page}")

        else:
            log.write(f"未知子命令: {subcmd}")

    def _cmd_graph(self, args: list):
        """graph 命令。"""
        log = self.query_one("#log", OutputLog)

        if not args:
            log.write("用法: graph run|status|resume")
            return

        subcmd = args[0]

        if subcmd == "run":
            # 支持两种格式: graph run -m <mod> 或 run <mod>
            module = None
            pages = None

            # 解析参数
            i = 0
            while i < len(args):
                if args[i] in ("-m", "--module") and i + 1 < len(args):
                    module = args[i + 1]
                    i += 2
                elif not args[i].startswith("-"):
                    if module is None:
                        module = args[i]
                    else:
                        pages = args[i].split(",")
                    i += 1
                else:
                    i += 1

            if not module:
                log.write("用法: run <module> [pages]")
                return

            log.write(f"[dim]$ aitest graph run -m {module}[/dim]")
            log.write("")

            output = io.StringIO()
            try:
                import time
                start_time = time.time()

                with redirect_stdout(output), redirect_stderr(output):
                    from aitest.cli.commands.graph.run import run_command
                    run_command(module=module, pages=pages, output_format="table")

                elapsed = time.time() - start_time
                result = output.getvalue()
                if result:
                    for line in result.strip().split("\n"):
                        log.write(f"  {line}")

                # 更新执行上下文
                if self._ctx_manager:
                    # 提取生成的文档
                    docs = []
                    for line in result.split("\n"):
                        if "[" in line and "]" in line and ".md" in line:
                            # 简单提取文档路径
                            docs.append(line.strip())

                    self._ctx_manager.update_run(
                        module=module,
                        status="completed",
                        elapsed=elapsed,
                        docs=docs,
                    )

            except SystemExit:
                pass
            except Exception as e:
                log.write(f"[red]执行失败: {e}[/red]")

                # 记录失败
                if self._ctx_manager:
                    self._ctx_manager.update_run(
                        module=module,
                        status="failed",
                        elapsed=0,
                    )

        elif subcmd == "status":
            from aitest.cli.config import CLIConfig
            from aitest.cli.context import CLIContext

            config = CLIConfig()
            ctx = CLIContext(config)
            adapter = ctx.get_engine_adapter()

            data = adapter.get_status()
            runs = data.get("runs", [])

            if not runs:
                log.write("未找到执行状态")
                return

            for run_data in runs:
                module_name = run_data.get("module", "")
                status = run_data.get("status", "unknown")
                completed = len(run_data.get("completed_phases", []))
                failed = len(run_data.get("failed_phases", []))

                status_icon = {
                    "completed": "✅",
                    "completed_with_issues": "⚠️",
                    "failed": "❌",
                }.get(status, "❓")

                log.write(f"  {status_icon} {module_name}: {status} ({completed} phases completed)")

        elif subcmd == "resume":
            # 支持两种格式: graph resume -m <mod> 或 resume <mod>
            module = None
            pages = None

            # 解析参数
            i = 0
            while i < len(args):
                if args[i] in ("-m", "--module") and i + 1 < len(args):
                    module = args[i + 1]
                    i += 2
                elif not args[i].startswith("-"):
                    if module is None:
                        module = args[i]
                    else:
                        pages = args[i].split(",")
                    i += 1
                else:
                    i += 1

            if not module:
                log.write("用法: resume <module>")
                return

            log.write(f"[dim]$ aitest graph resume -m {module}[/dim]")
            log.write("")

            output = io.StringIO()
            try:
                with redirect_stdout(output), redirect_stderr(output):
                    from aitest.cli.commands.graph.run import run_command
                    run_command(module=module, pages=pages, mode="resume", output_format="table")

                result = output.getvalue()
                if result:
                    for line in result.strip().split("\n"):
                        log.write(f"  {line}")

            except SystemExit:
                pass
            except Exception as e:
                log.write(f"[red]恢复失败: {e}[/red]")

        else:
            log.write(f"未知子命令: {subcmd}")

    def _cmd_view(self, args: list):
        """view 命令 — 查看生成的文档。"""
        log = self.query_one("#log", OutputLog)

        if not args:
            log.write("用法: view <编号> 或 view all/view last")
            return

        target = args[0]

        output = io.StringIO()
        try:
            with redirect_stdout(output), redirect_stderr(output):
                from aitest.cli.commands.view import view_command
                view_command(target=target)

            result = output.getvalue()
            if result:
                for line in result.strip().split("\n"):
                    log.write(f"  {line}")

        except SystemExit:
            pass
        except Exception as e:
            log.write(f"[red]查看失败: {e}[/red]")

    def _cmd_server(self, args: list):
        """server 命令。"""
        log = self.query_one("#log", OutputLog)

        if not args:
            log.write("用法: server start|stop|status")
            return

        subcmd = args[0]

        if subcmd == "start":
            daemon = "-d" in args or "--daemon" in args
            from aitest.cli.adapters.server_adapter import ServerAdapter

            adapter = ServerAdapter()
            try:
                result = adapter.start(daemon=daemon)
                if daemon:
                    log.write(f"服务器已启动 (PID: {result.get('pid')})")
                    log.write(f"访问: http://localhost:{result.get('port', 8000)}/chat")
            except RuntimeError as e:
                log.write(f"[red]{e}[/red]")

        elif subcmd == "stop":
            from aitest.cli.adapters.server_adapter import ServerAdapter

            adapter = ServerAdapter()
            try:
                result = adapter.stop()
                log.write(f"服务器已停止 (PID: {result.get('pid')})")
            except RuntimeError as e:
                log.write(f"[red]{e}[/red]")

        elif subcmd == "status":
            from aitest.cli.adapters.server_adapter import ServerAdapter

            adapter = ServerAdapter()
            result = adapter.status()
            status = result.get("status", "unknown")
            pid = result.get("pid")
            port = result.get("port", 8000)

            status_text = {
                "running": "[green]运行中[/green]",
                "stopped": "[dim]已停止[/dim]",
                "stale_pid": "[yellow]残留 PID[/yellow]",
                "external_process": "[yellow]外部进程[/yellow]",
            }.get(status, status)

            log.write(f"状态: {status_text}")
            log.write(f"端口: {port}")
            if pid:
                log.write(f"PID: {pid}")

        else:
            log.write(f"未知子命令: {subcmd}")

    def _cmd_config(self, args: list):
        """config 命令。"""
        log = self.query_one("#log", OutputLog)

        if not args:
            log.write("用法: config show|get|set")
            return

        subcmd = args[0]

        if subcmd == "show":
            from aitest.cli.config import CLIConfig
            config = CLIConfig()
            data = config.get_all()

            for key, value in data.items():
                if isinstance(value, dict):
                    for k, v in value.items():
                        log.write(f"  {key}.{k}: {v}")
                else:
                    log.write(f"  {key}: {value}")

        elif subcmd == "get":
            if len(args) < 2:
                log.write("用法: config get <key>")
                return

            key = args[1]
            from aitest.cli.config import CLIConfig
            config = CLIConfig()
            value = config.get(key)
            log.write(f"{key} = {value}")

        elif subcmd == "set":
            if len(args) < 3:
                log.write("用法: config set <key> <value>")
                return

            key, value = args[1], args[2]
            from aitest.cli.config import CLIConfig
            config = CLIConfig()
            config.set(key, value)
            log.write(f"[green]{key} = {value}[/green]")

        else:
            log.write(f"未知子命令: {subcmd}")

    def _cmd_doctor(self):
        """doctor 命令。"""
        log = self.query_one("#log", OutputLog)

        output = io.StringIO()
        try:
            with redirect_stdout(output), redirect_stderr(output):
                from aitest.cli.commands.doctor import doctor_command
                doctor_command(output_format="table")

            result = output.getvalue()
            if result:
                for line in result.strip().split("\n"):
                    log.write(f"  {line}")
        except SystemExit:
            pass
        except Exception as e:
            log.write(f"[red]诊断失败: {e}[/red]")

    def _cmd_version(self):
        """version 命令。"""
        log = self.query_one("#log", OutputLog)

        try:
            from importlib.metadata import version
            cli_version = version("aitest")
        except Exception:
            cli_version = "dev"

        log.write(f"Alice Engine v{cli_version}")

    def on_input_submitted(self, event: Input.Submitted):
        """处理输入。"""
        text = event.value.strip()
        if text:
            input_widget = self.query_one("#command-input", CommandInput)
            input_widget.add_history(text)
            input_widget.value = ""
            self._execute_input(text)

    def action_show_help(self):
        """显示帮助。"""
        self._show_help()


def run_tui():
    """启动 TUI。"""
    app = AliceTUI()
    app.run()


if __name__ == "__main__":
    run_tui()

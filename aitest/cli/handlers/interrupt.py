"""
CLI Interrupt Handler — 处理 HITL 中断。
"""

from dataclasses import dataclass
from typing import Optional
from pathlib import Path

from rich.console import Console

console = Console()


@dataclass
class InterruptPayload:
    """中断信息。"""
    phase: str
    phase_index: int
    total_phases: int
    module: str
    files: list[dict]
    summary: dict
    execution_result: dict = None


@dataclass
class InterruptDecision:
    """用户决策。"""
    action: str  # continue / edit / regenerate / skip
    feedback: str = None


@dataclass
class ValidationResult:
    """合法性检查结果。"""
    ok: bool
    errors: list[str] = None


class CLIInterruptHandler:
    """CLI 模式下的中断处理器。"""

    def handle(self, payload: InterruptPayload) -> InterruptDecision:
        """处理中断，返回用户决策。"""
        from aitest.cli.output.formatter import print_interrupt

        # 展示中断信息
        files = [f.get("path", "") for f in payload.files]
        summary = payload.summary.get("text", "") if payload.summary else ""
        print_interrupt(payload.phase, files, summary)

        # 等待用户输入
        while True:
            choice = input("> ").strip().lower()

            if choice == "" or choice == "enter":
                return InterruptDecision(action="continue")
            elif choice == "v":
                # 查看文件
                self._view_files(payload.files)
                continue
            elif choice == "e":
                # 修改文件
                self._edit_files(payload.files)
                return InterruptDecision(action="continue")
            elif choice == "r":
                # 重新生成
                feedback = input("请描述修改意见: ").strip()
                return InterruptDecision(action="regenerate", feedback=feedback)
            elif choice == "s":
                # 跳过
                return InterruptDecision(action="skip")
            else:
                console.print("[yellow]⚠️  无效输入，请重试[/yellow]")

    def _view_files(self, files: list[dict]):
        """查看文件内容。"""
        import subprocess
        import sys

        for file_info in files:
            path = file_info.get("path", "")
            if not path:
                continue

            file_path = Path(path)
            if not file_path.exists():
                console.print(f"[yellow]⚠️  文件不存在: {path}[/yellow]")
                continue

            # 打开编辑器查看
            if sys.platform == "win32":
                subprocess.run(["notepad", str(file_path)])
            else:
                subprocess.run(["less", str(file_path)])

    def _edit_files(self, files: list[dict]):
        """修改文件。"""
        import subprocess
        import sys

        for file_info in files:
            path = file_info.get("path", "")
            if not path:
                continue

            file_path = Path(path)
            if not file_path.exists():
                console.print(f"[yellow]⚠️  文件不存在: {path}[/yellow]")
                continue

            # 打开编辑器修改
            if sys.platform == "win32":
                subprocess.run(["notepad", str(file_path)])
            else:
                subprocess.run(["vim", str(file_path)])

            # 验证修改
            validation = self.validate(file_path, "")
            if not validation.ok:
                console.print("[yellow]⚠️  修改验证失败:[/yellow]")
                for error in validation.errors:
                    console.print(f"  ❌ {error}")

    def validate(self, file_path: Path, phase: str) -> ValidationResult:
        """验证修改后的文件是否合法。"""
        if not file_path.exists():
            return ValidationResult(ok=False, errors=["文件不存在"])

        content = file_path.read_text(encoding="utf-8")

        # 基本检查: 文件非空
        if not content.strip():
            return ValidationResult(ok=False, errors=["文件为空"])

        # Markdown 文件检查: 包含标题
        if file_path.suffix == ".md" and "#" not in content:
            return ValidationResult(ok=False, errors=["缺少 # 标题"])

        return ValidationResult(ok=True)

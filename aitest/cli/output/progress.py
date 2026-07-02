"""
CLI 进度条 — 使用 rich 库显示执行进度。
"""

from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TaskProgressColumn


def create_progress() -> Progress:
    """创建进度条。"""
    return Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        TaskProgressColumn(),
        console=None,  # 使用默认 console
    )

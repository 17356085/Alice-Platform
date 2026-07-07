"""会话上下文管理器。

管理会话级上下文:
  - 项目上下文 (持久化缓存)
  - 执行上下文 (会话内累积)
  - 对话上下文 (动态管理)
  - 文件上下文 (LRU 缓存)

Usage:
    from aitest.cli.context_manager import ContextManager

    ctx = ContextManager("/path/to/project")
    ctx.add_message("user", "跑一下 equipment 的测试")
    ctx.add_message("assistant", "✅ 完成 (23.1s)")

    context = ctx.get_context_for_ai()
"""

import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

from aitest.cli.cache.project_cache import ProjectCache
from aitest.cli.cache.file_cache import FileCache


@dataclass
class Message:
    """对话消息。"""
    role: str                          # "user" / "assistant"
    content: str                       # 消息内容
    timestamp: float = field(default_factory=time.time)
    related_files: list[str] = field(default_factory=list)


@dataclass
class RunInfo:
    """执行信息。"""
    module: str                        # 模块名
    status: str                        # "completed" / "failed"
    elapsed: float                     # 耗时 (秒)
    docs: list[str] = field(default_factory=list)  # 生成的文档路径


class ContextManager:
    """会话上下文管理器。"""

    def __init__(self, project_path: str):
        """初始化上下文管理器。

        Args:
            project_path: 项目路径
        """
        self.project_path = project_path

        # 缓存管理器
        self.project_cache = ProjectCache()
        self.file_cache = FileCache()

        # 项目上下文 (持久化)
        self.project_context = self._load_project_context()

        # 会话上下文 (内存)
        self.messages: list[Message] = []
        self.last_run: Optional[RunInfo] = None
        self.summary: Optional[str] = None

    def _load_project_context(self) -> dict:
        """加载项目上下文 (优先缓存)。"""
        project_id = Path(self.project_path).name

        # 尝试从缓存加载
        cached = self.project_cache.get(project_id)
        if cached:
            return cached

        # 扫描项目结构
        context = self._scan_project()

        # 缓存结果
        self.project_cache.put(project_id, context)

        return context

    def _scan_project(self) -> dict:
        """扫描项目结构。"""
        project_path = Path(self.project_path)
        modules_dir = project_path / ".tlo" / "knowledge" / "modules"

        modules = []
        if modules_dir.exists():
            for module_dir in sorted(modules_dir.iterdir()):
                if module_dir.is_dir():
                    pages_dir = module_dir / "pages"
                    pages = []
                    if pages_dir.exists():
                        pages = [p.name for p in pages_dir.iterdir() if p.is_dir()]

                    # 统计测试文件
                    test_count = 0
                    script_dir = project_path / "script" / module_dir.name
                    if script_dir.exists():
                        test_count = len(list(script_dir.glob("test_*.py")))

                    modules.append({
                        "name": module_dir.name,
                        "pages": pages,
                        "page_count": len(pages),
                        "test_count": test_count,
                    })

        return {
            "project_id": project_path.name,
            "project_path": str(project_path),
            "modules": modules,
            "module_count": len(modules),
        }

    def add_message(self, role: str, content: str, **kwargs):
        """添加对话消息。

        Args:
            role: 角色 ("user" / "assistant")
            content: 消息内容
            **kwargs: 其他参数 (related_files 等)
        """
        message = Message(role=role, content=content, **kwargs)
        self.messages.append(message)

        # 超过 20 条消息时摘要
        if len(self.messages) > 20:
            self._summarize_old_messages()

    def _summarize_old_messages(self):
        """摘要旧消息 (混合策略)。"""
        # 保留最近 10 轮
        recent = self.messages[-20:]
        old = self.messages[:-20]

        # 提取关键信息
        key_info = self._extract_key_info(old)

        # 评估质量
        if self._is_summary_quality_good(key_info, old):
            self.summary = key_info
        else:
            # TODO: 调用 AI 摘要 (未来实现)
            self.summary = key_info

        self.messages = recent

    def _extract_key_info(self, messages: list[Message]) -> str:
        """提取关键信息。"""
        operations = []
        results = []
        modules = set()

        for msg in messages:
            if msg.role == "user":
                # 提取用户操作
                if any(kw in msg.content for kw in ["run", "跑", "执行"]):
                    operations.append(msg.content[:50])
                # 提取模块名
                for kw in ["equipment", "tank", "production", "warehouse", "personnel", "system"]:
                    if kw in msg.content:
                        modules.add(kw)
            elif msg.role == "assistant":
                # 提取执行结果
                if "✅" in msg.content:
                    results.append("成功")
                elif "❌" in msg.content:
                    results.append("失败")

        parts = []
        if operations:
            parts.append(f"操作: {', '.join(operations[:3])}")
        if results:
            parts.append(f"结果: {', '.join(set(results))}")
        if modules:
            parts.append(f"模块: {', '.join(modules)}")

        return "; ".join(parts) if parts else "无操作记录"

    def _is_summary_quality_good(self, summary: str, messages: list[Message]) -> bool:
        """评估摘要质量。"""
        # 检查 1: 摘要长度
        if len(summary) < 20:
            return False

        # 检查 2: 是否包含关键信息
        if not any(kw in summary for kw in ["操作", "结果", "模块"]):
            return False

        return True

    def update_run(self, module: str, status: str, elapsed: float, docs: list[str] = None):
        """更新执行上下文。

        Args:
            module: 模块名
            status: 执行状态
            elapsed: 耗时 (秒)
            docs: 生成的文档路径列表
        """
        self.last_run = RunInfo(
            module=module,
            status=status,
            elapsed=elapsed,
            docs=docs or [],
        )

    def get_file_content(self, file_path: str) -> Optional[str]:
        """获取文件内容 (带缓存)。

        Args:
            file_path: 文件路径

        Returns:
            文件内容，如果读取失败则返回 None
        """
        # 检查缓存
        cached = self.file_cache.get(file_path)
        if cached:
            return cached

        # 读取文件
        try:
            content = Path(file_path).read_text(encoding="utf-8")
            self.file_cache.put(file_path, content)
            return content
        except (OSError, UnicodeDecodeError):
            return None

    def get_context_for_ai(self) -> str:
        """获取 AI 需要的上下文。

        Returns:
            格式化的上下文字符串
        """
        parts = []

        # 项目信息
        ctx = self.project_context
        parts.append(f"项目: {ctx.get('project_id', '')}")
        parts.append(f"路径: {ctx.get('project_path', '')}")

        # 模块信息
        modules = ctx.get("modules", [])
        if modules:
            module_names = [m["name"] for m in modules]
            parts.append(f"模块 ({len(modules)}): {', '.join(module_names)}")

        # 最近执行
        if self.last_run:
            parts.append(f"最近执行: {self.last_run.module} ({self.last_run.status}, {self.last_run.elapsed:.1f}s)")

        # 对话摘要
        if self.summary:
            parts.append(f"历史: {self.summary}")

        return "\n".join(parts)

    def get_module_info(self, module_name: str) -> Optional[dict]:
        """获取模块信息。

        Args:
            module_name: 模块名

        Returns:
            模块信息，如果不存在则返回 None
        """
        modules = self.project_context.get("modules", [])
        for module in modules:
            if module["name"] == module_name:
                return module
        return None

    def get_modules(self) -> list[dict]:
        """获取所有模块信息。

        Returns:
            模块信息列表
        """
        return self.project_context.get("modules", [])

    def clear_conversation(self):
        """清空对话历史。"""
        self.messages.clear()
        self.summary = None

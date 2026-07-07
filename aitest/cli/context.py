"""CLI 上下文 — 解析活跃项目、创建 adapter。

Usage:
    from aitest.cli.context import CLIContext
    from aitest.cli.config import CLIConfig

    config = CLIConfig()
    ctx = CLIContext(config)
    adapter = ctx.get_engine_adapter()
    result = adapter.run(module="equipment")
"""

from typing import Optional
from pathlib import Path

from aitest.cli.config import CLIConfig


class CLIContext:
    """CLI 运行上下文。"""

    def __init__(self, config: CLIConfig):
        self.config = config
        self._project_path: Optional[str] = None

    @property
    def project_path(self) -> str:
        """解析项目路径。优先级: 显式设置 > config > 自动检测。"""
        if self._project_path:
            return self._project_path

        # 从 config 获取
        path = self.config.active_project_path
        if path and Path(path).exists():
            return path

        # 自动检测: 从当前目录向上找 .tlo/
        cwd = Path.cwd()
        for parent in [cwd] + list(cwd.parents):
            if (parent / ".tlo" / "project.yaml").exists():
                return str(parent)

        raise ValueError(
            "未找到项目。请使用:\n"
            "  alice project set --id=<id>      # 切换已注册项目\n"
            "  alice project register --path=<p> # 注册新项目\n"
            "  alice project init                # 交互式创建项目"
        )

    @project_path.setter
    def project_path(self, value: str):
        self._project_path = value

    @property
    def project_id(self) -> Optional[str]:
        """当前项目 ID。"""
        return self.config.active_project

    def get_engine_adapter(self, **kwargs):
        """创建 Engine adapter。"""
        from aitest.cli.adapters.engine_adapter import LiveEngineAdapter
        return LiveEngineAdapter(project_path=self.project_path, **kwargs)

    def get_graph_adapter(self, **kwargs):
        """创建 Graph adapter。"""
        from aitest.cli.adapters.graph_adapter import GraphAdapter
        return GraphAdapter(project_path=self.project_path, **kwargs)

    def get_project_adapter(self):
        """创建 Project adapter。"""
        from aitest.cli.adapters.project_adapter import ProjectAdapter
        return ProjectAdapter(config=self.config)

    def get_server_adapter(self):
        """创建 Server adapter。"""
        from aitest.cli.adapters.server_adapter import ServerAdapter
        host = self.config.get("server.host", "0.0.0.0")
        port = self.config.get("server.port", 8000)
        return ServerAdapter(host=host, port=port)

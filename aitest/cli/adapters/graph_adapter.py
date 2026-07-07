"""Graph adapter — SOP 执行。

薄封装层，将 CLI 参数转换为 Engine 调用。
"""

from typing import Optional


class GraphAdapter:
    """SOP 执行 adapter。"""

    def __init__(self, project_path: str, llm_provider: str | None = None, event_bus=None):
        self.project_path = project_path
        self.llm_provider = llm_provider
        self.event_bus = event_bus

    def run(
        self,
        module: str,
        pages: list[str] | None = None,
        mode: str = "full",
        extensions: list[str] | None = None,
    ) -> dict:
        """执行 SOP。

        Args:
            module: 模块名
            pages: 页面列表 (None = 自动发现)
            mode: 执行模式 (full/resume/from-automation/status)
            extensions: 扩展列表 (audit/complexity/knowledge/memory)

        Returns:
            Engine.run() 的返回值
        """
        from aitest.cli.adapters.engine_adapter import LiveEngineAdapter

        adapter = LiveEngineAdapter(
            project_path=self.project_path,
            llm_provider=self.llm_provider,
            event_bus=self.event_bus,
        )
        return adapter.run(module=module, pages=pages, mode=mode, extensions=extensions)

    def get_status(self, module: str | None = None) -> dict:
        """获取执行状态。"""
        from aitest.cli.adapters.engine_adapter import LiveEngineAdapter

        adapter = LiveEngineAdapter(project_path=self.project_path)
        return adapter.get_status(module=module)

    def resume(
        self,
        module: str,
        pages: list[str] | None = None,
        extensions: list[str] | None = None,
    ) -> dict:
        """继续中断的执行。"""
        return self.run(module=module, pages=pages, mode="resume", extensions=extensions)

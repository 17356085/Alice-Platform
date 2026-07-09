"""Engine adapter — CLI → Engine 的抽象接口。

CLI 层通过此 adapter 调用 Engine，不直接 import aitest.engine。
"""

from typing import Protocol, Optional, runtime_checkable


@runtime_checkable
class EngineAdapterProtocol(Protocol):
    """Engine adapter 接口。"""

    def run(self, module: str, pages: list[str] | None = None, mode: str = "full", **kwargs) -> dict:
        """执行一次完整 SOP 流水线。"""
        ...

    def get_status(self, module: str | None = None) -> dict:
        """获取执行状态。"""
        ...

    def resume(self, module: str, **kwargs) -> dict:
        """继续中断的执行。"""
        ...


class LiveEngineAdapter:
    """真实 Engine 调用。"""

    def __init__(self, project_path: str, llm_provider: str | None = None, mock_llm: bool = False, event_bus=None):
        self.project_path = project_path
        self.llm_provider = llm_provider
        self.mock_llm = mock_llm
        self.event_bus = event_bus

    def run(self, module: str, pages: list[str] | None = None, mode: str = "full", **kwargs) -> dict:
        """执行一次完整 SOP 流水线。"""
        from aitest.engine import Engine

        engine = Engine(
            workstudy=self.project_path,
            llm_provider=self.llm_provider,
            mock_llm=self.mock_llm or kwargs.get("mock_llm", False) or None,
            event_bus=self.event_bus,
        )

        # 加载 extensions
        extensions = kwargs.get("extensions")
        if extensions:
            from aitest.engine.extensions import (
                AuditExtension, ComplexityExtension,
                KnowledgeExtension, MemoryExtension,
            )
            ext_map = {
                "audit": AuditExtension,
                "complexity": ComplexityExtension,
                "knowledge": KnowledgeExtension,
                "memory": MemoryExtension,
            }
            for ext_name in extensions:
                ext_cls = ext_map.get(ext_name.strip())
                if ext_cls:
                    engine.add_extension(ext_cls())

        return engine.run(module=module, pages=pages, mode=mode)

    def get_status(self, module: str | None = None) -> dict:
        """获取执行状态。"""
        import json
        from pathlib import Path

        tlo_dir = Path(self.project_path) / ".tlo"
        status_dir = tlo_dir / "runtime" / "sop-status"

        if not status_dir.exists():
            return {"status": "no_data", "runs": []}

        results = []
        for f in sorted(status_dir.glob("SOP_STATUS_*.json")):
            if module and module not in f.name:
                continue
            try:
                with open(f, "r", encoding="utf-8") as fh:
                    results.append(json.load(fh))
            except (json.JSONDecodeError, OSError):
                continue

        return {"status": "ok", "runs": results}

    def resume(self, module: str, **kwargs) -> dict:
        """继续中断的执行。"""
        return self.run(module=module, mode="resume", **kwargs)

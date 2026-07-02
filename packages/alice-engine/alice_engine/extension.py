"""EngineExtension — 引擎扩展协议。"""

from __future__ import annotations

from typing import TYPE_CHECKING, Protocol, runtime_checkable

if TYPE_CHECKING:
    from alice_engine.engine import Engine
    from alice_engine.engine import RunResult


@runtime_checkable
class EngineExtension(Protocol):
    """Engine Extension 协议。

    Extensions 在 Engine 生命周期钩子中运行:
      - on_init:       Engine 初始化后
      - on_phase_end:  每个 Phase 完成后
      - on_cycle_end:  整个 SOP 流水线完成后

    用法:
        class MyExtension:
            def on_init(self, engine):
                self.engine = engine

            def on_phase_end(self, module, phase, result):
                print(f"Phase {phase} done")

            def on_cycle_end(self, module, result):
                print(f"All done: {result.status}")
    """

    def on_init(self, engine: Engine) -> None:
        """Engine 初始化后调用。"""
        ...

    def on_phase_end(self, module: str, phase: str, result: dict) -> None:
        """每个 Phase 完成后调用。"""
        ...

    def on_cycle_end(self, module: str, result: RunResult) -> None:
        """整个 SOP 流水线完成后调用。"""
        ...

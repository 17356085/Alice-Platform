"""Adapter 接口 — 外部系统适配器抽象。

SDK 定义接口，平台层实现具体逻辑。
"""

from __future__ import annotations

from typing import Protocol, runtime_checkable


@runtime_checkable
class AuditAdapter(Protocol):
    """审计适配器接口。"""

    def check_state(self, module: str, page: str, state: dict) -> dict:
        """检查状态合规性。

        Args:
            module: 模块名
            page: 页面名
            state: 当前状态

        Returns:
            检查结果 {"passed": bool, "issues": list}
        """
        ...

    def check_sop(self, module: str, phase: str, result: dict) -> dict:
        """检查 SOP 合规性。

        Args:
            module: 模块名
            phase: 阶段名
            result: 阶段结果

        Returns:
            检查结果 {"passed": bool, "issues": list}
        """
        ...


@runtime_checkable
class EventAdapter(Protocol):
    """事件适配器接口。"""

    def emit(self, event_type: str, data: dict, **kwargs) -> None:
        """发射事件。

        Args:
            event_type: 事件类型
            data: 事件数据
            **kwargs: 额外参数
        """
        ...

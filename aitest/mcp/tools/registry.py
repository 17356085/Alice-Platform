"""
P2-3: Tool Registry — 注册表模式
P3-2: Tool 依赖元数据 — depends_on / produces / side_effect / estimated_duration
"""
from dataclasses import dataclass, field
from typing import Any, Callable

from aitest.mcp.rate_limit import ToolPermission, TOOL_PERMISSIONS


@dataclass
class ToolDef:
    """MCP Tool 注册项 — 单一事实源。新增 Tool 只需在 TOOL_REGISTRY 中添加一行。

    P3-2 新增元数据字段:
      - permission: 从 TOOL_PERMISSIONS 移入，每个 Tool 自带权限声明
      - depends_on: 前置依赖的其他 Tool 名称（Agent 可据此推导调用顺序）
      - produces: 产物类型（如 "test_result", "code_quality_report"）
      - side_effect: "read" | "write" | "execute" — 比 permission 更细粒度
      - estimated_duration: 预估耗时（Agent 调度决策用）
    """
    name: str
    description: str
    schema: dict
    handler: Any  # Callable[[dict], dict]
    # P3-2 元数据
    permission: ToolPermission = ToolPermission.READ
    depends_on: list[str] = field(default_factory=list)
    produces: list[str] = field(default_factory=list)
    side_effect: str = "read"
    estimated_duration: str = "1s"

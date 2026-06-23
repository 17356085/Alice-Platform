"""Capability Router — 统一能力路由层。

Week 2 Day 1-2: Agent 通过 Capability 名称调用能力，不关心底层实现。

参考:
  - Aperant config/agent-configs.ts (声明式 Agent → Tool 映射)
  - Aperant tools/registry.ts (ToolRegistry 模式)
  - AITest 现有 mcp/tools/registry.py (ToolDef dataclass)

用法:
    from aitest.platform.capabilities import create_router
    router = create_router()
    tools = router.tool_defs_for_agent("automation-agent")
    result = router.execute(tool_call, context)
"""
import time
import logging
from dataclasses import dataclass, field
from typing import Any, Optional, Protocol, runtime_checkable
from abc import ABC, abstractmethod

logger = logging.getLogger(__name__)


# ══════════════════════════════════════════════════════════════════════════
#  Data Types
# ══════════════════════════════════════════════════════════════════════════

@dataclass
class ToolDef:
    """工具定义 — 对应 LLM function calling 的 JSON Schema。"""
    name: str                           # e.g. "browser__navigate"
    description: str
    parameters: dict                    # JSON Schema
    capability: str = ""                # 所属 Capability
    side_effect: str = "read"           # read | write | execute
    estimated_duration: str = "1s"
    requires_confirmation: bool = False

    def to_openai_format(self) -> dict:
        """转为 OpenAI/Anthropic tool calling 格式。"""
        return {
            "type": "function",
            "function": {
                "name": self.name,
                "description": self.description,
                "parameters": self.parameters,
            },
        }


@dataclass
class ToolCall:
    """LLM 发起的单次工具调用。"""
    id: str
    name: str
    arguments: dict
    agent_name: str = ""
    timestamp: float = field(default_factory=lambda: time.time())


@dataclass
class ToolResult:
    """工具执行结果。"""
    call_id: str
    success: bool
    content: str                        # 文本返回给 LLM
    data: Any = None                    # 结构化数据 (供 Observation Bus)
    error: Optional[str] = None
    duration_ms: float = 0.0
    truncated: bool = False


# ══════════════════════════════════════════════════════════════════════════
#  CapabilityProvider — 能力提供者基类
# ══════════════════════════════════════════════════════════════════════════

class CapabilityProvider(ABC):
    """能力提供者基类。

    一个 Capability 可以有多个 Provider (e.g., BrowserUse + Playwright → browser.*)。
    Router 根据 context 选择最佳 Provider。
    """

    capability: str = ""                # e.g. "browser.navigate"
    provider_name: str = ""             # e.g. "browseruse"
    priority: int = 100                 # 越小越优先

    @abstractmethod
    def get_tool_def(self) -> ToolDef:
        """返回传给 LLM 的工具定义。"""
        ...

    @abstractmethod
    def available(self, context: dict) -> bool:
        """检查此 Provider 在当前上下文中是否可用。"""
        ...

    @abstractmethod
    def execute(self, call: ToolCall, context: dict) -> ToolResult:
        """执行工具调用。"""
        ...

    def truncation_limit(self) -> int:
        return 8000


# ══════════════════════════════════════════════════════════════════════════
#  CapabilityRouter
# ══════════════════════════════════════════════════════════════════════════

class CapabilityRouter:
    """统一能力路由层。

    用法:
        router = CapabilityRouter()
        router.register(BrowserNavigateProvider())
        tools = router.tool_defs_for_agent("automation-agent")
        result = router.execute(tool_call, context)
    """

    def __init__(self, load_plugins: bool = True):
        self._registry: dict[str, list[CapabilityProvider]] = {}
        self._agent_capabilities: dict[str, list[str]] = {}
        if load_plugins:
            self._load_plugins()

    # ── Plugin discovery ──────────────────────────────────────────

    def _load_plugins(self):
        """Load capability providers from installed plugins."""
        try:
            from aitest.platform.plugin import get_plugin_manager
            pm = get_plugin_manager()
            pm.load_all()
            providers = pm.get_providers()
            for name, cls in providers.items():
                try:
                    instance = cls()
                    self.register(instance)
                    logger.info(f"Plugin provider registered: {name} ({cls.__name__})")
                except Exception as e:
                    logger.warning(f"Failed to instantiate plugin provider '{name}': {e}")
        except Exception as e:
            logger.debug(f"Plugin system not available: {e}")

    # ── 注册 ─────────────────────────────────────────────────────

    def register(self, provider: CapabilityProvider) -> None:
        """注册一个能力提供者。"""
        cap = provider.capability
        if cap not in self._registry:
            self._registry[cap] = []
        self._registry[cap].append(provider)
        self._registry[cap].sort(key=lambda p: p.priority)

    def set_agent_capabilities(self, mapping: dict[str, list[str]]) -> None:
        """设置 Agent → Capability 映射。"""
        self._agent_capabilities = mapping

    # ── 查询 ─────────────────────────────────────────────────────

    def list_capabilities(self) -> list[str]:
        return list(self._registry.keys())

    def list_agents(self) -> list[str]:
        return list(self._agent_capabilities.keys())

    def resolve(self, capability: str, context: dict) -> CapabilityProvider:
        """根据上下文选择最佳 Provider。"""
        providers = self._registry.get(capability, [])
        for provider in providers:
            if provider.available(context):
                return provider
        raise CapabilityUnavailableError(f"No available provider for '{capability}'")

    def tool_defs_for_agent(self, agent_name: str) -> list[dict]:
        """获取 Agent 可用的所有工具定义（JSON Schema 格式，可直接传 LLM）。

        参考 Aperant agent-configs.ts: getRequiredMcpServers() 模式。
        """
        capabilities = self._agent_capabilities.get(agent_name, [])
        if not capabilities:
            # 默认给所有注册的 Capability
            capabilities = list(self._registry.keys())

        tools = []
        seen = set()
        for cap in capabilities:
            providers = self._registry.get(cap, [])
            for p in providers:
                td = p.get_tool_def()
                if td.name not in seen:
                    tools.append(td.to_openai_format())
                    seen.add(td.name)
                    break  # 取最高优先级的一个

        return tools

    # ── 执行 ─────────────────────────────────────────────────────

    def execute(self, call: ToolCall, context: dict) -> ToolResult:
        """执行工具调用。"""
        capability = self._tool_name_to_capability(call.name)
        if not capability:
            return ToolResult(
                call_id=call.id, success=False,
                content=f"Unknown tool: {call.name}",
                error=f"No capability registered for '{call.name}'"
            )

        try:
            provider = self.resolve(capability, context)
        except CapabilityUnavailableError as e:
            return ToolResult(call_id=call.id, success=False, content=str(e), error=str(e))

        try:
            result = provider.execute(call, context)
        except Exception as e:
            logger.exception(f"Tool execution failed: {call.name}")
            return ToolResult(
                call_id=call.id, success=False,
                content=f"Tool error: {e}", error=str(e)
            )

        # 输出截断 (参考 Aperant tools/truncation.ts)
        limit = provider.truncation_limit()
        if len(result.content) > limit:
            result.content = (
                result.content[:limit]
                + f"\n\n[... truncated {len(result.content) - limit} chars ...]"
            )
            result.truncated = True

        return result

    def execute_tool_calls(
        self, tool_calls: list[dict], context: dict, agent_name: str = ""
    ) -> list[ToolResult]:
        """批量执行 LLM 返回的 tool calls。"""
        results = []
        for tc in tool_calls:
            call = ToolCall(
                id=tc.get("id", ""),
                name=tc.get("name", tc.get("function", {}).get("name", "")),
                arguments=tc.get("input", tc.get("arguments", tc.get("function", {}).get("arguments", {}))),
                agent_name=agent_name,
            )
            results.append(self.execute(call, context))
        return results

    def _tool_name_to_capability(self, tool_name: str) -> Optional[str]:
        """工具名 → Capability 名映射。"""
        for cap, providers in self._registry.items():
            for p in providers:
                if p.get_tool_def().name == tool_name:
                    return cap
        return None


class CapabilityUnavailableError(Exception):
    """指定 Capability 无可用 Provider。"""
    pass

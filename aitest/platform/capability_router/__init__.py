"""Capability Router — 统一能力路由层。

Week 2 Day 1-2: Agent 通过 Capability 名称调用能力，不关心底层实现。

用法:
    from aitest.platform.capability_router import create_router, get_router
    router = create_router()
    tools = router.tool_defs_for_agent("automation-agent")
"""
from aitest.platform.capability_router.router import (
    CapabilityRouter, CapabilityProvider, CapabilityUnavailableError,
    ToolDef, ToolCall, ToolResult,
)
from aitest.platform.capability_router.agent_capabilities import AGENT_CAPABILITIES


def create_router() -> "CapabilityRouter":
    """工厂函数：创建预配置的 CapabilityRouter。"""
    from aitest.platform.capability_router.providers.browser import (
        BrowserNavigateProvider, BrowserScreenshotProvider,
    )
    from aitest.platform.capability_router.providers.knowledge import (
        RAGSearchProvider, BusinessRuleLookupProvider,
    )
    from aitest.platform.capability_router.providers.execute import (
        PytestProvider, PythonScriptProvider,
    )
    from aitest.platform.capability_router.providers.codegen import (
        PageObjectGenProvider, TestScriptGenProvider,
    )

    router = CapabilityRouter()
    for pc in [
        BrowserNavigateProvider, BrowserScreenshotProvider,
        RAGSearchProvider, BusinessRuleLookupProvider,
        PytestProvider, PythonScriptProvider,
        PageObjectGenProvider, TestScriptGenProvider,
    ]:
        router.register(pc())
    router.set_agent_capabilities(AGENT_CAPABILITIES)
    return router


_router: "CapabilityRouter" = None

def get_router() -> "CapabilityRouter":
    global _router
    if _router is None:
        _router = create_router()
    return _router

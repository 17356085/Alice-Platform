"""Optional bridge to the platform layer via explicit registered ports."""

from __future__ import annotations

from alice_engine.platform_ports import get_platform_ports


def get_planner_memory_context(module: str, task_description: str) -> str:
    """Resolve planner memory hints from the platform, if available."""
    try:
        fn = get_platform_ports().planner_memory_context
        if fn is None:
            return ""
        return fn(module, task_description)
    except Exception:
        return ""


def create_capability_router():
    """Create the platform capability router when the platform is installed."""
    try:
        factory = get_platform_ports().capability_router_factory
        if factory is None:
            return None
        return factory()
    except Exception:
        return None


def create_mcp_clients_for_agent(agent_name: str):
    """Connect MCP clients through the platform when available."""
    try:
        factory = get_platform_ports().mcp_clients_factory
        if factory is None:
            return [], {}
        return factory(agent_name)
    except Exception:
        return [], {}


def create_testing_memory_store():
    """Return the platform memory store when available."""
    try:
        factory = get_platform_ports().testing_memory_store_factory
        if factory is None:
            return None
        return factory()
    except Exception:
        return None


def get_knowledge_service():
    """Return the platform knowledge service when available."""
    try:
        factory = get_platform_ports().knowledge_service_factory
        if factory is None:
            return None
        return factory()
    except Exception:
        return None

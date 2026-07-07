"""Platform-side registration of explicit SDK ports."""

from __future__ import annotations

import asyncio

from alice_engine.platform_ports import configure_platform_ports


def _planner_memory_context(module: str, task_description: str) -> str:
    from aitest.knowledge.rag_engine import build_planner_memory_context

    return build_planner_memory_context(module=module, task_description=task_description)


def _capability_router_factory():
    from aitest.platform.capability_router import create_router

    return create_router()


def _mcp_clients_factory(agent_name: str):
    from aitest.mcp.mcp_client import create_mcp_clients_for_agent, merge_mcp_tools

    try:
        clients = asyncio.run(create_mcp_clients_for_agent(agent_name))
    except RuntimeError:
        clients = []
    return clients or [], merge_mcp_tools(clients or [])


def _testing_memory_store_factory():
    from aitest.platform.testing_memory_store import TestingMemoryStore

    return TestingMemoryStore()


def _knowledge_service_factory():
    from aitest.platform.knowledge import get_knowledge

    return get_knowledge()


def register_platform_ports():
    return configure_platform_ports(
        planner_memory_context=_planner_memory_context,
        capability_router_factory=_capability_router_factory,
        mcp_clients_factory=_mcp_clients_factory,
        testing_memory_store_factory=_testing_memory_store_factory,
        knowledge_service_factory=_knowledge_service_factory,
    )

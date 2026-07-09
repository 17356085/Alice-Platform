"""Platform-side registration of explicit SDK ports."""

from __future__ import annotations

import asyncio
import logging

from alice_engine.platform_ports import configure_platform_ports

logger = logging.getLogger(__name__)


def _planner_memory_context(module: str, task_description: str) -> str:
    from aitest.knowledge.rag_engine import build_planner_memory_context

    return build_planner_memory_context(module=module, task_description=task_description)


def _capability_router_factory():
    from aitest.platform.capability_router import create_router

    return create_router()


def _mcp_clients_factory(agent_name: str):
    """Create MCP clients for an agent, handling both sync and async call sites.

    asyncio.run() fails with RuntimeError("This event loop is already running")
    when called from within an async context (FastAPI, test fixtures with
    pytest-asyncio, etc.). In that case run_until_complete() on the *same*
    loop is NOT a valid fallback either — that loop is busy executing the
    code that called us, so scheduling more work on it just raises the same
    "already running" error. The only reliable fix is to run the coroutine
    to completion on a *different* thread with its own fresh event loop,
    which sidesteps the conflict entirely.

    If MCP SDK is missing (ImportError inside the coroutine) the individual
    connect helpers already degrade gracefully and return an empty client list,
    so no special handling is needed here beyond the loop-conflict path.
    """
    from aitest.mcp.mcp_client import create_mcp_clients_for_agent, merge_mcp_tools

    coro = create_mcp_clients_for_agent(agent_name)
    try:
        # Happy path: no running event loop (CLI, worker thread, etc.)
        clients = asyncio.run(coro)
    except RuntimeError as exc:
        # CPython's actual message is "asyncio.run() cannot be called from
        # a running event loop" (older versions said "This event loop is
        # already running"). Match both by checking for "running event loop".
        if "running event loop" in str(exc) or "already running" in str(exc):
            logger.debug(
                "MCP factory: event loop already running for agent=%s — "
                "running coroutine on a dedicated thread",
                agent_name,
            )
            try:
                coro.close()
            except Exception:
                pass
            clients = _run_coro_in_new_thread(agent_name)
        else:
            # Different RuntimeError (e.g. loop closed) — log and degrade.
            try:
                coro.close()
            except Exception:
                pass
            logger.warning(
                "MCP factory: asyncio.run() failed for agent=%s: %s — "
                "agent will run without MCP tools",
                agent_name,
                exc,
            )
            clients = []
    except Exception as exc:
        try:
            coro.close()
        except Exception:
            pass
        logger.warning(
            "MCP factory: unexpected error for agent=%s: %s — "
            "agent will run without MCP tools",
            agent_name,
            exc,
        )
        clients = []

    return clients or [], merge_mcp_tools(clients or [])


def _run_coro_in_new_thread(agent_name: str, timeout: float = 30.0):
    """Run create_mcp_clients_for_agent() to completion on a dedicated thread.

    Used when the calling thread already has a running event loop — a fresh
    thread gets a fresh loop, so asyncio.run() works normally there without
    colliding with the loop that is currently executing our caller.
    """
    import concurrent.futures

    from aitest.mcp.mcp_client import create_mcp_clients_for_agent

    def _runner():
        coro = create_mcp_clients_for_agent(agent_name)
        try:
            return asyncio.run(coro)
        except Exception:
            try:
                coro.close()
            except Exception:
                pass
            raise

    try:
        with concurrent.futures.ThreadPoolExecutor(max_workers=1) as pool:
            future = pool.submit(_runner)
            return future.result(timeout=timeout)
    except Exception as exc:
        logger.warning(
            "MCP factory: thread-based fallback failed for agent=%s: %s — "
            "agent will run without MCP tools",
            agent_name,
            exc,
        )
        return []


def _testing_memory_store_factory():
    from aitest.platform.testing_memory_store import TestingMemoryStore

    return TestingMemoryStore()


def _knowledge_service_factory():
    from aitest.platform.knowledge import get_knowledge

    return get_knowledge()


def register_platform_ports():
    """Register all explicit platform-side SDK ports."""
    return configure_platform_ports(
        planner_memory_context=_planner_memory_context,
        capability_router_factory=_capability_router_factory,
        mcp_clients_factory=_mcp_clients_factory,
        testing_memory_store_factory=_testing_memory_store_factory,
        knowledge_service_factory=_knowledge_service_factory,
    )

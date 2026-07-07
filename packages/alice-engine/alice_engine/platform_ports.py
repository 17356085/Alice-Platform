"""Explicit platform port registry for optional SDK integrations."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable


@dataclass
class PlatformPorts:
    planner_memory_context: Callable[[str, str], str] | None = None
    capability_router_factory: Callable[[], Any] | None = None
    mcp_clients_factory: Callable[[str], tuple[list[Any], dict[str, Any]]] | None = None
    testing_memory_store_factory: Callable[[], Any] | None = None
    knowledge_service_factory: Callable[[], Any] | None = None


_PORTS = PlatformPorts()


def configure_platform_ports(
    *,
    planner_memory_context: Callable[[str, str], str] | None = None,
    capability_router_factory: Callable[[], Any] | None = None,
    mcp_clients_factory: Callable[[str], tuple[list[Any], dict[str, Any]]] | None = None,
    testing_memory_store_factory: Callable[[], Any] | None = None,
    knowledge_service_factory: Callable[[], Any] | None = None,
) -> PlatformPorts:
    if planner_memory_context is not None:
        _PORTS.planner_memory_context = planner_memory_context
    if capability_router_factory is not None:
        _PORTS.capability_router_factory = capability_router_factory
    if mcp_clients_factory is not None:
        _PORTS.mcp_clients_factory = mcp_clients_factory
    if testing_memory_store_factory is not None:
        _PORTS.testing_memory_store_factory = testing_memory_store_factory
    if knowledge_service_factory is not None:
        _PORTS.knowledge_service_factory = knowledge_service_factory
    return _PORTS


def get_platform_ports() -> PlatformPorts:
    return _PORTS


def reset_platform_ports() -> None:
    global _PORTS
    _PORTS = PlatformPorts()

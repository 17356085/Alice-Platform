"""Capability contracts owned by the SDK boundary.

The SDK defines the stable shapes and provider protocol. Platform packages may
implement routing, authorization, plugin loading, and concrete tool execution
against these contracts without making ``alice_engine`` import platform code.
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Any, Protocol, runtime_checkable


@dataclass
class CapabilityToolDef:
    """LLM-facing tool definition for a capability provider."""

    name: str
    description: str
    parameters: dict[str, Any]
    capability: str = ""
    side_effect: str = "read"
    estimated_duration: str = "1s"
    requires_confirmation: bool = False

    def to_openai_format(self) -> dict[str, Any]:
        return {
            "type": "function",
            "function": {
                "name": self.name,
                "description": self.description,
                "parameters": self.parameters,
            },
        }


@dataclass
class CapabilityToolCall:
    """A single capability tool call requested by a model."""

    id: str
    name: str
    arguments: dict[str, Any]
    agent_name: str = ""
    timestamp: float = field(default_factory=time.time)


@dataclass
class CapabilityToolResult:
    """Result returned by a capability provider."""

    call_id: str
    success: bool
    content: str
    data: Any = None
    error: str | None = None
    duration_ms: float = 0.0
    truncated: bool = False


@dataclass
class CapabilityContract:
    """Discoverable contract for a capability provider."""

    capability: str
    tool_name: str
    description: str
    provider_name: str = ""
    side_effect: str = "read"
    estimated_duration: str = "1s"
    requires_confirmation: bool = False
    priority: int = 100
    available: bool = True
    source: str = "builtin"
    extra: dict[str, Any] = field(default_factory=dict)


@runtime_checkable
class CapabilityProvider(Protocol):
    """SDK port implemented by platform capability providers."""

    capability: str
    provider_name: str
    priority: int

    def get_tool_def(self) -> CapabilityToolDef:
        ...

    def available(self, context: dict[str, Any]) -> bool:
        ...

    def execute(
        self,
        call: CapabilityToolCall,
        context: dict[str, Any],
    ) -> CapabilityToolResult:
        ...


def capability_contract(
    provider: CapabilityProvider,
    *,
    available: bool = True,
    source: str = "builtin",
    **extra: Any,
) -> CapabilityContract:
    """Build the stable discovery contract for a provider implementation."""

    tool_def = provider.get_tool_def()
    return CapabilityContract(
        capability=provider.capability,
        tool_name=tool_def.name,
        description=tool_def.description,
        provider_name=provider.provider_name,
        side_effect=tool_def.side_effect,
        estimated_duration=tool_def.estimated_duration,
        requires_confirmation=tool_def.requires_confirmation,
        priority=provider.priority,
        available=available,
        source=source,
        extra=extra,
    )


# Backward-friendly aliases matching the platform router vocabulary.
ToolDef = CapabilityToolDef
ToolCall = CapabilityToolCall
ToolResult = CapabilityToolResult

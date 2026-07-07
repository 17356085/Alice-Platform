"""Shared contract assertions for extension samples.

Phase 4 PR 4.4 uses these helpers as the reusable baseline for provider,
capability, and graph extension tests.
"""

from __future__ import annotations

from typing import Any


def assert_provider_contract_shape(contract: Any, *, expected_name: str, expected_kind: str = "llm") -> None:
    """Validate the common provider contract shape."""
    assert contract is not None
    assert contract.name == expected_name
    assert contract.kind == expected_kind
    assert contract.module
    assert contract.class_name
    assert isinstance(contract.supports_tools, bool)
    assert isinstance(contract.supports_streaming, bool)
    assert isinstance(contract.available, bool)
    assert isinstance(contract.extra, dict)


def assert_capability_contract_shape(
    contract: Any,
    *,
    expected_capability: str,
    expected_tool_name: str,
) -> None:
    """Validate the common capability contract shape."""
    assert contract is not None
    assert contract.capability == expected_capability
    assert contract.tool_name == expected_tool_name
    assert contract.description
    assert contract.provider_name
    assert isinstance(contract.priority, int)
    assert isinstance(contract.available, bool)
    assert isinstance(contract.extra, dict)


def assert_graph_contract_shape(contract: Any, *, expected_graph_id: str) -> None:
    """Validate the common graph contract shape."""
    assert contract is not None
    assert contract.graph_id == expected_graph_id
    assert contract.name
    assert contract.module
    assert contract.builder_name
    assert contract.category
    assert isinstance(contract.supports_checkpoint, bool)
    assert isinstance(contract.supports_parallel, bool)
    assert isinstance(contract.available, bool)
    assert isinstance(contract.extra, dict)

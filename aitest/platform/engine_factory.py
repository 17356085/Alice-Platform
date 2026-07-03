"""
Execution Engine Factory — decouple API/Service from concrete engine implementations. v3.0

Eliminates hard imports of AgentLoop and SOPRunner from ExecutionService and API layer.
Instead, consumers call get_engine() which resolves the appropriate implementation at runtime.

Usage:
    from aitest.platform.engine_factory import get_engine, ExecutionEngine

    engine = get_engine("automation-agent", module="equipment", pages=["device-list"])
    state = engine.run()

    # Or for interactive (SSE) execution:
    engine = get_engine("sop", module="equipment", pages=["device-list"])
    for event in engine.run_interactive():
        process(event)
"""

from __future__ import annotations

import logging
from typing import Protocol, Any, Iterator, runtime_checkable

_log = logging.getLogger(__name__)


@runtime_checkable
class ExecutionEngine(Protocol):
    """Protocol for execution engines (AgentLoop, SOPRunner, etc.).

    Any class implementing these methods can be used as an execution engine.
    This decouples the API/Service layer from concrete implementations.
    """

    def run(self) -> Any:
        """Execute synchronously. Returns execution state."""
        ...

    def run_interactive(self) -> Iterator[Any]:
        """Execute with streaming events (for SSE). Yields AgentEvent objects."""
        ...

    def cancel(self) -> None:
        """Request cancellation. Best-effort."""
        ...


# ── Engine Registry ─────────────────────────────────────────────────────

_ENGINES: dict[str, type] = {}


def register_engine(name: str, cls: type) -> None:
    """Register an engine implementation. Call at module import time."""
    _ENGINES[name] = cls


def _ensure_builtin_engines() -> None:
    """Lazy-register built-in engines. Called once on first get_engine()."""
    if _ENGINES:
        return

    # AgentLoop — the standard agent execution engine
    try:
        from aitest.agents.agent_runner import AgentLoop
        register_engine("agent", AgentLoop)
        # Also register common agent names
        for agent_name in ("automation-agent", "execution-agent", "test-design-agent",
                           "review-agent", "arch-agent", "dev-agent"):
            register_engine(agent_name, AgentLoop)
    except ImportError:
        _log.warning("AgentLoop not available — agent engines disabled")

    # SOPRunner — SOP graph execution engine
    try:
        from aitest.graphs.sop_runner import SOPRunner
        register_engine("sop", SOPRunner)
    except ImportError:
        _log.warning("SOPRunner not available — SOP engine disabled")


def get_engine(
    engine_type: str,
    *,
    module: str = "",
    pages: list[str] | None = None,
    page: str = "",
    agent: str = "",
    provider: str = "",
    mode: str = "full",
    verbose: bool = False,
    **kwargs,
) -> ExecutionEngine:
    """Factory: resolve and instantiate an execution engine.

    Args:
        engine_type: Engine name ("agent", "sop", "automation-agent", etc.)
        module: Target module name
        pages: Page slugs to execute
        page: Single page (for AgentLoop compat)
        agent: Agent name (for AgentLoop)
        provider: LLM provider
        mode: Execution mode
        verbose: Verbose logging
        **kwargs: Additional engine-specific args

    Returns:
        ExecutionEngine instance

    Raises:
        ValueError: If engine_type is not registered
    """
    _ensure_builtin_engines()

    # Resolve: direct match → agent fallback
    cls = _ENGINES.get(engine_type)
    if cls is None:
        # Try "agent" as fallback for unknown agent names
        cls = _ENGINES.get("agent")
        if cls is None:
            raise ValueError(
                f"Unknown engine type '{engine_type}'. "
                f"Registered: {list(_ENGINES.keys())}"
            )
        _log.info(f"Engine type '{engine_type}' not registered, falling back to 'agent'")

    pages = pages or []
    effective_page = page or (pages[0] if pages else "")

    # Instantiate based on engine class
    from aitest.agents.agent_runner import AgentLoop as _AgentLoop
    from aitest.graphs.sop_runner import SOPRunner as _SOPRunner

    if cls is _AgentLoop or (isinstance(cls, type) and issubclass(cls, _AgentLoop)):
        return cls(
            agent_name=agent or engine_type if engine_type not in ("agent",) else agent or "automation-agent",
            provider=provider or None,
            module=module,
            page=effective_page,
            pages=pages,
            verbose=verbose,
            **kwargs,
        )
    elif cls is _SOPRunner or (isinstance(cls, type) and issubclass(cls, _SOPRunner)):
        return cls(
            module=module,
            pages=pages,
            provider=provider or None,
            mode=mode,
            **kwargs,
        )
    else:
        # Generic instantiation
        return cls(**kwargs)

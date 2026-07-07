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

__all__ = ["ExecutionEngine", "get_engine", "register_engine", "get_execution_kernel", "resolve_kernel_kind"]

import logging
from dataclasses import dataclass
from typing import Protocol, Any, Iterator, runtime_checkable, Callable

from alice_engine.kernel import ExecutionKernel, RuntimeExecutionKernel

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

@dataclass
class _EngineSpec:
    name: str
    factory: Callable[..., "ExecutionEngine"]


_ENGINES: dict[str, _EngineSpec] = {}
_KERNEL: ExecutionKernel | None = None


def register_engine(
    name: str,
    factory: Callable[..., "ExecutionEngine"],
    *,
    aliases: list[str] | None = None,
) -> None:
    """Register an engine implementation factory."""
    spec = _EngineSpec(name=name, factory=factory)
    _ENGINES[name] = spec
    for alias in aliases or []:
        _ENGINES[alias] = spec


def _build_agent_engine(
    *,
    engine_type: str,
    module: str = "",
    pages: list[str] | None = None,
    page: str = "",
    agent: str = "",
    provider: str = "",
    verbose: bool = False,
    checkpoint_thread_id: str = "",
    **kwargs,
) -> ExecutionEngine:
    from alice_engine.core.executor import AgentLoop

    pages = pages or []
    effective_page = page or (pages[0] if pages else "")
    agent_name = agent or (engine_type if engine_type not in ("agent", "sop") else "automation-agent")
    return AgentLoop(
        agent_name=agent_name,
        provider=provider or None,
        module=module,
        page=effective_page,
        pages=pages,
        verbose=verbose,
        **kwargs,
    )


def _build_sop_engine(
    *,
    module: str = "",
    pages: list[str] | None = None,
    provider: str = "",
    mode: str = "full",
    run_id: str = "",
    checkpoint_thread_id: str = "",
    **kwargs,
) -> ExecutionEngine:
    from alice_engine.workflow.sop_runner import SOPRunner

    return SOPRunner(
        module=module,
        pages=pages or [],
        provider=provider or None,
        mode=mode,
        run_id=run_id,
        checkpoint_thread_id=checkpoint_thread_id,
        **kwargs,
    )


def _ensure_builtin_engines() -> None:
    """Lazy-register built-in engines. Called once on first get_engine()."""
    try:
        from aitest.platform.sdk_ports import register_platform_ports

        register_platform_ports()
    except Exception:
        pass
    if _ENGINES:
        return

    # AgentLoop — the standard agent execution engine
    try:
        register_engine(
            "agent",
            _build_agent_engine,
            aliases=[
                "automation-agent",
                "execution-agent",
                "test-design-agent",
                "review-agent",
                "arch-agent",
                "dev-agent",
                "project-agent",
                "requirement-agent",
                "report-agent",
                "knowledge-agent",
                "bug-analysis-agent",
            ],
        )
    except ImportError:
        _log.warning("AgentLoop not available — agent engines disabled")

    # SOPRunner — SOP graph execution engine
    try:
        register_engine("sop", _build_sop_engine)
    except ImportError:
        _log.warning("SOPRunner not available — SOP engine disabled")


def get_execution_kernel() -> ExecutionKernel:
    """Return the shared public kernel for platform synchronous execution."""
    global _KERNEL
    try:
        from aitest.platform.sdk_ports import register_platform_ports

        register_platform_ports()
    except Exception:
        pass
    if _KERNEL is None:
        _KERNEL = RuntimeExecutionKernel()
    return _KERNEL


def resolve_kernel_kind(engine_type: str, *, agent: str = "") -> str:
    """Map platform engine selectors onto the public kernel request kind."""
    effective = (agent or engine_type or "").strip()
    return "sop" if effective == "sop" else "agent"


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
    spec = _ENGINES.get(engine_type)
    if spec is None:
        # Try "agent" as fallback for unknown agent names
        spec = _ENGINES.get("agent")
        if spec is None:
            raise ValueError(
                f"Unknown engine type '{engine_type}'. "
                f"Registered: {list(_ENGINES.keys())}"
            )
        _log.info(f"Engine type '{engine_type}' not registered, falling back to 'agent'")

    return spec.factory(
        engine_type=engine_type,
        module=module,
        pages=pages or [],
        page=page,
        agent=agent,
        provider=provider,
        mode=mode,
        verbose=verbose,
        **kwargs,
    )

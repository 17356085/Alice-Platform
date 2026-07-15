"""Thread-scoped runtime environment overrides for legacy executor paths."""

from __future__ import annotations

import os
import threading
from contextlib import contextmanager
from pathlib import Path
from typing import Iterator

_STATE = threading.local()
_TEST_PROJECT_ROOT: Path | None = None


def _state_dict() -> dict[str, object]:
    state = getattr(_STATE, "values", None)
    if state is None:
        state = {}
        _STATE.values = state
    return state


def current_workstudy() -> Path:
    override = _state_dict().get("workstudy")
    if override is not None:
        return Path(override)
    return Path(os.environ.get("ENGINE_WORKSTUDY", os.environ.get("AITEST_WORKSTUDY", ".")))


def current_context_modules() -> Path:
    workstudy = current_workstudy()
    tlo_modules = workstudy / ".tlo" / "knowledge" / "modules"
    return tlo_modules if tlo_modules.exists() else workstudy / "context"


def configure_test_project_root(root: str | Path | None) -> None:
    """Set the project root used when resolving external test artifacts."""
    global _TEST_PROJECT_ROOT
    _TEST_PROJECT_ROOT = Path(root) if root is not None else None


def current_test_project_root() -> Path | None:
    """Return the configured external test project root, if any."""
    override = _state_dict().get("test_project_root")
    if override is not None:
        return Path(override)
    return _TEST_PROJECT_ROOT


def current_llm_provider(default: str = "anthropic") -> str:
    if current_mock_llm():
        return "mock"
    override = _state_dict().get("llm_provider")
    if override is not None:
        return str(override)
    return os.environ.get("LLM_PROVIDER", os.environ.get("AITEST_PROVIDER", default))


def current_mock_llm() -> bool:
    override = _state_dict().get("mock_llm")
    if override is not None:
        return bool(override)
    return os.environ.get("MOCK_LLM") == "1"


@contextmanager
def runtime_environment_scope(
    *,
    workstudy: str | Path | None = None,
    llm_provider: str | None = None,
    mock_llm: bool | None = None,
) -> Iterator[None]:
    state = _state_dict()
    previous = dict(state)
    try:
        if workstudy is not None:
            state["workstudy"] = Path(workstudy)
        if llm_provider is not None:
            state["llm_provider"] = llm_provider
        if mock_llm is not None:
            state["mock_llm"] = mock_llm
        yield
    finally:
        _STATE.values = previous

"""
Shared fixtures for Alice platform tests.

Principles:
  - No real LLM calls — FakeLLMProvider returns controlled responses.
  - No real env vars — isolated_env saves/restores os.environ per test.
  - Real SQLite for DB tests (fast, no external process).
  - Real filesystem in temp dirs for worktree/artifact tests.
"""

from __future__ import annotations

import os
import sys
import tempfile
import shutil
from pathlib import Path
from collections.abc import Generator
from typing import Optional
from dataclasses import dataclass, field
from unittest.mock import MagicMock

import pytest

# Ensure aitest is importable
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))


# ══════════════════════════════════════════════════════════════════════════
#  Fake LLM Provider — controllable, no network
# ══════════════════════════════════════════════════════════════════════════

@dataclass
class PresetResponse:
    """A single preset response for FakeLLMProvider."""
    content: str = ""
    tool_calls: list[dict] = field(default_factory=list)
    token_usage: dict = field(default_factory=dict)
    model: str = "fake-model"
    finish_reason: str = "stop"

    # Stream events to emit before returning
    stream_events: list = field(default_factory=list)


class FakeLLMProvider:
    """
    Controllable fake LLM provider for testing.

    Usage:
        fake = FakeLLMProvider()
        fake.set_response("Hello, world!")
        # or with tool calls:
        fake.set_response("ok", tool_calls=[{"name": "read", "args": {...}}])
        # or queue multiple responses:
        fake.queue_response("First call response")
        fake.queue_response("Second call response")
        # or simulate error:
        fake.set_error(RuntimeError("API down"))
    """

    def __init__(self):
        self._presets: list[PresetResponse] = []
        self._errors: list[Exception] = []
        self._call_count = 0
        self._last_system_prompt: str = ""
        self._last_user_prompt: str = ""
        self._last_tools: list[dict] = []
        self._last_temperature: float = 0.7
        self._last_max_tokens: int = 8192

    # ── Control interface ─────────────────────────────────────────────

    def set_response(
        self,
        content: str = "",
        *,
        tool_calls: list[dict] | None = None,
        token_usage: dict | None = None,
        model: str = "fake-model",
        finish_reason: str = "stop",
    ) -> None:
        """Set a single response. Clears any queued responses."""
        self._presets = [PresetResponse(
            content=content,
            tool_calls=tool_calls or [],
            token_usage=token_usage or {"input": 10, "output": len(content.split())},
            model=model,
            finish_reason=finish_reason,
        )]
        self._errors = []

    def queue_response(
        self,
        content: str = "",
        *,
        tool_calls: list[dict] | None = None,
        token_usage: dict | None = None,
        model: str = "fake-model",
        finish_reason: str = "stop",
    ) -> None:
        """Queue a response. Consumed in FIFO order."""
        self._presets.append(PresetResponse(
            content=content,
            tool_calls=tool_calls or [],
            token_usage=token_usage or {"input": 10, "output": len(content.split())},
            model=model,
            finish_reason=finish_reason,
        ))

    def set_error(self, error: Exception) -> None:
        """Set an error to raise on next call."""
        self._errors = [error]
        self._presets = []

    def queue_error(self, error: Exception) -> None:
        """Queue an error for a future call."""
        self._errors.append(error)

    # ── Call inspection ───────────────────────────────────────────────

    @property
    def call_count(self) -> int:
        return self._call_count

    @property
    def last_system_prompt(self) -> str:
        return self._last_system_prompt

    @property
    def last_user_prompt(self) -> str:
        return self._last_user_prompt

    @property
    def last_tools(self) -> list[dict]:
        return self._last_tools

    # ── LLMProvider interface ─────────────────────────────────────────

    def complete(
        self,
        system_prompt: str,
        user_prompt: str,
        tools: Optional[list[dict]] = None,
        temperature: float = 0.7,
        max_tokens: int = 8192,
    ):
        from aitest.llm.provider_base import LLMResponse

        self._call_count += 1
        self._last_system_prompt = system_prompt
        self._last_user_prompt = user_prompt
        self._last_tools = tools or []
        self._last_temperature = temperature
        self._last_max_tokens = max_tokens

        # Raise error if queued
        if self._errors:
            raise self._errors.pop(0)

        # Pop next preset or default empty
        preset = self._presets.pop(0) if self._presets else PresetResponse()

        return LLMResponse(
            content=preset.content,
            tool_calls=preset.tool_calls,
            token_usage=preset.token_usage,
            model=preset.model,
            finish_reason=preset.finish_reason,
        )

    def stream_complete(
        self,
        system_prompt: str,
        user_prompt: str,
        tools: Optional[list[dict]] = None,
        temperature: float = 0.7,
        max_tokens: int = 8192,
    ) -> Generator:
        from aitest.llm.provider_base import StreamEvent, LLMResponse

        self._call_count += 1
        self._last_system_prompt = system_prompt
        self._last_user_prompt = user_prompt
        self._last_tools = tools or []
        self._last_temperature = temperature
        self._last_max_tokens = max_tokens

        if self._errors:
            raise self._errors.pop(0)

        preset = self._presets.pop(0) if self._presets else PresetResponse()

        if preset.stream_events:
            for event in preset.stream_events:
                yield event
        else:
            # Default: emit content_start → content_chunk → content_end → done
            yield StreamEvent(type="content_start", content="")
            yield StreamEvent(type="content_chunk", content=preset.content)
            yield StreamEvent(type="content_end", content="")

        yield StreamEvent(
            type="done",
            finish_reason=preset.finish_reason,
            token_usage=preset.token_usage,
        )

        return LLMResponse(
            content=preset.content,
            tool_calls=preset.tool_calls,
            token_usage=preset.token_usage,
            model=preset.model,
            finish_reason=preset.finish_reason,
        )

    def supports_tools(self) -> bool:
        return True


# ══════════════════════════════════════════════════════════════════════════
#  Fixtures
# ══════════════════════════════════════════════════════════════════════════


@pytest.fixture
def fake_llm() -> FakeLLMProvider:
    """Fresh FakeLLMProvider — no network, fully controllable."""
    return FakeLLMProvider()


@pytest.fixture
def temp_dir() -> Generator[Path, None, None]:
    """Temporary directory, auto-cleaned after test."""
    path = Path(tempfile.mkdtemp(prefix="aitest_"))
    yield path
    shutil.rmtree(path, ignore_errors=True)


@pytest.fixture
def temp_worktree(temp_dir: Path) -> Path:
    """Temporary worktree directory inside temp_dir."""
    wt = temp_dir / "worktree"
    wt.mkdir(parents=True, exist_ok=True)
    return wt


@pytest.fixture
def isolated_env(monkeypatch) -> Generator[dict, None, None]:
    """
    Isolate environment variables. Returns a dict you can mutate
    to set test values. Original values restored after test.

    Usage:
        def test_foo(isolated_env):
            isolated_env["ANTHROPIC_API_KEY"] = "sk-test"
            # ... test code that reads ANTHROPIC_API_KEY
    """
    saved = {}
    # Remove all AITEST/LLM-related env vars
    for key in list(os.environ.keys()):
        if any(prefix in key.upper() for prefix in (
            "AITEST_", "ANTHROPIC_", "OPENAI_", "DEEPSEEK_",
            "MIMO_", "GOOGLE_", "BU_", "BROWSER_",
        )):
            saved[key] = os.environ.pop(key, None)

    # Provide a dict the test can mutate
    overrides: dict[str, str] = {}

    def _getenv(key, default=None):
        return overrides.get(key) or os.environ.get(key, default)

    monkeypatch.setattr(os, "environ", os.environ)  # ensure real os.environ
    for key, val in saved.items():
        if val is not None:
            monkeypatch.delenv(key, raising=False)

    yield overrides

    # Restore
    for key, val in saved.items():
        if val is not None:
            os.environ[key] = val


@pytest.fixture
def clean_config(isolated_env):
    """Config instance with all external API keys cleared. Safe for unit tests."""
    # Clear cached config singleton
    import aitest.config as _cfg_mod
    old = getattr(_cfg_mod, "_config_instance", None)
    _cfg_mod._config_instance = None

    from aitest.config import Config
    cfg = Config()
    yield cfg

    # Restore
    _cfg_mod._config_instance = old


@pytest.fixture
def observation_bus():
    """Fresh ObservationBus instance — no existing subscribers."""
    from aitest.platform.observation_bus import ObservationBus
    return ObservationBus()


@pytest.fixture
def fake_event_bus(monkeypatch):
    """
    Mock platform event_bus that records published events.
    Prevents real event_bus from trying to spawn threads/subscribers.
    """
    events: list = []

    class FakeBus:
        def publish(self, event_type, event_data=None):
            events.append({"type": event_type, "data": event_data or {}})

        def subscribe(self, event_type, callback):
            pass  # no-op in tests

        def unsubscribe(self, callback):
            pass

    fake = FakeBus()
    # Patch get_bus to return fake
    monkeypatch.setattr(
        "aitest.platform.event_bus.get_event_bus",
        lambda: fake,
    )
    # Also patch the singleton accessor if it exists
    monkeypatch.setattr(
        "aitest.platform.event_bus._bus",
        fake,
        raising=False,
    )
    return fake


@pytest.fixture
def test_db_path(temp_dir: Path) -> Path:
    """Path to a temporary SQLite database file."""
    return temp_dir / "test.db"

"""Executor utility functions — lightweight helpers for AgentLoop.

This module contains:
- Logging setup
- Encoding fixes
- Config stubs
- Trace context stubs
- No-op tracer

Extracted from executor.py to reduce file size and improve modularity.
"""

from __future__ import annotations

import io
import sys
import logging as _logging
import threading
from pathlib import Path

from alice_engine.core.runtime_environment import (
    current_llm_provider,
    current_workstudy,
)


# ══════════════════════════════════════════════════════════════════════════
#  Encoding Fix
# ══════════════════════════════════════════════════════════════════════════


def fix_stdout_encoding():
    """修复 Windows GBK 编码问题。仅在需要时调用。"""
    if hasattr(sys.stdout, 'buffer') and not isinstance(sys.stdout, io.TextIOWrapper):
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')


# ══════════════════════════════════════════════════════════════════════════
#  Logging
# ══════════════════════════════════════════════════════════════════════════


def get_logger(name: str):
    """获取 logger。executor 自包含，不依赖上层 wrapper。"""
    return _logging.getLogger(name)


# ══════════════════════════════════════════════════════════════════════════
#  Path Helpers
# ══════════════════════════════════════════════════════════════════════════


def get_project_dir() -> Path:
    """获取项目目录。"""
    return current_workstudy()


def get_test_project_root() -> Path:
    """获取测试项目根目录。"""
    return current_workstudy()


# ══════════════════════════════════════════════════════════════════════════
#  Config Stub (Minimal)
# ══════════════════════════════════════════════════════════════════════════


class _Config:
    """最小化 config 替代品。"""

    @staticmethod
    def resolve_llm_provider() -> str:
        return current_llm_provider("anthropic")

    @staticmethod
    def resolve_model_for_tier(tier: str, provider: str) -> dict:
        return {"model": "claude-sonnet-4-6", "provider": provider}


config = _Config()


# ══════════════════════════════════════════════════════════════════════════
#  Trace Context Stub (Thread-local)
# ══════════════════════════════════════════════════════════════════════════


class _TraceContext:
    """最小化 TraceContext 替代品。"""
    _local = threading.local()

    @classmethod
    def set(cls, **kwargs):
        for k, v in kwargs.items():
            setattr(cls._local, k, v)

    @classmethod
    def get_skill_version(cls) -> str:
        return getattr(cls._local, "skill_version", "latest")


TraceContext = _TraceContext


# ══════════════════════════════════════════════════════════════════════════
#  No-op Tracer (OpenTelemetry stub)
# ══════════════════════════════════════════════════════════════════════════


class _NoopSpan:
    def __enter__(self):
        return self

    def __exit__(self, *args):
        pass

    def set_attribute(self, *args):
        pass


class _NoopTracer:
    def start_as_current_span(self, name):
        return _NoopSpan()


def get_tracer():
    """最小化 tracer 替代品。"""
    return _NoopTracer()

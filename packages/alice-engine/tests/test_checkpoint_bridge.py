"""Checkpoint bridge smoke tests."""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path


def _load_checkpoint_bridge():
    path = Path(__file__).resolve().parents[3] / "aitest" / "platform" / "checkpoint.py"
    spec = importlib.util.spec_from_file_location("aitest_platform_checkpoint_test", path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def test_checkpoint_bridge_returns_empty_snapshot_for_missing_thread():
    bridge = _load_checkpoint_bridge()
    snapshot = bridge.get_checkpoint_snapshot("missing-thread", governance_path=".")
    assert snapshot.thread_id == "missing-thread"
    assert snapshot.available is False
    assert snapshot.has_values is False


def test_checkpoint_bridge_instance():
    bridge = _load_checkpoint_bridge()
    instance = bridge.get_checkpoint_bridge(".")
    assert instance.has_snapshot("missing-thread") is False

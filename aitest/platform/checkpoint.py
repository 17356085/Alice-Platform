"""Platform checkpoint bridge.

This module keeps resume logic on the platform side while reusing the SDK's
checkpoint manager implementation.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any


@dataclass
class CheckpointSnapshot:
    """Lightweight checkpoint snapshot used for resume planning."""

    thread_id: str
    available: bool = False
    values: dict[str, Any] = field(default_factory=dict)
    raw: dict[str, Any] = field(default_factory=dict)
    loaded_at: str = ""

    @property
    def has_values(self) -> bool:
        return bool(self.values)


class CheckpointBridge:
    """Bridge to the LangGraph checkpoint store used by SOP execution."""

    def __init__(self, governance_path: str = "."):
        self.governance_path = governance_path

    def get_snapshot(self, thread_id: str) -> CheckpointSnapshot:
        snapshot = CheckpointSnapshot(thread_id=thread_id, loaded_at=datetime.now(timezone.utc).isoformat())
        try:
            from alice_engine.runtime.checkpoint import CheckpointManager

            manager = CheckpointManager(self.governance_path)
            checkpointer = manager.get_checkpointer()
            if checkpointer is None:
                return snapshot
            saved = checkpointer.get_tuple({"configurable": {"thread_id": thread_id}})
            if not saved or not getattr(saved, "checkpoint", None):
                return snapshot

            checkpoint = saved.checkpoint
            channel_values = checkpoint.get("channel_values", {})
            if isinstance(channel_values, dict):
                snapshot.values = dict(channel_values)
            snapshot.raw = checkpoint if isinstance(checkpoint, dict) else {}
            snapshot.available = True
        except Exception:
            return snapshot
        return snapshot

    def has_snapshot(self, thread_id: str) -> bool:
        return self.get_snapshot(thread_id).available


def get_checkpoint_bridge(governance_path: str = ".") -> CheckpointBridge:
    return CheckpointBridge(governance_path)


def get_checkpoint_snapshot(thread_id: str, governance_path: str = ".") -> CheckpointSnapshot:
    return get_checkpoint_bridge(governance_path).get_snapshot(thread_id)

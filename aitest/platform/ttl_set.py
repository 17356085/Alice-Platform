"""
TTLSet — bounded, time-aware idempotency tracker. v2.5

Replaces unbounded `set[str]` for deduplication across all event consumers.
Uses OrderedDict for O(1) insert + O(1) oldest-eviction.

Design:
  - max_size: cap total entries (default 10,000). Evict oldest on overflow.
  - max_age_s: max age in seconds (default 86,400 = 24h). Entries older than
    this are treated as "not seen" and cleaned on access.
  - Thread-safe via internal lock.
  - add() returns True if first-time (idempotency gate).
  - Memory: ~100 bytes/entry. At 10k entries → ~1 MB. Bounded, not growing.

Usage:
    from aitest.platform.ttl_set import TTLSet

    seen = TTLSet(max_size=10_000, max_age_s=86_400)
    if seen.add(event_id):
        process(event)   # first time
    # else: already seen within TTL window
"""

from __future__ import annotations

import threading
import time
from collections import OrderedDict


class TTLSet:
    """Bounded set with TTL-based eviction. Thread-safe."""

    def __init__(self, max_size: int = 10_000, max_age_s: float = 86_400.0):
        if max_size < 1:
            raise ValueError("max_size must be >= 1")
        self._max_size = max_size
        self._max_age_s = max_age_s
        self._lock = threading.Lock()
        # OrderedDict: key → inserted_at (monotonic timestamp)
        self._entries: OrderedDict[str, float] = OrderedDict()

    def add(self, key: str) -> bool:
        """Add key. Returns True if first-time (not in set / expired).
        Returns False if already seen within TTL window.

        Also triggers eviction on insert — bounded memory.
        """
        now = time.monotonic()
        with self._lock:
            # 1. Check if already present and not expired
            if key in self._entries:
                inserted_at = self._entries[key]
                if now - inserted_at < self._max_age_s:
                    return False  # still fresh → duplicate
                # Expired → remove and re-add as new
                del self._entries[key]

            # 2. Evict if at capacity
            while len(self._entries) >= self._max_size:
                self._entries.popitem(last=False)  # FIFO: evict oldest

            # 3. Insert
            self._entries[key] = now
            return True

    def __contains__(self, key: str) -> bool:
        """Check membership with TTL. Does NOT auto-clean on read —
        use add() for the idempotency gate; this is for introspection."""
        now = time.monotonic()
        with self._lock:
            ts = self._entries.get(key)
            if ts is None:
                return False
            if now - ts >= self._max_age_s:
                return False
            return True

    def __len__(self) -> int:
        with self._lock:
            return len(self._entries)

    def cleanup(self) -> int:
        """Explicit stale cleanup. Returns number evicted."""
        now = time.monotonic()
        removed = 0
        with self._lock:
            stale = [
                k for k, ts in self._entries.items()
                if now - ts >= self._max_age_s
            ]
            for k in stale:
                del self._entries[k]
                removed += 1
        return removed

    def clear(self):
        with self._lock:
            self._entries.clear()

    @property
    def max_size(self) -> int:
        return self._max_size

    @property
    def max_age_s(self) -> float:
        return self._max_age_s

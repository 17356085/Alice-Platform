"""
RunEventConsumer — the one small abstraction v2.4 introduces.

Protocol for event consumers. Enables future async/thread-pool/remote
dispatch without changing individual consumers.

Usage:
    from aitest.platform.consumer import RunEventConsumer

    class MyConsumer(RunEventConsumer):
        def handle(self, event: RunEvent) -> None:
            print(f"Got event: {event.event_type}")
"""

from typing import Protocol

from .run_event import RunEvent


class RunEventConsumer(Protocol):
    """Consume a RunEvent. May be called synchronously or on a background thread."""

    def handle(self, event: RunEvent) -> None:
        ...

    def close(self) -> None:
        """Optional cleanup. Called on shutdown."""
        ...

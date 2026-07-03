"""
RunEventConsumer — the one small abstraction v2.4 introduces.

Protocol for event consumers. Enables future async/thread-pool/remote
dispatch without changing individual consumers.

All platform consumers follow this lifecycle:
    consumer = MyConsumer()
    consumer.start()       # subscribes to EventBus
    # ... consumer handles events ...
    consumer.stop()        # unsubscribes from EventBus

Usage:
    from aitest.platform.consumer import RunEventConsumer

    class MyConsumer:
        def start(self) -> None:
            get_bus().subscribe(EventType.RUN_COMPLETED, self._on_completed)

        def stop(self) -> None:
            get_bus().unsubscribe(EventType.RUN_COMPLETED, self._on_completed)

        @property
        def is_active(self) -> bool:
            return self._active
"""

from typing import Protocol, runtime_checkable

from .run_event import RunEvent
from aitest.infra.logging import get_logger
_log = get_logger(__name__)


@runtime_checkable
class RunEventConsumer(Protocol):
    """Lifecycle protocol for event consumers.

    Consumers subscribe to the EventBus on start() and unsubscribe on stop().
    is_active reports whether the consumer is currently subscribed.
    """

    def start(self) -> None:
        """Subscribe to EventBus. Called once at server startup."""
        ...

    def stop(self) -> None:
        """Unsubscribe from EventBus. Called once at server shutdown."""
        ...

    @property
    def is_active(self) -> bool:
        """Whether this consumer is currently subscribed to the EventBus."""
        ...

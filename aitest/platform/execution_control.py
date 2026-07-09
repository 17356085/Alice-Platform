"""Execution control plane — cancellation, timeout, and run lifecycle management.

This module handles:
- Run cancellation
- Timeout enforcement
- Resume operations
- Active run tracking
- Control handle registration

Extracted from execution_service.py to improve modularity.
"""

from __future__ import annotations

import threading
from typing import Any

from alice_engine.contracts import ExecutionContext, ExecutionResult

from .run import Run
from .run_event import EventType, make_event
from .run_store import RunStore


class ExecutionControl:
    """Control plane for managing run lifecycle and cancellation."""

    def __init__(self, store: RunStore, bus: Any):
        """Initialize control plane.

        Args:
            store: Run store for persistence
            bus: Event bus for publishing control events
        """
        self._store = store
        self._bus = bus
        self._active_controls: dict[str, Any] = {}
        self._controls_lock = threading.Lock()

    def resume(self, run_id: str, execute_callback) -> ExecutionResult | None:
        """Resume a paused or interrupted run.

        Args:
            run_id: ID of the run to resume
            execute_callback: Function to call to re-execute (signature: execute(ctx, **kwargs) -> ExecutionResult)

        Returns:
            ExecutionResult if resumed successfully, None if run not found or already completed
        """
        run = self._store.load_run(run_id)
        if run is None or run.status == "completed":
            return None

        checkpoint_thread_id = run.request_id or run.run_id
        ctx = ExecutionContext(
            workspace_id=run.workspace_id,
            user_id=run.triggered_by,
            scopes=["read", "execute"],
            org_id=run.org_id,
            module=run.module,
            pages=list(run.pages),
            agent=run.agent,
            mode=run.mode,
            metadata={"entrypoint": "resume", "trigger_type": "resume"},
        )
        result = execute_callback(
            ctx,
            module=run.module,
            pages=run.pages,
            agent=run.agent,
            mode="resume",
            provider="",
            checkpoint_thread_id=checkpoint_thread_id,
        )
        return result

    def cancel(self, request_id: str) -> bool:
        """Cancel an execution request and all associated runs.

        Args:
            request_id: Request ID to cancel

        Returns:
            True if cancelled, False if request not found or already frozen
        """
        runs = self._store.list_runs(limit=500)
        run = next((r for r in runs if r.request_id == request_id), None)
        if run is None or run.is_frozen:
            return False

        control = self._get_control(run.run_id)
        if control is not None and hasattr(control, "cancel"):
            control.cancel()

        run.cancel()
        self._store.save_run(run)
        request = self._store.load_request(request_id)
        if request:
            request.cancel()
            self._store.save_request(request)

        ev = make_event(
            EventType.RUN_CANCELLED,
            run_id=run.run_id,
            request_id=request_id,
            workspace_id=run.workspace_id,
            org_id=run.org_id,
            module=run.module,
            agent=run.agent,
        )
        self._store.save_event(ev)
        self._bus.publish_async(ev)
        return True

    def timeout_run(self, run_id: str) -> bool:
        """Mark a run as timed out and trigger cancellation.

        Args:
            run_id: Run ID to timeout

        Returns:
            True if timed out, False if run not found or already frozen
        """
        run = self._store.load_run(run_id)
        if run is None or run.is_frozen:
            return False

        control = self._get_control(run_id)
        if control is not None and hasattr(control, "cancel"):
            control.cancel()

        run.timed_out()
        self._store.save_run(run)
        ev = make_event(
            EventType.RUN_FAILED,
            run_id=run.run_id,
            request_id=run.request_id,
            workspace_id=run.workspace_id,
            org_id=run.org_id,
            module=run.module,
            agent=run.agent,
            error="timeout",
        )
        self._store.save_event(ev)
        self._bus.publish_async(ev)
        return True

    def get_active_run_ids(self) -> list[str]:
        """Get list of currently active run IDs.

        Returns:
            List of run IDs with registered control handles
        """
        with self._controls_lock:
            return list(self._active_controls.keys())

    def register_control(self, run_id: str, control: Any) -> None:
        """Register a control handle for a running execution.

        Args:
            run_id: Run ID
            control: Control handle (must have a cancel() method)
        """
        with self._controls_lock:
            self._active_controls[run_id] = control

    def unregister_control(self, run_id: str) -> None:
        """Unregister a control handle after execution completes.

        Args:
            run_id: Run ID
        """
        with self._controls_lock:
            self._active_controls.pop(run_id, None)

    def _get_control(self, run_id: str) -> Any | None:
        """Get control handle for a run (internal helper).

        Args:
            run_id: Run ID

        Returns:
            Control handle or None if not found
        """
        with self._controls_lock:
            return self._active_controls.get(run_id)

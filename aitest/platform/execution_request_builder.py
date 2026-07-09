"""Request normalization and building utilities.

This module handles:
- Context normalization (merging defaults with user input)
- Request creation from ExecutionContext
- Idempotency key resolution
- Finding existing requests for deduplication

Extracted from execution_service.py to improve modularity.
"""

from __future__ import annotations

import uuid
from typing import Any

from alice_engine.contracts import ExecutionContext

from .config_registry import cfg
from .execution_request import ExecutionRequest
from .run_event import EventDataKey as K
from .run_store import RunStore


class ExecutionRequestBuilder:
    """Utilities for normalizing contexts and building execution requests."""

    def __init__(self, store: RunStore):
        """Initialize request builder.

        Args:
            store: Run store for finding existing requests
        """
        self._store = store

    def normalize_context(
        self,
        ctx: ExecutionContext,
        *,
        module: str = "",
        pages: list[str] | None = None,
        agent: str = "automation-agent",
        mode: str = "full",
        provider: str | None = None,
        priority: int = 0,
        idempotency_key: str = "",
        max_retries: int = 3,
        metadata: dict[str, Any] | None = None,
    ) -> ExecutionContext:
        """Normalize any entrypoint input into the shared execution contract.

        Args:
            ctx: Base execution context
            module: Module name (overrides ctx.module if provided)
            pages: Pages list (overrides ctx.pages if provided)
            agent: Agent name (overrides ctx.agent if provided)
            mode: Execution mode (overrides ctx.mode if provided)
            provider: LLM provider (overrides ctx.provider if provided)
            priority: Execution priority
            idempotency_key: Key for deduplication
            max_retries: Maximum retry attempts
            metadata: Additional metadata to merge

        Returns:
            Normalized ExecutionContext
        """
        merged_metadata = dict(metadata or {})
        if idempotency_key:
            merged_metadata["idempotency_key"] = idempotency_key
        merged_metadata["max_retries"] = max_retries
        return ctx.with_execution(
            module=module or ctx.module,
            pages=pages if pages is not None else ctx.pages,
            agent=agent or ctx.agent,
            mode=mode or ctx.mode,
            provider=provider if provider is not None else ctx.provider,
            priority=priority,
            metadata=merged_metadata,
        )

    def create_request(self, ctx: ExecutionContext, *, agent: str) -> ExecutionRequest:
        """Create an execution request from normalized context.

        Args:
            ctx: Normalized execution context
            agent: Agent name

        Returns:
            New ExecutionRequest instance
        """
        return ExecutionRequest(
            request_id=str(uuid.uuid4()),
            workspace_id=ctx.workspace_id,
            org_id=ctx.org_id,
            triggered_by=ctx.user_id,
            trigger_type=ctx.metadata.get("trigger_type", "manual"),
            agent=agent,
            idempotency_key=self._resolve_idempotency_key(ctx, ctx.metadata.get("idempotency_key", "")),
            module=ctx.module,
            pages=ctx.pages,
            mode=ctx.mode,
            provider=ctx.provider or None,
            priority=ctx.priority,
            max_retries=self._safe_int(ctx.metadata.get("max_retries", 3), default=3),
        )

    def find_existing_request(self, ctx: ExecutionContext, idempotency_key: str) -> ExecutionRequest | None:
        """Find an existing request by idempotency key.

        Args:
            ctx: Execution context (for workspace/org scoping)
            idempotency_key: Idempotency key to search for

        Returns:
            Existing ExecutionRequest or None if not found
        """
        if not idempotency_key:
            return None
        finder = getattr(self._store, "find_request_by_idempotency_key", None)
        if callable(finder):
            return finder(
                idempotency_key,
                workspace_id=ctx.workspace_id,
                org_id=ctx.org_id,
            )
        return None

    @staticmethod
    def _safe_int(value: Any, *, default: int) -> int:
        """Safely convert value to int with fallback.

        Args:
            value: Value to convert
            default: Default value if conversion fails

        Returns:
            Converted int or default
        """
        try:
            return int(value)
        except Exception:
            return default

    @staticmethod
    def _resolve_idempotency_key(ctx: ExecutionContext, idempotency_key: str = "") -> str:
        """Resolve idempotency key from context or explicit parameter.

        Args:
            ctx: Execution context
            idempotency_key: Explicit idempotency key (takes precedence)

        Returns:
            Resolved idempotency key (empty string if none)
        """
        key = str(idempotency_key or (ctx.metadata.get("idempotency_key", "") if isinstance(ctx.metadata, dict) else "")).strip()
        return key

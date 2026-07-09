"""Server-side dependency resolution helpers.

Phase 8 composition-root governance keeps request handlers on a single
resolution path for shared platform services.
"""

from __future__ import annotations

from fastapi import Request


def get_from_app_state(request: Request, attr: str, factory):
    """Return a shared app.state dependency, falling back to the factory."""
    obj = getattr(request.app.state, attr, None)
    if obj is None:
        obj = factory()
    return obj


def get_execution_service(request: Request):
    """Resolve ExecutionService through the server composition root."""
    from aitest.platform.execution_service import ExecutionService

    return get_from_app_state(request, "execution_service", ExecutionService)

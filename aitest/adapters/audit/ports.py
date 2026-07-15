"""Ports used by audit adapters to reach optional platform services."""

from collections.abc import Callable
from typing import Any


_kpi_factory: Callable | None = None


def register_kpi_factory(factory: Callable) -> None:
    """Register the KPI collector factory from the package composition root."""
    global _kpi_factory
    _kpi_factory = factory


def record_kpi(audit_type: str, module: str, report: dict) -> Any:
    """Record an audit KPI when the platform composition has supplied a port."""
    if _kpi_factory is None:
        return None
    return _kpi_factory().record_audit(audit_type, module, report)

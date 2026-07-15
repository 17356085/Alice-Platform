"""Workflow database models — backward compatibility re-export.

Moved: 2026-07-14 to aitest.infra.models.workflow (Step 2.1 - eliminate infra → platform dependency)
This file re-exports for backward compatibility.
"""

from aitest.infra.models.workflow import WorkflowModel

__all__ = ["WorkflowModel"]

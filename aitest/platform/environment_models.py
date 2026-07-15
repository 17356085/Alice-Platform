"""Environment ORM Models — backward compatibility re-export.

Moved: 2026-07-14 to aitest.infra.models.environment (Step 2.1 - eliminate infra → platform dependency)
This file re-exports for backward compatibility.
"""

from aitest.infra.models.environment import EnvironmentModel

__all__ = ["EnvironmentModel"]
